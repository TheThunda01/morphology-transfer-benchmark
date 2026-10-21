"""Study annotated morphology relationships without identifying new drug targets."""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import warnings

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, balanced_accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]


def numeric(value):
    if value.strip() in {'','NA','NaN','nan'}:return np.nan
    number=float(value)
    if not np.isfinite(number):raise ValueError('non-finite numeric input other than declared missing values')
    return number


def load_snapshot(directory,config):
    path=Path(directory)/'profiles.csv.gz'
    raw=path.read_bytes();manifest=json.loads(path.with_suffix('.manifest.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=manifest['snapshot_sha256']:
        raise ValueError('snapshot SHA-256 mismatch')
    for file,key in [('moa.tsv','annotation_sha256'),('barcode_platemap.csv','barcode_sha256')]:
        if hashlib.sha256((Path(directory)/'upstream'/file).read_bytes()).hexdigest()!=manifest[key]:
            raise ValueError('upstream metadata SHA-256 mismatch: '+file)
    selection=manifest['selection']
    for key in ['moa_classes','dose_recode','feature_objects','shape_measurements','intensity_measurements','channels','cell_line']:
        if selection[key]!=config[key]:raise ValueError('config changes the pinned input selection: '+key)
    names=([f'{o}_AreaShape_{m}' for o in config['feature_objects'] for m in config['shape_measurements']]
           +[f'{o}_Intensity_{m}_{c}' for o in config['feature_objects'] for m in config['intensity_measurements'] for c in config['channels']])
    reader=csv.DictReader(io.StringIO(gzip.decompress(raw).decode('utf-8')),strict=True)
    rows=list(reader)
    if (len(rows)!=manifest['rows'] or not set(names).issubset(reader.fieldnames)
            or len(reader.fieldnames)!=len(set(reader.fieldnames))):raise ValueError('snapshot schema/row-count mismatch')
    keys=set()
    for row in rows:
        if None in row or any(v is None for v in row.values()):raise ValueError('malformed CSV width')
        key=(row['Metadata_Plate'],row['Metadata_Well'])
        if key in keys:raise ValueError('duplicate plate-well key')
        keys.add(key)
        if row['Metadata_cell_id']!=config['cell_line']:raise ValueError('unexpected cell line')
        control=row['Metadata_broad_sample']=='DMSO'
        if not control and row['Metadata_dose_recode']!=str(config['dose_recode']):raise ValueError('unexpected dose bin')
    matrix=np.array([[numeric(row[n]) for n in names] for row in rows])
    return rows,matrix,names,manifest


def normalize_controls(rows,x,min_controls=12,mad_scale=1.4826):
    """Plate-local negative controls are available at analysis time; no treated-well fitting."""
    out=np.empty_like(x);report=[]
    all_controls=[i for i,row in enumerate(rows) if row['Metadata_broad_sample']=='DMSO']
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        diagnostic_center=np.nanmedian(x[all_controls],axis=0)
        diagnostic_scale=mad_scale*np.nanmedian(np.abs(x[all_controls]-diagnostic_center),axis=0)
    diagnostic_scale[(~np.isfinite(diagnostic_scale))|(diagnostic_scale<=1e-12)]=np.nan
    for plate in sorted({r['Metadata_Plate'] for r in rows}):
        indices=[i for i,r in enumerate(rows) if r['Metadata_Plate']==plate]
        controls=[i for i in indices if rows[i]['Metadata_broad_sample']=='DMSO']
        if len(controls)<min_controls:raise ValueError('insufficient DMSO controls: '+plate)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            center=np.nanmedian(x[controls],axis=0)
            scale=mad_scale*np.nanmedian(np.abs(x[controls]-center),axis=0)
        invalid=~np.isfinite(center)|~np.isfinite(scale)|(scale<=1e-12)
        # A nonestimable control scale leaves that plate-feature missing. It is
        # never replaced with a treated-well scale or silently treated as zero.
        scale[invalid]=np.nan
        out[indices]=(x[indices]-center)/scale
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            control_shift=float(np.sqrt(np.nanmean(((center-diagnostic_center)/diagnostic_scale)**2)))
        report.append({'plate':plate,'plate_map':rows[indices[0]]['Metadata_Plate_Map_Name'],
                       'controls':len(controls),'unusable_control_features':int(invalid.sum()),
                       'treated_wells':len(indices)-len(controls),
                       'control_shift_rms_global_control_mad_units':control_shift if np.isfinite(control_shift) else None})
    return out,report


def aggregate_compounds(rows,x,config):
    groups=defaultdict(list)
    for i,row in enumerate(rows):
        if row['Metadata_broad_sample']=='DMSO':continue
        identity=row['Metadata_InChIKey14']
        if not identity:raise ValueError('missing related-compound identity')
        groups[identity].append(i)
    accepted=[];matrix=[];audit=[]
    for identity,indices in sorted(groups.items()):
        selected=[rows[i] for i in indices]
        labels={r['Metadata_moa'] for r in selected};plates={r['Metadata_Plate'] for r in selected}
        missing=float(np.isnan(x[indices]).mean())
        reason='eligible'
        if len(labels)!=1:reason='conflicting_moa_for_related_identity'
        elif next(iter(labels)) not in config['moa_classes']:reason='outside_prespecified_panel'
        elif len(plates)<config['minimum_replicates']:reason='too_few_distinct_replicate_plates'
        elif missing>config['maximum_missing_fraction']:reason='too_many_missing_normalized_values'
        item={'group':identity,'compound_names':'|'.join(sorted({r['Metadata_pert_iname'] for r in selected})),
              'broad_ids':'|'.join(sorted({r['Metadata_broad_id'] for r in selected})),
              'moa':'|'.join(sorted(labels)),'replicate_wells':len(indices),'distinct_plates':len(plates),
              'plate_maps':'|'.join(sorted({r['Metadata_Plate_Map_Name'] for r in selected})),
              'well_positions':'|'.join(sorted({r['Metadata_Well'] for r in selected})),
              'raw_dose_values':'|'.join(sorted({r['Metadata_mmoles_per_liter'] for r in selected})),
              'missing_fraction':missing,'status':reason}
        audit.append(item)
        if reason=='eligible':
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',RuntimeWarning)
                vector=np.nanmedian(x[indices],axis=0)
            accepted.append(item);matrix.append(vector)
    return accepted,np.array(matrix),audit


def split_compounds(groups,config):
    rng=np.random.default_rng(config['seed']);splits={key:[] for key in ['train','validation','test']}
    for label in config['moa_classes']:
        indices=np.array([i for i,row in enumerate(groups) if row['moa']==label])
        if len(indices)<config['minimum_compounds_per_class']:raise ValueError('class lacks split support')
        indices=rng.permutation(indices)
        nt=max(1,int(len(indices)*config['test_fraction']));nv=max(1,int(len(indices)*config['validation_fraction']))
        if len(indices)-nt-nv<3:raise ValueError('fewer than three training identities in a class')
        splits['test'].extend(indices[:nt]);splits['validation'].extend(indices[nt:nt+nv]);splits['train'].extend(indices[nt+nv:])
    return {key:np.array(sorted(values),dtype=int) for key,values in splits.items()}


def training_transform(x,train,max_missing=0.05):
    keep=(np.isnan(x[train]).mean(axis=0)<=max_missing)&(np.nanstd(x[train],axis=0)>1e-12)
    if not keep.any():raise ValueError('no usable training features')
    transform=make_pipeline(SimpleImputer(strategy='median'),StandardScaler())
    transform.fit(x[train][:,keep])
    return transform.transform(x[:,keep]),keep,transform


def retrieval(groups,x,queries,references):
    rows=[]
    for i in queries:
        query=groups[i];qmaps=set(query['plate_maps'].split('|'))
        refs=[j for j in references if groups[j]['group']!=query['group'] and not qmaps.intersection(groups[j]['plate_maps'].split('|'))]
        positive=[groups[j]['moa']==query['moa'] for j in refs]
        base={'group':query['group'],'compound':query['compound_names'],'moa':query['moa'],
              'reference_count':len(refs),'positive_reference_count':sum(positive),
              'status':'eligible','nearest_compound':None,'top1_correct':None,'average_precision':None,
              'random_top1_expectation':None,'random_ap_expectation':None}
        if not refs:base['status']='no_references_after_exclusions'
        elif not any(positive):base['status']='no_positive_references_after_exclusions'
        elif np.linalg.norm(x[i])<=1e-12:base['status']='zero_query_vector'
        else:
            ref=np.array(refs);norm=np.linalg.norm(x[ref],axis=1)
            if (norm<=1e-12).any():raise ValueError('zero reference vector; cannot compute cosine similarity')
            similarity=x[ref]@x[i]/(norm*np.linalg.norm(x[i]))
            ordering=sorted(range(len(refs)),key=lambda k:(-similarity[k],groups[refs[k]]['group']))
            top=refs[ordering[0]];n=len(refs);m=sum(positive);harmonic=sum(1/k for k in range(1,n+1))
            random_ap=1.0 if n==1 else harmonic/n+(m-1)*(n-harmonic)/(n*(n-1))
            base.update(nearest_compound=groups[top]['compound_names'],top1_correct=bool(groups[top]['moa']==query['moa']),
                        average_precision=float(average_precision_score(positive,similarity)),
                        random_top1_expectation=m/n,random_ap_expectation=random_ap)
        rows.append(base)
    return rows


def classification(groups,x,splits,config):
    labels=np.array([r['moa'] for r in groups]);train=splits['train'];val=splits['validation'];test=splits['test']
    models={
        'prior':[('prior',DummyClassifier(strategy='prior'))],
        'logistic':[(f'C={c}',LogisticRegression(C=c,max_iter=2000,random_state=config['seed'])) for c in config['logistic_c']],
        'random_forest':[(f'depth={depth}',RandomForestClassifier(n_estimators=config['random_forest_trees'],max_depth=depth,random_state=config['seed'],n_jobs=1)) for depth in config['random_forest_depth']]}
    tuning=[];scores=[];predictions=[]
    for name,candidates in models.items():
        best=None
        for setting,model in candidates:
            model.fit(x[train],labels[train]);pred=model.predict(x[val])
            score=float(f1_score(labels[val],pred,labels=config['moa_classes'],average='macro',zero_division=0))
            tuning.append({'model':name,'setting':setting,'validation_macro_f1':score})
            if best is None or score>best[0]:best=(score,setting,model)
        _,setting,model=best;pred=model.predict(x[test])
        scores.append({'model':name,'setting':setting,'test_compounds':len(test),
                       'accuracy':float(accuracy_score(labels[test],pred)),
                       'balanced_accuracy':float(balanced_accuracy_score(labels[test],pred)),
                       'macro_f1':float(f1_score(labels[test],pred,labels=config['moa_classes'],average='macro',zero_division=0))})
        predictions.extend({'group':groups[i]['group'],'model':name,'actual':str(labels[i]),'predicted':str(p)} for i,p in zip(test,pred))
    return scores,tuning,predictions


def annotation_audit(directory,groups,audit,config):
    observed={row['group']:row for row in audit}
    with (Path(directory)/'upstream/moa.tsv').open() as stream:
        annotations=list(csv.DictReader(stream,delimiter='\t'))
    output=[];seen=set()
    for row in annotations:
        if row['moa'] not in config['moa_classes'] or row['InChIKey14'] in seen:continue
        group=row['InChIKey14'];seen.add(group)
        item=observed.get(group)
        output.append({'group':group,'compound':row['pert_iname'],'moa':row['moa'],
                       'status':item['status'] if item else 'absent_from_selected_dose_snapshot'})
    return output


def bootstrap_mean(values,seed,repeats=2000):
    values=np.asarray(values,dtype=float)
    if len(values)==0:return [None,None]
    rng=np.random.default_rng(seed)
    means=values[rng.integers(0,len(values),size=(repeats,len(values)))].mean(axis=1)
    return [float(x) for x in np.quantile(means,[0.025,0.975])]


def display(value):
    return 'unavailable' if value is None else f'{value:.3f}'


def write_csv(path,rows):
    if not rows:raise ValueError('cannot infer empty table schema')
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def plot_report(path,support,queries,scores,excluded=()):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(15,5.8),layout='constrained')
    labels=list(support)
    axes[0].barh(labels,[support[k] for k in labels],color=['#777777' if k in excluded else '#0072b2' for k in labels])
    for i,k in enumerate(labels):
        if k in excluded:axes[0].text(support[k]+0.15,i,'not scored',va='center',fontsize=8)
    axes[0].set_xlabel('Distinct related-compound groups');axes[0].set_title('Available panel support')
    eligible=[q for q in queries if q['status']=='eligible'];positions=np.arange(len(eligible))
    axes[1].scatter(positions,[q['average_precision'] for q in eligible],label='Cosine retrieval',color='#0072b2')
    axes[1].scatter(positions,[q['random_ap_expectation'] for q in eligible],label='Random-order expectation',color='#d55e00',marker='x')
    axes[1].set_ylim(0,1.05);axes[1].set_xlabel('Eligible held-out compound');axes[1].set_ylabel('Average precision');axes[1].set_title('Train-gallery retrieval');axes[1].legend(fontsize=8)
    axes[2].bar([s['model'] for s in scores],[s['macro_f1'] for s in scores],color=['#777777','#0072b2','#009e73'])
    axes[2].set_ylim(0,1);axes[2].set_ylabel('Macro F1');axes[2].set_title('Fixed held-out compounds')
    fig.suptitle('Within-panel morphology benchmark · A549, one dose category',fontsize=14)
    fig.savefig(path,metadata={'Date':None});plt.close(fig)


def run(data_dir,output):
    config=json.loads((ROOT/'config.json').read_text());rows,raw,names,manifest=load_snapshot(data_dir,config)
    normalized,controls=normalize_controls(rows,raw,config['minimum_controls_per_plate'],config['mad_scale'])
    groups,x,audit=aggregate_compounds(rows,normalized,config)
    available=Counter(row['moa'] for row in groups)
    eligible_classes=[label for label in config['moa_classes'] if available[label]>=config['minimum_compounds_per_class']]
    if len(eligible_classes)<2:raise ValueError('fewer than two classes pass the prespecified distinct-compound support gate')
    for row in audit:
        if row['status']=='eligible' and row['moa'] not in eligible_classes:row['status']='insufficient_class_support'
    candidates=annotation_audit(data_dir,groups,audit,config)
    take=[i for i,row in enumerate(groups) if row['moa'] in eligible_classes]
    groups=[groups[i] for i in take];x=x[take]
    analysis_config={**config,'moa_classes':eligible_classes}
    splits=split_compounds(groups,analysis_config)
    transformed,keep,transform=training_transform(x,splits['train'],config['maximum_missing_fraction'])
    queries=retrieval(groups,transformed,splits['test'],splits['train'])
    scores,tuning,predictions=classification(groups,transformed,splits,analysis_config)
    support=[{'moa':label,'available_groups':available[label],'status':'included' if label in eligible_classes else 'insufficient_class_support',
              **{split:sum(groups[i]['moa']==label for i in indices) for split,indices in splits.items()}} for label in config['moa_classes']]
    class_results=[]
    for score in scores:
        model_predictions=[p for p in predictions if p['model']==score['model']]
        correct=[int(p['actual']==p['predicted']) for p in model_predictions]
        low,high=bootstrap_mean(correct,config['seed'])
        score.update(accuracy_bootstrap95_low=low,accuracy_bootstrap95_high=high)
        class_results.extend({'model':score['model'],'moa':label,'test_groups':sum(p['actual']==label for p in model_predictions),
                              'correct':sum(p['actual']==label and p['predicted']==label for p in model_predictions)} for label in eligible_classes)
    eligible=[q for q in queries if q['status']=='eligible']
    metadata_distribution=[]
    for split,indices in splits.items():
        maps=Counter(m for i in indices for m in groups[i]['plate_maps'].split('|'))
        metadata_distribution.extend({'split':split,'plate_map':m,'compound_groups':n} for m,n in sorted(maps.items()))
    split_maps={split:{m for i in indices for m in groups[i]['plate_maps'].split('|')} for split,indices in splits.items()}
    metrics={'scope':'Within a prespecified mechanism panel after documented support exclusions; no target or efficacy inference',
             'source_sha256':manifest['snapshot_sha256'],'config_sha256':hashlib.sha256((ROOT/'config.json').read_bytes()).hexdigest(),
             'source_rows':len(rows),'compound_groups':len(groups),'input_features':len(names),'training_features':int(keep.sum()),
             'split_counts':{k:len(v) for k,v in splits.items()},'support':support,
             'requested_moa_classes':config['moa_classes'],'included_moa_classes':eligible_classes,
             'accuracy_change_per_one_test_group':1/len(splits['test']),
             'shared_train_test_plate_maps':sorted(split_maps['train']&split_maps['test']),
             'control_diagnostic_note':'Global control median/MAD is used only to describe plate shifts; predictive transformations use plate-local DMSO controls then training groups.',
             'retrieval':{'queries':len(queries),'eligible_queries':len(eligible),'ineligible_queries':len(queries)-len(eligible),
                          'mean_average_precision':float(np.mean([q['average_precision'] for q in eligible])) if eligible else None,
                          'random_mean_average_precision':float(np.mean([q['random_ap_expectation'] for q in eligible])) if eligible else None,
                          'top1_accuracy':float(np.mean([q['top1_correct'] for q in eligible])) if eligible else None},
             'classification':scores,'neural_model':'Not fitted: only a small number of distinct compound groups per class',
             'normalization':'DMSO-only plate median/MAD; all subsequent feature selection, imputation and scaling fitted on training compound groups',
             'upstream_dose_field':'Metadata_mmoles_per_liter; name conflicts with micromolar doses in source publication, so values are retained as source values without silent unit conversion'}
    metrics['selected_dose_values']=sorted({r['Metadata_mmoles_per_liter'] for r in rows if r['Metadata_broad_sample']!='DMSO'})
    metrics['retrieval']['mean_ap_bootstrap95']=bootstrap_mean([q['average_precision'] for q in eligible],config['seed'])
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    split_rows=[{'group':groups[i]['group'],'moa':groups[i]['moa'],'split':key} for key,indices in splits.items() for i in indices]
    features=[{'feature':n,'retained_from_training':bool(flag)} for n,flag in zip(names,keep)]
    for filename,table in [('compound_audit.csv',audit),('annotation_audit.csv',candidates),('control_audit.csv',controls),('split_manifest.csv',split_rows),
                           ('class_support.csv',support),('retrieval_queries.csv',queries),('model_comparison.csv',scores),
                           ('validation_candidates.csv',tuning),('test_predictions.csv',predictions),('class_predictions.csv',class_results),
                           ('metadata_distribution.csv',metadata_distribution),('features.csv',features)]:write_csv(output/filename,table)
    (output/'metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n')
    plot_report(output/'benchmark.svg',{r['moa']:r['available_groups'] for r in support},queries,scores,
                [r['moa'] for r in support if r['status']!='included'])
    text=['# Morphology transfer benchmark','',f"{len(groups)} related-compound groups; {len(rows)} retained raw wells; {int(keep.sum())}/{len(names)} training-usable features.",'',
          f"The fixed split contains {len(splits['train'])} training, {len(splits['validation'])} validation, and {len(splits['test'])} test groups. All related identities and replicate wells stay together.",'',
          f"Requested {len(config['moa_classes'])} mechanism classes; {len(eligible_classes)} pass the prespecified minimum of {config['minimum_compounds_per_class']} distinct compound groups. Inspect class_support.csv and annotation_audit.csv for all exclusions.",'',
          f"Retrieval: {len(eligible)}/{len(queries)} test queries have a same-MOA training reference after both identity and plate-map exclusions. Mean AP is {display(metrics['retrieval']['mean_average_precision'])}; random-order expected AP is {display(metrics['retrieval']['random_mean_average_precision'])}. These are within-panel results.",'',
          '| Model | Selected setting | Test accuracy | Test macro F1 |','| --- | --- | ---: | ---: |']
    text += [f"| {s['model']} | {s['setting']} | {s['accuracy']:.3f} | {s['macro_f1']:.3f} |" for s in scores]
    text += ['', '![Support, retrieval, and model comparison](benchmark.svg)','',
             'Models use one fixed compound split and settings selected on validation macro F1. No neural model was fitted because class support is small. The test set is small; these estimates do not establish model superiority or broad mechanism recognition.', '',
             f"One changed test-group prediction moves overall accuracy by {100/len(splits['test']):.2f} percentage points. model_comparison.csv contains descriptive bootstrap intervals for accuracy; retrieval mean-AP intervals are in metrics.json. These resample fixed held-out compound results, assume exchangeability, and do not include uncertainty from data collection, model fitting, split choice, annotation error, or related chemistry. class_predictions.csv gives every class denominator.",'',
             'Each query has an explicit eligibility record. The reference gallery contains training groups only; same identity and any shared plate map are excluded. Classifier inputs retain plate/position confounding risk despite compound separation. DMSO normalization uses negative controls on the same plates, an explicitly assumed available-at-analysis resource.', '',
             'Morphology is an indirect, context-dependent phenotype. Annotated MOA can be incomplete or wrong; matches do not identify direct targets, mechanisms, drug efficacy, or clinical safety. The source dose field name and publication units disagree; the analysis uses the fixed upstream dose category and preserves original values.','']
    (output/'report.md').write_text('\n'.join(text));return metrics


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data');parser.add_argument('--output',type=Path,default=ROOT/'results')
    args=parser.parse_args()
    try:print(json.dumps(run(args.data_dir,args.output),indent=2,allow_nan=False))
    except (ValueError,OSError,KeyError,csv.Error) as error:parser.exit(2,f'benchmark failed: {error}\n')

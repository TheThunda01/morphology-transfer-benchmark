"""Rebuild the compact snapshot from public, content-addressed Level-3 profiles."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='https://cellpainting-gallery.s3.amazonaws.com/cpg0004-lincs/broad/workspace/software/lincs-cell-painting_DVC/'
DIRECTORY_MD5='856a0e07b38c2cdeae7822b80d8f8ee9'
META=['Metadata_Plate','Metadata_Well','Metadata_Plate_Map_Name','Metadata_Batch_Number','Metadata_Batch_Date',
      'Metadata_cell_id','Metadata_broad_sample','Metadata_broad_id','Metadata_pert_iname','Metadata_InChIKey14',
      'Metadata_moa','Metadata_target','Metadata_broad_sample_type','Metadata_pert_type',
      'Metadata_mmoles_per_liter','Metadata_dose_recode']


def content(md5,cache,suffix=''):
    path=cache/(md5+suffix)
    if path.exists():
        raw=path.read_bytes()
    else:
        with urllib.request.urlopen(BASE+md5[:2]+'/'+md5[2:]+suffix,timeout=45) as response:
            raw=response.read(12_000_001)
        if len(raw)>12_000_000:raise ValueError('unexpectedly large source object')
        path.write_bytes(raw)
    if hashlib.md5(raw).hexdigest()!=md5:raise ValueError('source content digest mismatch: '+md5)
    return raw


def feature_names(config):
    return ([f'{obj}_AreaShape_{measure}' for obj in config['feature_objects'] for measure in config['shape_measurements']]
            +[f'{obj}_Intensity_{measure}_{channel}' for obj in config['feature_objects']
              for measure in config['intensity_measurements'] for channel in config['channels']])


def process(entry,config,cache):
    raw=content(entry['md5'],cache)
    reader=csv.DictReader(io.StringIO(gzip.decompress(raw).decode('utf-8')),strict=True)
    names=feature_names(config)
    if not set(META+names).issubset(reader.fieldnames or []):raise ValueError('required profile fields missing')
    kept=[];counts=Counter()
    for row in reader:
        counts['upstream_rows']+=1
        if row['Metadata_cell_id']!=config['cell_line']:
            counts['other_cell_line']+=1;continue
        if row['Metadata_broad_sample']=='DMSO':
            counts['controls_retained']+=1
        elif row['Metadata_pert_type']=='trt' and row['Metadata_dose_recode']==str(config['dose_recode']):
            counts['treatment_rows_at_selected_dose']+=1
            moa=row['Metadata_moa']
            if not moa:counts['missing_moa_at_dose']+=1;continue
            if '|' in moa:counts['multiple_moa_at_dose']+=1;continue
            if moa not in config['moa_classes']:counts['outside_panel_at_dose']+=1;continue
            if not row['Metadata_InChIKey14'] or not row['Metadata_broad_id']:
                counts['missing_compound_identity']+=1;continue
            counts['panel_treatments_retained']+=1
        else:
            counts['other_dose_or_role']+=1;continue
        kept.append({k:row[k] for k in META+names})
    provenance={'upstream_path':entry['relpath'],'md5':entry['md5'],'sha256':hashlib.sha256(raw).hexdigest(),
                'bytes':len(raw),'url':BASE+entry['md5'][:2]+'/'+entry['md5'][2:]}
    return kept,counts,provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'data/profiles.csv.gz')
    parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args()
    if args.output.exists():parser.error('output exists; use a new path to preserve the snapshot')
    if not 1<=args.workers<=12:parser.error('workers must be between 1 and 12')
    config=json.loads((ROOT/'config.json').read_text())
    cache=ROOT/'.cache';cache.mkdir(exist_ok=True)
    directory=content(DIRECTORY_MD5,cache,'.dir')
    entries=[r for r in json.loads(directory) if r['relpath'].endswith('_augmented.csv.gz')]
    if len(entries)!=136:raise ValueError('unexpected number of Level-3 plates')
    rows=[];counts=Counter();sources=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(process,e,config,cache) for e in entries]
        for index,future in enumerate(as_completed(futures),1):
            kept,observed,source=future.result();rows.extend(kept);counts.update(observed);sources.append(source)
            if index%20==0:print(f'Checked {index}/{len(entries)} raw profile objects',flush=True)
    rows.sort(key=lambda r:(r['Metadata_Plate'],r['Metadata_Well']))
    if len({(r['Metadata_Plate'],r['Metadata_Well']) for r in rows})!=len(rows):raise ValueError('duplicate source well')
    text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=META+feature_names(config),lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    raw=gzip.compress(text.getvalue().encode(),mtime=0)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(raw)
    manifest={'source':'Broad LINCS Cell Painting Pilot1; Level3 annotated well medians',
              'source_commit':config['dataset_ref'],'source_license':'CC0-1.0',
              'captured_utc':datetime.now(timezone.utc).isoformat(),
              'source_directory_md5':DIRECTORY_MD5,'snapshot_sha256':hashlib.sha256(raw).hexdigest(),
              'snapshot_bytes':len(raw),'rows':len(rows),'numeric_features':len(feature_names(config)),
              'annotation_sha256':hashlib.sha256((ROOT/'data/upstream/moa.tsv').read_bytes()).hexdigest(),
              'barcode_sha256':hashlib.sha256((ROOT/'data/upstream/barcode_platemap.csv').read_bytes()).hexdigest(),
              'selection':config,'filter_counts':dict(counts),'source_objects':sorted(sources,key=lambda r:r['upstream_path'])}
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'data/upstream/dvc_manifest.json').write_bytes(directory)
    print(json.dumps({'rows':len(rows),'bytes':len(raw),'filter_counts':dict(counts)},indent=2))


if __name__=='__main__':main()

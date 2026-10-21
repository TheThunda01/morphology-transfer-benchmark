"""Small synthetic checks of data roles, eligibility, and scoring arithmetic."""
from itertools import combinations
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import warnings

import numpy as np

from morphology.analysis import (
    aggregate_compounds, bootstrap_mean, display, load_snapshot, normalize_controls, numeric,
    retrieval, split_compounds, training_transform,
)

ROOT=Path(__file__).resolve().parents[1]


def compound(group, moa='A', maps='map-1'):
    return {'group': group, 'moa': moa, 'plate_maps': maps, 'compound_names': group}


def well(group, plate, moa='A', sample=None, position='B02'):
    return {'Metadata_broad_sample': sample or group,
            'Metadata_InChIKey14': group, 'Metadata_moa': moa,
            'Metadata_Plate': plate, 'Metadata_pert_iname': group,
            'Metadata_broad_id': 'BRD-'+group,
            'Metadata_Plate_Map_Name': 'map-'+plate, 'Metadata_Well': position,
            'Metadata_mmoles_per_liter': '10'}


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.config = {'seed': 123, 'moa_classes': ['A', 'B'],
                       'minimum_compounds_per_class': 6,
                       'test_fraction': 0.2, 'validation_fraction': 0.2}
        self.groups = [compound(f'{label}{i}', label) for label in ['A', 'B'] for i in range(6)]

    def test_deterministic_split_is_disjoint_complete_and_keeps_class_support(self):
        result=split_compounds(self.groups,self.config)
        again=split_compounds(self.groups,self.config)
        sets={key:set(indices) for key,indices in result.items()}
        self.assertFalse(sets['train'] & sets['test'])
        self.assertFalse(sets['validation'] & sets['test'])
        self.assertFalse(sets['train'] & sets['validation'])
        self.assertEqual(set.union(*sets.values()),set(range(len(self.groups))))
        for split,indices in result.items():
            np.testing.assert_array_equal(indices,again[split])
            self.assertEqual({self.groups[i]['moa'] for i in indices},{'A','B'})
        self.assertEqual([len(result[k]) for k in ['train','validation','test']],[8,2,2])

    def test_under_supported_class_cannot_silently_enter_split(self):
        with self.assertRaisesRegex(ValueError,'class lacks split support'):
            split_compounds(self.groups[:-1],self.config)
        with self.assertRaisesRegex(ValueError,'fewer than three training'):
            split_compounds(self.groups,{**self.config,'test_fraction':0.5,'validation_fraction':0.25})


class AggregationTests(unittest.TestCase):
    def setUp(self):
        self.config={'moa_classes':['A','B'],'minimum_replicates':3,'maximum_missing_fraction':0.2}

    def test_related_ids_aggregate_once_and_controls_do_not_enter_compounds(self):
        rows=[well('shared',f'p{i}',sample=f'lot{i}') for i in range(3)]
        rows.append(well('', 'p0',sample='DMSO'))
        x=np.array([[1.,2.],[3.,4.],[5.,6.],[1000.,1000.]])
        groups,matrix,audit=aggregate_compounds(rows,x,self.config)
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]['group'],'shared')
        self.assertEqual(groups[0]['replicate_wells'],3)
        self.assertEqual(groups[0]['distinct_plates'],3)
        np.testing.assert_array_equal(matrix,[[3.,4.]])
        self.assertEqual(audit[0]['status'],'eligible')

    def test_conflict_replicate_and_missingness_exclusions_are_visible(self):
        cases=[([well('g','p0','A'),well('g','p1','B'),well('g','p2','A')],
                np.ones((3,2)),'conflicting_moa_for_related_identity'),
               ([well('g','p0'),well('g','p0'),well('g','p0')],
                np.ones((3,2)),'too_few_distinct_replicate_plates'),
               ([well('g',f'p{i}') for i in range(3)],
                np.array([[np.nan,np.nan],[1.,2.],[3.,4.]]),'too_many_missing_normalized_values')]
        for rows,matrix,reason in cases:
            with self.subTest(reason=reason):
                groups,values,audit=aggregate_compounds(rows,matrix,self.config)
                self.assertEqual(groups,[])
                self.assertEqual(values.size,0)
                self.assertEqual(audit[0]['status'],reason)

    def test_missing_related_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'missing related-compound identity'):
            aggregate_compounds([well('','p')],np.array([[1.,2.]]),self.config)


class TransformationTests(unittest.TestCase):
    def test_control_normalization_never_fits_treated_rows(self):
        rows=[well('','p',sample='DMSO'),well('','p',sample='DMSO'),well('treated','p')]
        x=np.array([[1.,10.],[3.,10.],[5.,100.]])
        normalized,audit=normalize_controls(rows,x,min_controls=2,mad_scale=1.0)
        np.testing.assert_array_equal(normalized[:,0],[-1.,1.,3.])
        self.assertTrue(np.isnan(normalized[:,1]).all())
        self.assertEqual(audit[0]['unusable_control_features'],1)
        self.assertEqual(audit[0]['controls'],2)
        altered=x.copy();altered[2]=[500.,1e9]
        other,_=normalize_controls(rows,altered,min_controls=2,mad_scale=1.0)
        np.testing.assert_array_equal(normalized[:2],other[:2])
        self.assertEqual(other[2,0],498.)

    def test_missing_control_scale_is_not_replaced_from_treated_rows(self):
        rows=[well('','p',sample='DMSO'),well('','p',sample='DMSO'),well('treated','p')]
        x=np.array([[np.nan,1.],[np.nan,3.],[999.,9.]])
        normalized,audit=normalize_controls(rows,x,min_controls=2,mad_scale=1.0)
        self.assertTrue(np.isnan(normalized[:,0]).all())
        self.assertEqual(audit[0]['unusable_control_features'],1)

    def test_insufficient_controls_checked_for_each_plate(self):
        rows=[well('','p1',sample='DMSO'),well('','p1',sample='DMSO'),
              well('','p2',sample='DMSO'),well('treated','p2')]
        with self.assertRaisesRegex(ValueError,'insufficient DMSO controls: p2'):
            normalize_controls(rows,np.array([[1.],[3.],[1.],[4.]]),min_controls=2)

    def test_feature_filter_imputer_and_scaler_fit_training_only(self):
        x=np.array([[1.,np.nan,5.,np.nan],[3.,2.,5.,np.nan],
                    [5.,4.,5.,np.nan],[7.,6.,5.,np.nan],
                    [1e12,1e12,-99.,42.],[np.nan,np.nan,100.,0.]])
        train=np.arange(4)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            transformed,keep,pipeline=training_transform(x,train,max_missing=0.25)
        np.testing.assert_array_equal(keep,[True,True,False,False])
        np.testing.assert_array_equal(pipeline.named_steps['simpleimputer'].statistics_,[4.,4.])
        np.testing.assert_array_equal(pipeline.named_steps['standardscaler'].mean_,[4.,4.])
        self.assertTrue(np.isfinite(transformed).all())
        altered=x.copy();altered[4:]=[[-1e15,np.nan,999.,1000.],[1e15,3e15,888.,2000.]]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            other,other_keep,other_pipeline=training_transform(altered,train,max_missing=0.25)
        np.testing.assert_array_equal(keep,other_keep)
        np.testing.assert_allclose(transformed[train],other[train])
        np.testing.assert_array_equal(pipeline.named_steps['standardscaler'].scale_,
                                      other_pipeline.named_steps['standardscaler'].scale_)

    def test_no_usable_training_features_fails(self):
        with self.assertRaisesRegex(ValueError,'no usable training features'):
            training_transform(np.ones((4,2)),np.arange(3))


class RetrievalTests(unittest.TestCase):
    def test_same_identity_and_any_shared_plate_map_are_excluded(self):
        groups=[compound('query','A','m1|m2'),compound('query','A','m3'),
                compound('same-map','A','m2|m5'),compound('positive','A','m3'),
                compound('negative','B','m4')]
        x=np.array([[1.,0.],[1.,0.],[1.,0.],[1.,0.],[0.,1.]])
        result=retrieval(groups,x,[0],[1,2,3,4])[0]
        self.assertEqual(result['reference_count'],2)
        self.assertEqual(result['positive_reference_count'],1)
        self.assertEqual(result['nearest_compound'],'positive')
        self.assertTrue(result['top1_correct'])
        self.assertEqual(result['average_precision'],1.)
        self.assertEqual(result['random_top1_expectation'],0.5)
        self.assertEqual(result['random_ap_expectation'],0.75)

    def test_average_precision_and_random_expectation_match_enumerated_rankings(self):
        groups=[compound('query','A','query-map')]+[compound(f'r{i}','A' if i in [0,2] else 'B',f'm{i}') for i in range(4)]
        # Descending distinct cosine scores produce relevant ranks 1 and 3.
        x=np.array([[1.,0.],[1.,0.],[0.9,0.2],[0.7,0.7],[0.,1.]])
        result=retrieval(groups,x,[0],[1,2,3,4])[0]
        self.assertAlmostEqual(result['average_precision'],(1+2/3)/2)
        random_ap=[]
        for ranks in combinations(range(1,5),2):
            random_ap.append(sum(k/rank for k,rank in enumerate(ranks,1))/2)
        self.assertAlmostEqual(result['random_ap_expectation'],float(np.mean(random_ap)))
        self.assertEqual(result['random_top1_expectation'],0.5)

    def test_single_and_all_positive_gallery_boundaries(self):
        groups=[compound('query','A','mq'),compound('p1','A','m1'),compound('p2','A','m2')]
        x=np.array([[1.,0.],[1.,1.],[0.,1.]])
        for references in [[1],[1,2]]:
            result=retrieval(groups,x,[0],references)[0]
            self.assertEqual(result['average_precision'],1.)
            self.assertEqual(result['random_ap_expectation'],1.)
            self.assertEqual(result['random_top1_expectation'],1.)

    def test_no_references_no_positives_and_zero_query_have_explicit_status(self):
        groups=[compound('query','A','m1'),compound('same-map','A','m1'),
                compound('negative','B','m2'),compound('positive','A','m3')]
        x=np.array([[1.,0.],[1.,0.],[0.,1.],[1.,0.]])
        for references,status in [([1],'no_references_after_exclusions'),
                                  ([2],'no_positive_references_after_exclusions')]:
            result=retrieval(groups,x,[0],references)[0]
            self.assertEqual(result['status'],status)
            self.assertEqual(result['positive_reference_count'],0)
            self.assertIsNone(result['average_precision'])
            self.assertIsNone(result['top1_correct'])
        x[0]=0
        self.assertEqual(retrieval(groups,x,[0],[3])[0]['status'],'zero_query_vector')

    def test_zero_reference_vector_cannot_be_used_as_cosine_match(self):
        groups=[compound('query','A','m1'),compound('positive','A','m2')]
        with self.assertRaisesRegex(ValueError,'zero reference vector'):
            retrieval(groups,np.array([[1.,0.],[0.,0.]]),[0],[1])

    def test_empty_eligible_results_remain_unavailable(self):
        groups=[compound('query','A','m1'),compound('negative','B','m2')]
        x=np.array([[1.,0.],[0.,1.]])
        self.assertEqual(retrieval(groups,x,[],[1]),[])
        queries=retrieval(groups,x,[0],[1])
        eligible=[q['average_precision'] for q in queries if q['status']=='eligible']
        self.assertEqual(eligible,[])
        self.assertEqual(bootstrap_mean(eligible,123),[None,None])
        self.assertEqual(display(None),'unavailable')
        self.assertEqual(display(0.),'0.000')


class NumericTests(unittest.TestCase):
    def test_missing_tokens_and_finite_values(self):
        for token in ['', ' ', 'NA', 'NaN', 'nan']:
            with self.subTest(token=token):self.assertTrue(np.isnan(numeric(token)))
        self.assertEqual(numeric(' 1.25 '),1.25)
        self.assertEqual(numeric('-2'),-2.)
        self.assertEqual(numeric('0'),0.)

    def test_invalid_or_infinite_values_rejected(self):
        for token in ['inf','-inf','Infinity','1e999','missing','NULL']:
            with self.subTest(token=token),self.assertRaises(ValueError):numeric(token)


class SnapshotContractTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'config.json').read_text())

    def test_pinned_snapshot_shape_and_control_treatment_counts(self):
        rows,matrix,names,manifest=load_snapshot(ROOT/'data',self.config)
        self.assertEqual(len(rows),3674)
        self.assertEqual(matrix.shape,(3674,72))
        self.assertEqual(len(names),72)
        self.assertEqual(len(set(names)),72)
        self.assertEqual(len({(r['Metadata_Plate'],r['Metadata_Well']) for r in rows}),3674)
        controls=sum(r['Metadata_broad_sample']=='DMSO' for r in rows)
        self.assertEqual(controls,3264)
        self.assertEqual(len(rows)-controls,410)
        self.assertEqual(manifest['numeric_features'],len(names))

    def test_edited_gzip_rejected_before_decompression(self):
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)/'data'
            shutil.copytree(ROOT/'data',destination)
            path=destination/'profiles.csv.gz'
            path.write_bytes(path.read_bytes()+b'edited')
            with patch('morphology.analysis.gzip.decompress') as decompress:
                with self.assertRaisesRegex(ValueError,'snapshot SHA-256 mismatch'):
                    load_snapshot(destination,self.config)
                decompress.assert_not_called()

    def test_edited_annotation_or_barcode_rejected_before_profile_parse(self):
        for name in ['moa.tsv','barcode_platemap.csv']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as directory:
                destination=Path(directory)/'data'
                shutil.copytree(ROOT/'data',destination)
                path=destination/'upstream'/name
                path.write_bytes(path.read_bytes()+b'\n')
                with patch('morphology.analysis.gzip.decompress') as decompress:
                    with self.assertRaisesRegex(ValueError,'upstream metadata SHA-256 mismatch: '+name):
                        load_snapshot(destination,self.config)
                    decompress.assert_not_called()


if __name__=='__main__':
    unittest.main()

"""Compare numerical results, without requiring cross-platform SVG byte equality."""
import csv
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def comparable_metadata(value):
    """Normalize one documented wording correction in the frozen reference."""
    if isinstance(value,dict) and value.get('neural_model') == 'Not fitted: only a small number of independent compounds per class':
        value=dict(value)
        value['neural_model']='Not fitted: only a small number of distinct compound groups per class'
    return value


def equivalent(a,b):
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a,(float,int)) and not isinstance(a,bool) and isinstance(b,(float,int)) and not isinstance(b,bool):
        return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-10)
    return a==b


def scalar(value):
    try:return float(value)
    except ValueError:return value


def check(actual):
    expected=ROOT/'results'
    for source in expected.glob('*.json'):
        left=json.loads(source.read_text());right=json.loads((actual/source.name).read_text())
        if source.name=='metrics.json':
            left,right=comparable_metadata(left),comparable_metadata(right)
        if not equivalent(left,right):
            raise ValueError('JSON differs: '+source.name)
    tables=list(expected.glob('*.csv'))
    for source in tables:
        def read(path):
            with path.open() as stream:return [{k:scalar(v) for k,v in row.items()} for row in csv.DictReader(stream)]
        if not equivalent(read(source),read(actual/source.name)):raise ValueError('CSV differs: '+source.name)
    print(f'Reproduced metrics JSON and {len(tables)} CSV tables within tolerance.')


if __name__=='__main__':check(Path(sys.argv[1]))

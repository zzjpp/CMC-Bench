"""Shared paths, taxonomy and UTF-8 serializers for CMC-Bench."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='1.0.0'
SPLITS=('dev','validation','test')
TAXONOMY=json.loads((ROOT/'taxonomy.json').read_text(encoding='utf-8'))
ABILITIES=TAXONOMY['abilities']
LEVELS={int(k):v for k,v in TAXONOMY['difficulty_levels'].items()}
DESCRIPTORS={int(k):v for k,v in TAXONOMY['difficulty_descriptors'].items()}


def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def dump(path,value):
    target=ROOT/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def jsonl(path,rows):
    target=ROOT/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8',newline='\n')

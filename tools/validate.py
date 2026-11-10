"""Validate schema constraints, provenance, answer isolation and grouped splits.

The small recursive validator implements the JSON Schema keywords used in the
bundled schema. Optional full Draft 2020-12 validation can also use jsonschema.
"""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from evaluate import read_jsonl

ROOT=Path(__file__).resolve().parents[1]


def check(value, rule, schema, path='$'):
    if '$ref' in rule:
        target=schema
        for part in rule['$ref'].split('/')[1:]:
            target=target[part]
        check(value,target,schema,path)
        return
    if 'const' in rule:
        assert value==rule['const'],f'{path}: const mismatch'
    if 'enum' in rule:
        assert value in rule['enum'],f'{path}: invalid enum {value!r}'
    typ=rule.get('type')
    types={'string':str,'integer':int,'object':dict,'array':list,'null':type(None)}
    if typ:
        assert type(value) is types[typ],f'{path}: expected {typ}'
    if isinstance(value,str):
        assert len(value)>=rule.get('minLength',0),f'{path}: too short'
        if 'pattern' in rule:
            assert re.search(rule['pattern'],value),f'{path}: pattern mismatch'
        if rule.get('format')=='uri':
            assert value.startswith('https://'),f'{path}: expected HTTPS source'
    if type(value) is int:
        assert value>=rule.get('minimum',float('-inf')) and value<=rule.get('maximum',float('inf')),f'{path}: out of range'
    if isinstance(value,list):
        assert rule.get('minItems',0)<=len(value)<=rule.get('maxItems',float('inf')),f'{path}: bad item count'
        if rule.get('uniqueItems'):
            assert len({json.dumps(x,sort_keys=True) for x in value})==len(value),f'{path}: duplicates'
        for i,x in enumerate(value):
            check(x,rule.get('items',{}),schema,f'{path}[{i}]')
    if isinstance(value,dict):
        assert set(rule.get('required',[]))<=set(value),f'{path}: missing keys'
        props=rule.get('properties',{})
        extra=set(value)-set(props)
        if rule.get('additionalProperties') is False:
            assert not extra,f'{path}: unknown keys {extra}'
        for k,v in value.items():
            child=props.get(k,rule.get('additionalProperties',{}))
            if isinstance(child,dict):
                check(v,child,schema,f'{path}.{k}')


def main():
    schema=json.loads((ROOT/'schema/item.schema.json').read_text(encoding='utf-8'))
    items=read_jsonl(ROOT/'data/items.jsonl')
    assert len(items)==333, 'CMC-Bench requires exactly 333 canonical problems'
    ids=[q['id'] for q in items]
    assert len(set(ids))==len(ids),'duplicate IDs'
    sources={s['source_id']:s for s in json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))}
    for s in sources.values():
        b=(ROOT/s['path']).read_bytes()
        assert b.startswith(b'%PDF'),s['path']
        assert hashlib.sha256(b).hexdigest()==s['sha256'],s['path']
    families=defaultdict(set); papers=defaultdict(set); hashes=defaultdict(list)
    aliases=[]
    for q in items:
        check(q,schema,schema,q['id'])
        assert q['reference_solution_format']=='inline_full_solution'
        assert not any(t in q['reference_solution'] for t in ['解法提要：','PDF为评分侧金标准','完整逐步解答：sources/']), 'Reference must contain the derivation, not a pointer'
        assert sum(c['points'] for c in q['scoring_rubric'])==4
        assert len({c['id'] for c in q['scoring_rubric']})==len(q['scoring_rubric'])
        assert set(q['ability_tags'])=={c['ability'] for c in q['scoring_rubric']}
        assert set(q['ability_evidence'])==set(q['ability_tags'])
        assert hashlib.sha256(q['question_latex'].encode()).hexdigest()==q['statement_sha256']
        assert q['question_latex'].count('$')%2==0
        assert not any('_' in text or '^' in text for text in q['question_latex'].split('$')[::2]),'Unescaped math outside delimiters'
        assert q['difficulty_annotation']['empirical_sample_size']==0
        families[q['family_id']].add(q['split'])
        hashes[re.sub(r'\s+','',q['question_latex'])].append(q['id'])
        for occ in q['source_occurrences']:
            src=sources[occ['source_id']]
            assert 1<=occ['page_one_based']<=src['page_count']
            papers[occ['source_id']].add(q['split'])
        assert q['source']['sha256']==sources[q['source']['source_id']]['sha256']
        gold=q.get('solution_source')
        if gold:
            src=sources[gold['source_id']]
            assert gold['sha256']==src['sha256'] and gold['path']==src['path']
            assert all(1<=p<=src['page_count'] for p in gold['pages_one_based'])
            assert src['kind']=='solutions'
            assert (src['edition'],src['stage'],src['track'])==(q['source']['edition'],q['source']['stage'],q['source']['track'])
        assert len(q['question'])>=15,'incomplete statement'
        aliases.extend(q['aliases'])
        for asset in q['assets']:
            assert (ROOT/asset['path']).is_file() and not asset['contains_solution']
    assert len(aliases)==len(set(aliases)) and not set(aliases)&set(ids)
    assert all(len(v)==1 for v in families.values()),'family split leakage'
    assert all(len(v)==1 for v in papers.values()),'paper split leakage'
    assert all(len(v)==1 for v in hashes.values()),'exact duplicate statements'
    for split in ['dev','validation','test']:
        chosen=[q for q in items if q['split']==split]
        assert set(json.loads((ROOT/f'splits/{split}.json').read_text()))=={q['id'] for q in chosen}
        inputs=read_jsonl(ROOT/f'data/inputs/{split}.jsonl')
        assert {q['id'] for q in inputs}=={q['id'] for q in chosen}
        assert all(set(q)=={'id','question','question_latex','assets'} for q in inputs)
        canonical={q['id']:q for q in chosen}
        assert all(all(row[k]==canonical[row['id']][k] for k in row) for row in inputs), 'Solver input differs from canonical statement'
        assert {q['difficulty'] for q in chosen}==set(range(1,9))
    lock=ROOT/'checksums.json'
    if lock.exists():
        for path,digest in json.loads(lock.read_text()).items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,f'Frozen file changed: {path}'
    print(f'PASS: {len(items)} schemas; source/gold hashes and pages; unique IDs/aliases; grouped splits; 8 levels per split; answer isolation; release hashes.')


if __name__=='__main__':
    main()

"""Aggregate adjudicated scores; never claim that text equality verifies a proof."""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

from common import ROOT, read_jsonl


def validate_grades(items, grades):
    expected = {q['id']:q for q in items}
    got = {}
    for g in grades:
        key = g['id']
        if key in got:
            raise ValueError(f'Duplicate grade: {key}')
        if key not in expected:
            raise ValueError(f'Unexpected item: {key}')
        if g.get('status') != 'adjudicated' or g.get('review_type') != 'human':
            raise ValueError(f'{key}: requires adjudicated human review; LLM proposals are not final scores')
        reviewers = g.get('reviewer_ids',[])
        if len(set(reviewers))<2 or any(not isinstance(x,str) or not x.strip() for x in reviewers):
            raise ValueError(f'{key}: at least two named human reviewers are required')
        if not g.get('rationale','').strip():
            raise ValueError(f'{key}: missing review rationale')
        digest = g.get('response_sha256','')
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError(f'{key}: missing response SHA256')
        rubric = {c['id']:c['points'] for c in expected[key]['scoring_rubric']}
        earned = g.get('criteria',{})
        if set(earned)!=set(rubric):
            raise ValueError(f'{key}: criterion keys must exactly match rubric')
        for k,v in earned.items():
            if type(v) is not int or not 0<=v<=rubric[k]:
                raise ValueError(f'{key}: invalid score for {k}')
        score = sum(earned.values())
        if type(g.get('fully_correct')) is not bool or type(g.get('critical_error')) is not bool:
            raise ValueError(f'{key}: explicit boolean correctness/error flags required')
        if g['fully_correct'] != (score==4 and not g['critical_error']):
            raise ValueError(f'{key}: correctness flag conflicts with score or critical error')
        if g['critical_error'] and score>2:
            raise ValueError(f'{key}: load-bearing mathematical error caps score at 2/4')
        got[key] = dict(g,score=score)
    if set(got)!=set(expected):
        raise ValueError('Incomplete evaluation; missing IDs: '+', '.join(sorted(set(expected)-set(got))))
    return got


def wilson(k,n):
    if not n:
        return None
    z=1.95996398454
    p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,mid-half),min(1,mid+half)]


def summarize(items, grades):
    got=validate_grades(items,grades)
    n=len(items)
    if not n:
        raise ValueError('Empty evaluation split')
    fully=sum(g['fully_correct'] for g in got.values())
    levels={}
    for level in range(1,9):
        subset=[q for q in items if q['difficulty']==level]
        levels[f'L{level}']=dict(n=len(subset),
            strict_accuracy=(sum(got[q['id']]['fully_correct'] for q in subset)/len(subset) if subset else None),
            normalized_score=(sum(got[q['id']]['score']/4 for q in subset)/len(subset) if subset else None))
    abilities={}
    for ability in sorted({c['ability'] for q in items for c in q['scoring_rubric']}):
        cells=[(q['id'],c) for q in items for c in q['scoring_rubric'] if c['ability']==ability]
        abilities[ability]=dict(n_items=len(set(i for i,_ in cells)),
            criterion_score=sum(got[i]['criteria'][c['id']] for i,c in cells)/sum(c['points'] for _,c in cells),
            interpretation=('method_application_proxy_not_validated_transfer' if ability=='Mathematical Generalization' else 'rubric_criterion_score_not_independent_psychometric_measure'))
    bands={}
    for lo in [1,3,5,7]:
        subset=[q for q in items if lo<=q['difficulty']<=lo+1]
        bands[f'L{lo}–L{lo+1}']=dict(n=len(subset),
            strict_accuracy=sum(got[q['id']]['fully_correct'] for q in subset)/len(subset) if subset else None,
            normalized_score=sum(got[q['id']]['score']/4 for q in subset)/len(subset) if subset else None)
    return dict(n=n,strict_accuracy=fully/n,strict_accuracy_wilson95=wilson(fully,n),
        normalized_score=sum(g['score']/4 for g in got.values())/n,
        difficulty_macro_accuracy=(sum(x['strict_accuracy'] for x in levels.values())/8
                                   if all(x['n'] for x in levels.values()) else None),
        per_difficulty=levels,per_difficulty_band=bands,per_ability=abilities,
        calibration_status='all_difficulty_labels_provisional',
        inference_cost='report from the actual run manifest; not inferred from scores')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('grades',type=Path)
    p.add_argument('--split',choices=['dev','validation','test'],default='test')
    p.add_argument('--output',type=Path)
    p.add_argument('--compare',type=Path,help='Paired comparator grades on exactly the same split')
    args=p.parse_args()
    items=[q for q in read_jsonl(ROOT/'data/items.jsonl') if q['split']==args.split]
    grades=read_jsonl(args.grades)
    report=summarize(items,grades)
    report['split']=args.split
    report['grades_sha256']=hashlib.sha256(args.grades.read_bytes()).hexdigest()
    if args.compare:
        other=read_jsonl(args.compare)
        a=validate_grades(items,grades); b=validate_grades(items,other)
        deltas=[int(a[q['id']]['fully_correct'])-int(b[q['id']]['fully_correct']) for q in items]
        rng=random.Random(20261110)
        draws=sorted(sum(rng.choices(deltas,k=len(deltas)))/len(deltas) for _ in range(10000))
        report['paired_comparison']=dict(strict_accuracy_delta=sum(deltas)/len(deltas),
            bootstrap95=[draws[249],draws[9749]],resampling_unit='unique_problem',seed=20261110,
            caveat='One final response per item; CI is exploratory for small public pilot')
    text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding='utf-8',newline='\n')
    print(text,end='')


if __name__=='__main__':
    main()

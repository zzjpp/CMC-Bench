"""Deterministically export the canonical 333-problem dataset (stdlib only)."""
import collections
import json
from common import ROOT, VERSION, ABILITIES, LEVELS, DESCRIPTORS, SPLITS, read_jsonl, dump, jsonl


def build():
    records=read_jsonl(ROOT/'data/items.jsonl')
    if len(records)!=333:
        raise ValueError('The canonical CMC-Bench corpus must contain exactly 333 problems')
    records.sort(key=lambda q:(q['year'], q['track'], q['id']))
    for split in SPLITS:
        subset = [q for q in records if q['split']==split]
        # Solver inputs deliberately contain no solution, year/track hint, or difficulty.
        jsonl(f'data/inputs/{split}.jsonl', [dict(id=q['id'],question=q['question'],question_latex=q['question_latex'],assets=q['assets']) for q in subset])
        dump(f'splits/{split}.json', [q['id'] for q in subset])
    jsonl('data/metadata.jsonl',[{k:v for k,v in q.items() if k not in {
        'reference_solution','final_answer','scoring_rubric','critical_errors','ability_evidence','solution_source'}} for q in records])
    summary = dict(version=VERSION,total=len(records),
        counts_by_split=dict(collections.Counter(q['split'] for q in records)),
        counts_by_difficulty=dict(sorted(collections.Counter(q['difficulty'] for q in records).items())),
        counts_by_split_and_difficulty={s:{str(i):sum(q['split']==s and q['difficulty']==i for q in records) for i in LEVELS} for s in SPLITS},
        counts_by_subject=dict(collections.Counter(q['subject'] for q in records)),
        counts_by_ability={a:sum(a in q['ability_tags'] for q in records) for a in ABILITIES},
        counts_by_stage=dict(collections.Counter(q['stage'] for q in records)),
        counts_by_track=dict(collections.Counter(q['track'] for q in records)),
        counts_by_year=dict(sorted(collections.Counter(q['year'] for q in records).items())),
        year_semantics='competition_cycle_preliminary_year; finals may occur next calendar year',
        merged_source_occurrences=sum(len(q['source_occurrences'])-1 for q in records),
        heldout_is_public=True, empirical_difficulty_calibrated=False,
        baseline_inference_calls=0, human_certified_items=0,
        inline_full_solutions=sum(q['reference_solution_format']=='inline_full_solution' for q in records),
        scope='Source-backed CMC benchmark; not exhaustive and not official')
    sources=json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))
    occurrences=collections.Counter(o['source_id'] for q in records for o in q['source_occurrences'])
    dump('sources/coverage.json',dict(documents=len(sources),
        indexed_question_papers=sum(n>0 for n in occurrences.values()),
        papers=[dict(source_id=p['source_id'],path=p['path'],indexed_problem_occurrences=occurrences[p['source_id']]) for p in sources],
        exclusions=json.loads((ROOT/'qa/exclusions.json').read_text(encoding='utf-8')),
        warning='Source document coverage is distinct from structured problem coverage.'))
    dump('statistics.json',summary)
    dump('taxonomy.json',dict(abilities=ABILITIES,difficulty_levels=LEVELS,difficulty_descriptors=DESCRIPTORS,
                              generalization='Proxy labels only; true transfer needs a separate controlled study'))
    outline = ['# 题目目录\n','开发集用于调试，验证集用于模型选择，公开测试集冻结后用于最终比较。所有难度均为初步结构标签。\n',
               '| ID | 题目 | 学科 | 难度 | 划分 |','|---|---|---|---:|---|']
    outline += [f"| {q['id']} | {q['title']} | {q['subject']} | L{q['difficulty']} | {q['split']} |" for q in records]
    (ROOT/'CATALOG.md').write_text('\n'.join(outline)+'\n',encoding='utf-8',newline='\n')
    tex = [r'\documentclass[UTF8]{ctexart}',r'\usepackage{amsmath,amssymb,graphicx,geometry}',
           r'\geometry{margin=25mm}',r'\title{CMC-Bench 题目册}',
           r'\date{2026年11月10日}',r'\begin{document}',r'\maketitle',
           '难度为未校准的初步结构标签。本册仅含题目，不含解答。']
    for q in records:
        tex += [r'\section*{'+q['id']+' — '+q['title']+'}',
                f"{q['split']}，L{q['difficulty']}。",q['question_latex']]
        for a in q['assets']:
            tex += [r'\begin{center}\includegraphics[width=0.32\textwidth]{'+a['path']+r'}\end{center}']
    tex += [r'\end{document}']
    (ROOT/'latex').mkdir(exist_ok=True)
    (ROOT/'latex/questions.tex').write_text('\n\n'.join(tex)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    build()

"""Export provider-neutral requests. Does not call models or access solutions."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYSTEM='你是一名数学解题者。请独立解题，给出最终结论与必要的计算或完整证明。不得假设题目未提供的条件。不确定时明确指出尚未完成的步骤。'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--split',choices=['dev','validation','test'],default='dev')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',required=True)
    p.add_argument('--track',choices=['closed_book','tool_assisted'],default='closed_book')
    p.add_argument('--max-output-tokens',type=int,default=8192)
    args=p.parse_args()
    if args.max_output_tokens<=0:
        p.error('max-output-tokens must be positive')
    src=ROOT/f'data/inputs/{args.split}.jsonl'
    rows=[json.loads(x) for x in src.read_text(encoding='utf-8').splitlines() if x.strip()]
    requests=[dict(id=q['id'],messages=[dict(role='system',content=SYSTEM),dict(role='user',content=q['question_latex'])],
                   optional_assets=q['assets'],max_output_tokens=args.max_output_tokens) for q in rows]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in requests),encoding='utf-8',newline='\n')
    manifest=dict(model=args.model,split=args.split,track=args.track,n_items=len(rows),
        max_output_tokens=args.max_output_tokens,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
        request_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        tools=('none' if args.track=='closed_book' else 'MUST preregister exact tool allowlist before running'),
        status='requests_prepared_not_executed',repetitions=1,
        note='id is logging metadata; send only messages to text model. No answer files or source PDFs may be mounted to solver.')
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'Prepared {len(rows)} requests; no inference calls made.')


if __name__=='__main__':
    main()

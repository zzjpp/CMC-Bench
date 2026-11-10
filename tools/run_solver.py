"""Run a text solver against ONLY an exported inputs file; never open gold data."""
import argparse
import json
from pathlib import Path
from http_client import append_json,bind_manifest,complete,digest,load_lines,transport_args,transport_config
from prepare_run import SYSTEM


def run(inputs,outdir,config,attempts=1):
    rows=load_lines(inputs)
    seen=set()
    for q in rows:
        if set(q)!={'id','question','question_latex','assets'} or q['id'] in seen:
            raise ValueError('Inputs must be unique solver-only records with the four exported fields')
        if not isinstance(q['question_latex'],str) or not q['question_latex'].strip():raise ValueError('Empty statement')
        seen.add(q['id'])
    if not rows:raise ValueError('Empty input set')
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    manifest=dict(protocol='cmc-text-solver-1',inputs_sha256=digest(rows),system=SYSTEM,config=config,
                  attempts=attempts,n_items=len(rows),asset_mode='text_only_optional_figures_not_sent',track='closed_book_text')
    bind_manifest(outdir/'manifest.json',manifest)
    path=outdir/'journal.jsonl'
    journal=load_lines(path) if path.exists() else []
    done={}
    for entry in journal:
        if entry['id'] not in seen or entry['id'] in done:raise ValueError('Invalid/duplicate solver journal entry')
        q=next(q for q in rows if q['id']==entry['id'])
        if entry['request_sha256']!=digest(q):raise ValueError('Solver journal input mismatch')
        done[entry['id']]=entry
    for q in rows:
        if q['id'] in done:continue
        calls=[]
        messages=[dict(role='system',content=SYSTEM),dict(role='user',content=q['question_latex'])]
        for _ in range(attempts):
            call=complete(messages=messages,**config);calls.append(call)
            if call['ok']:break
        last=calls[-1]
        entry=dict(id=q['id'],request_sha256=digest(q),calls=calls,response=(last['content'] if last['ok'] else ''),status=('ok' if last['ok'] else 'error'))
        append_json(path,entry);done[q['id']]=entry
        print(f"Solver {len(done)}/{len(rows)}: {q['id']} {entry['status']}",flush=True)
    output=outdir/'responses.jsonl'
    output.write_text(''.join(json.dumps({k:done[q['id']][k] for k in ['id','response','status']},ensure_ascii=False)+'\n' for q in rows),encoding='utf-8',newline='\n')
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    transport_args(p)
    a=p.parse_args()
    run(a.inputs,a.output_dir,transport_config(a),a.attempts)


if __name__=='__main__':main()

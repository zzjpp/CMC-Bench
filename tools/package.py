"""Build a verified, deterministic source ZIP without Git, caches or run outputs."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from common import ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'dist/CMC-Bench.zip')
    args=p.parse_args()
    subprocess.run([sys.executable,str(ROOT/'tools/validate.py')],cwd=ROOT,check=True)
    lock=json.loads((ROOT/'checksums.json').read_text(encoding='utf-8'))
    paths=sorted([*lock,'checksums.json'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in paths:
            target=(ROOT/name).resolve()
            if not target.is_relative_to(ROOT) or '.git' in target.parts:
                raise ValueError(f'Invalid package member: {name}')
            info=zipfile.ZipInfo('CMC-Bench/'+name,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=0o100644<<16
            z.writestr(info,target.read_bytes())
    with zipfile.ZipFile(args.output) as z:
        assert z.testzip() is None,'Corrupted ZIP member'
        for name,digest in lock.items():
            assert hashlib.sha256(z.read('CMC-Bench/'+name)).hexdigest()==digest,name
    digest=hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix+'.sha256').write_text(digest+'  '+args.output.name+'\n',encoding='utf-8',newline='\n')
    print(f'Created {args.output.resolve()} ({len(paths)} files); SHA256 {digest}')


if __name__=='__main__':main()

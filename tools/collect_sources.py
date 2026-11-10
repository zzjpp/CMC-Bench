"""Retrieve missing public PDFs using the frozen source manifest; verify bytes."""
import hashlib
import json
import urllib.request
from common import ROOT


def main():
    sources=json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))
    for src in sources:
        path=(ROOT/src['path']).resolve()
        if not path.is_relative_to(ROOT/'sources/pdf'):
            raise ValueError(src['path'])
        if path.exists():
            data=path.read_bytes()
        else:
            req=urllib.request.Request(src['url'],headers={'User-Agent':'CMC-Bench-source-verification'})
            with urllib.request.urlopen(req,timeout=60) as response:data=response.read()
        assert data.startswith(b'%PDF') and hashlib.sha256(data).hexdigest()==src['sha256'],src['source_id']
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(data)
    print(f'Verified {len(sources)} source PDFs')


if __name__=='__main__':main()

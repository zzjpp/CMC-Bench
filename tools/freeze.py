"""Write release hashes after reviewed edits; ordinary validation never rewrites them."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    paths=[]
    for dirname in ['data','schema','splits','sources','assets','latex','tools','tests','docs','.github','qa']:
        paths.extend(p for p in (ROOT/dirname).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.aux','.log','.out'}
                     and (dirname!='qa' or p.suffix=='.json'))
    paths += [ROOT/p for p in ['.gitattributes','.gitignore','.editorconfig','README.md','CATALOG.md','statistics.json','taxonomy.json','LICENSE','THIRD_PARTY_NOTICES.md','DATASET_CARD.md','requirements-audit.txt']]
    checksums={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (ROOT/'checksums.json').write_text(json.dumps(checksums,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(f'Froze {len(checksums)} release files. Do not rewrite this file merely to bypass a validation failure.')


if __name__=='__main__':
    main()

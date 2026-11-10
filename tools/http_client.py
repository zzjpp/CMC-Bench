"""Small text-only Chat Completions transport; stdlib, no SDK or stored key.

Reference: https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
No remote inference is performed on import or by the test suite.
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def write_json(path,value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def append_json(path,value):
    with Path(path).open('a',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n')
        f.flush()


def load_lines(path):
    rows=[]
    with Path(path).open(encoding='utf-8') as f:
        for n,line in enumerate(f,1):
            if not line.strip():continue
            try:rows.append(json.loads(line,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))))
            except ValueError as e:raise ValueError(f'{path}: invalid JSON at line {n}') from e
    return rows


def endpoint_url(endpoint):
    u=urllib.parse.urlsplit(endpoint)
    if u.username or u.password or u.query or u.fragment or not u.hostname:
        raise ValueError('Use a full endpoint URL without credentials, query or fragment')
    if u.scheme!='https' and not (u.scheme=='http' and u.hostname in {'127.0.0.1','localhost','::1'}):
        raise ValueError('Endpoint requires HTTPS, except local HTTP testing')
    return endpoint


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        # A Bearer key must never be forwarded to another endpoint.
        return None


def complete(endpoint,model,messages,max_tokens=8192,token_parameter='max_completion_tokens',
             key_env='CMC_API_KEY',timeout=120,temperature=None):
    endpoint_url(endpoint)
    if token_parameter not in {'max_completion_tokens','max_tokens'}:
        raise ValueError('Unsupported token parameter')
    if type(max_tokens) is not int or max_tokens<=0 or not 0<timeout<=300:
        raise ValueError('Invalid token budget or timeout')
    body=dict(model=model,messages=messages,**{token_parameter:max_tokens})
    if temperature is not None:body['temperature']=temperature
    headers={'Content-Type':'application/json'}
    key=os.environ.get(key_env,'')
    if key:headers['Authorization']='Bearer '+key
    request=urllib.request.Request(endpoint,data=json.dumps(body,ensure_ascii=False,allow_nan=False).encode(),headers=headers,method='POST')
    start=time.monotonic()
    usage=None
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=timeout) as response:
            raw=response.read(8_000_001)
        if len(raw)>8_000_000:raise ValueError('Response exceeds 8 MB limit')
        payload=json.loads(raw)
        choices=payload.get('choices',[])
        if len(choices)!=1:raise ValueError('Expected exactly one completion')
        choice=choices[0]
        content=choice.get('message',{}).get('content')
        usage=payload.get('usage')
        if usage is not None:
            if not isinstance(usage,dict):raise ValueError('Invalid usage object')
            usage={k:v for k,v in usage.items() if k in {'prompt_tokens','completion_tokens','total_tokens','completion_tokens_details','prompt_tokens_details'}}
        if not isinstance(content,str) or not content.strip():raise ValueError('Empty/nontext completion')
        if choice.get('finish_reason')!='stop':raise ValueError('Completion did not finish normally')
        return dict(ok=True,content=content,usage=usage,model=payload.get('model',model),elapsed_seconds=time.monotonic()-start)
    except urllib.error.HTTPError as e:
        # Never persist server error bodies: they can echo credentials.
        return dict(ok=False,error=f'HTTP {e.code}',usage=None,elapsed_seconds=time.monotonic()-start)
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError,TypeError) as e:
        return dict(ok=False,error=type(e).__name__,usage=usage,elapsed_seconds=time.monotonic()-start)


def bind_manifest(path,manifest):
    path=Path(path)
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=manifest:
            raise ValueError('Resume rejected: inputs, prompt, endpoint or run configuration changed; use a new run directory')
    else:write_json(path,manifest)


def transport_args(parser):
    parser.add_argument('--endpoint',required=True,help='Full HTTPS Chat Completions URL; local HTTP is allowed for testing')
    parser.add_argument('--model',required=True)
    parser.add_argument('--key-env',default='CMC_API_KEY',help='Name of environment variable; never pass the key itself')
    parser.add_argument('--token-parameter',choices=['max_completion_tokens','max_tokens'],default='max_completion_tokens')
    parser.add_argument('--max-tokens',type=int,default=8192)
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--attempts',type=int,choices=[1,2,3],default=1)
    parser.add_argument('--temperature',type=float,help='Omit to use endpoint default; some models do not accept this field')


def transport_config(args):
    endpoint_url(args.endpoint)
    if args.max_tokens<=0 or not 0<args.timeout<=300:raise ValueError('Invalid budget/timeout')
    return {k:getattr(args,k) for k in ['endpoint','model','key_env','token_parameter','max_tokens','timeout','temperature']}

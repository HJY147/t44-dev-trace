"""Bounded own-fixture failure projection; no session/token/password/log body output."""
import ast,hashlib,json,re
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'F05';L=R/'r30finalf05-launcher'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):
 if p.is_symlink() or p.stat().st_size>2000000:raise ValueError('BOUNDED_ORIGINAL_REQUIRED')
 return p.read_bytes()
def main():
 report={'kind':'F05_F_PROJECT_OWN_FAILURE_DIAGNOSTIC','state_changed':False,'private_log_bodies_disclosed':False,'files':{}}
 for p in [L/'08-F-project.stdout.private',L/'08-F-project.stderr.private',F/'F-http/execution.PUBLIC.json',F/'F-http/runtime.PUBLIC.json',F/'F-http/logs/runtime.stdout.private',F/'F-http/logs/runtime.stderr.private',F/'F-http/logs/http.stdout.private',F/'F-http/logs/http.stderr.private']:
  name=str(p.relative_to(R));row={'exists':p.is_file()};report['files'][name]=row
  if not p.is_file():continue
  raw=read(p);row.update(bytes=len(raw),sha256=sha(raw))
  try:
   v=json.loads(raw);row['safe_envelope']={k:v.get(k) for k in ['status','error_type','error','output','kind'] if k in v and isinstance(v[k],(str,int,bool,type(None)))}
  except (ValueError,UnicodeError):pass
  text=raw.decode(errors='replace');row['fixed_error_codes']=list(dict.fromkeys(re.findall(r'(?:ValueError|RuntimeError|Refused|TimeoutError): ([A-Z][A-Z0-9_]{3,180})(?=\s|$)',text)))
  row['exception_classes']=list(dict.fromkeys(re.findall(r'\b(ValueError|RuntimeError|Refused|TimeoutError|FileNotFoundError|CalledProcessError|PermissionError|KeyError|AttributeError|TypeError)\b',text)))
  row['trace_locations']=re.findall(r'File "([^"\n]{1,180})", line (\d+), in ([A-Za-z0-9_]+)',text)[-8:]
 for name in ['F-http','F-http/output','F-http/output/result']:
  p=F/name
  report[name]={'exists':p.exists(),'result_filenames':sorted(x.name for x in p.iterdir() if x.is_file()) if p.is_dir() and name.endswith('result') else []}
 # Read only literal template constants, never runtime env or fixture values.
 p=F/'runtime/f-http-prepare.py'
 if p.is_file():
  tree=ast.parse(read(p));report['wrapper_constants']={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['SOURCE','CONFIG','ADMIN_SHA','SOURCE_MANIFEST','BUNDLE']}
 print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()

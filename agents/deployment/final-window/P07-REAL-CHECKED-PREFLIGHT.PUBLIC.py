"""Read-only actual P06 HTTP checked gates and wallclock evidence; never HTTP/run/stage."""
import ast,datetime,hashlib,importlib.util,json,re,types,os,stat
from pathlib import Path
R=Path('/root/t44-final-20261029');F=R/'P06';T=R/'ops01/deployment/cloud-reuse'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lp=T/'P06-CONTINUOUS-fast10.PUBLIC.py';tree=ast.parse(lp.read_bytes());c=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='C' for x in n.targets));code=Path(ast.literal_eval(c.value.args[0]));p=F/'runtime/http-prepare.py';spec=importlib.util.spec_from_file_location('p06checked',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);plan=json.loads((F/'P-inputs/http-plan.json').read_bytes());binding=plan['target']['binding_sha256']
 args=types.SimpleNamespace(phase_dir=F/'campaign/p',binding_sha256=binding,code_dir=code,code_manifest_sha256=sha(code/'code-manifest.PUBLIC.json'),source_profile=Path(ast.literal_eval(next(n.value.args[0] for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PROFILE' for x in n.targets)))),plan=F/'P-inputs/http-plan.json',accounts=F/'P-accounts/output/accounts.initialized.private.json',service=F/'P-service/output/result/service.json',import_receipt=F/'backend-import-receipt.PUBLIC.json',ca=F/'campaign/p/tls/ca.pem',output_dir=F/'P-http')
 # Stage a NEW host-owned exact-byte copy outside every old phase; original is read only.
 source=args.service;st=source.lstat()
 if st.st_uid!=10001 or stat.S_IMODE(st.st_mode)!=0o600 or not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise ValueError('EXACT_ORIGINAL_SERVICE_OWNER_MODE_REQUIRED')
 area=R/'P07-preflight-inputs';area.mkdir(mode=0o700);copy=area/'service.original-root-copy.private.json'
 with copy.open('xb') as out:out.write(source.read_bytes())
 copy.chmod(0o600)
 if sha(copy)!=sha(source) or copy.stat().st_uid!=os.geteuid():raise ValueError('EXACT_BYTE_HOST_COPY_REQUIRED')
 args.service=copy
 a=m.tools();report={'kind':'P06_ACTUAL_HTTP_CHECKED_ONLY_NO_HTTP','clock':{**plan['window'],**plan['lifecycle']},'now_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'P_http_exists':args.output_dir.exists(),'wrapper_sha256':sha(p),'checks':{}}
 out=R/'r30finalp06-resume02-launcher/07-http.stdout.private';attempt=out.stat().st_mtime;report['actual_failure_stdout_mtime_utc']=datetime.datetime.fromtimestamp(attempt,datetime.timezone.utc).isoformat()
 original=m.time.time
 for label,at in [('original_failure_file_mtime_with_exact_root_service_copy',attempt)]:
  try:
   m.time.time=lambda:at;value,inputs,timeout=m.checked(args,a);report['checks'][label]={'success':True,'timeout_seconds':timeout,'source':value['source_sha'],'actual_image_and_edge':m.image_and_edge(value)}
  except Exception as e:
   reason=str(e);report['checks'][label]={'success':False,'error_class':type(e).__name__,'fixed_code':reason if re.fullmatch('[A-Z0-9_:. -]{1,200}',reason) else 'DETAIL_REDACTED'}
  finally:m.time.time=original
 report['same_byte_service_copy']={'original_uid':st.st_uid,'copy_uid':copy.stat().st_uid,'mode':stat.S_IMODE(copy.stat().st_mode),'sha256':sha(copy),'original_retained':True}
 report['timing_gate_expressions']=[x.strip() for x in p.read_text().splitlines() if 't0 +' in x or 'cutoff !=' in x or '780 <=' in x]
 print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()

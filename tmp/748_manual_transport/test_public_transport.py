from pathlib import Path
import base64,hashlib,importlib.util,io,json,tarfile,tempfile,ast
D=Path(__file__).resolve().parents[2]/'agents/deployment/manual-handoff'
spec=importlib.util.spec_from_file_location('builder',D/'build_user_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
package=Path('/Users/yang/Desktop/nothing/软件开发大作业/tmp/753_fresh_acceptance_90b/PUBLIC/MANUAL_TOOL_V4.PUBLIC.tar.gz')
with tempfile.TemporaryDirectory()as tmp:
 root=Path(tmp).resolve();bp=root/'bootstrap.PUBLIC.json';bp.write_text('{"status":"SYNTHETIC_PUBLIC_BOOTSTRAP_TEST_ONLY"}\n');out=root/'send';w=root/'newworkspace'
 v=m.build(package,bp,out,out,w);assert len(v['parts'])==4
 for row in v['parts']:assert len(base64.b64encode((out/row['name']).read_bytes()))<=32768
 raw=b''.join((out/x['name']).read_bytes()for x in v['parts']);assert raw==package.read_bytes();files=m.r.validate_archive(raw);assert len(files)==13
 command=(out/'USER_LOAD_RECEIVE.PUBLIC.sh').read_text();assert len(command.encode())<=16384
 # Execute the actual generated receiving command's Python with local fixture paths: only temp writes.
 code=command.split("<<'MANUAL_PUBLIC_RECEIVE'\n",1)[1].rsplit('\nMANUAL_PUBLIC_RECEIVE',1)[0];ast.parse(code,feature_version=(3,10));exec(compile(code,'local-user-receiver-test','exec'),{'__name__':'test'})
 assert (w/'MANUAL_TOOL_V4.original.PUBLIC.tar.gz').read_bytes()==raw and (w/'bootstrap.original.PUBLIC.json').read_bytes()==bp.read_bytes()
 for n,b in files.items():assert (w/n).read_bytes()==b
 # Preferred full GUI upload path uses unchanged single original tar.gz plus one short command.
 out2=root/'whole';w2=root/'wholeworkspace';v2=m.build(package,bp,out2,out2,w2);(out2/'MANUAL_TOOL_V4.PUBLIC.tar.gz').write_bytes(raw)
 whole=(out2/'USER_LOAD_RECEIVE_WHOLE.PUBLIC.sh').read_text();wholecode=whole.split("<<'MANUAL_PUBLIC_RECEIVE'\n",1)[1].rsplit('\nMANUAL_PUBLIC_RECEIVE',1)[0];exec(compile(wholecode,'whole-receiver-local-test','exec'),{'__name__':'test'})
 assert (w2/'MANUAL_TOOL_V4.original.PUBLIC.tar.gz').read_bytes()==raw and len(whole.encode())<=16384
 try:m.r.receive(v,bp.read_bytes(),out,w);raise AssertionError('overwriting workspace accepted')
 except ValueError:pass
 try:m.r.receive(v,bp.read_bytes()+b' ',out,root/'wrongboot');raise AssertionError('altered bootstrap accepted')
 except ValueError:pass
 part=out/v['parts'][0]['name'];part.write_bytes(b'0'+part.read_bytes()[1:])
 try:m.r.receive(v,bp.read_bytes(),out,root/'badpart');raise AssertionError('tampered part accepted')
 except ValueError:pass
 for path in ['../escape','/absolute','public/link']:
  stream=io.BytesIO()
  with tarfile.open(fileobj=stream,mode='w:gz')as t:
   member=tarfile.TarInfo(path);member.type=tarfile.SYMTYPE if path=='public/link'else tarfile.REGTYPE;member.linkname='../escape';t.addfile(member,io.BytesIO(b''))
  try:m.r.validate_archive(stream.getvalue());raise AssertionError('unsafe archive accepted')
  except ValueError:pass
 print(json.dumps({'status':'LOCAL_ACTUAL_ENCODE_HASH_UNPACK_AND_GENERATED_RECEIVER_PASSED','package_bytes':len(raw),'package_sha256':m.r.sha(raw),'part_bytes':[x['bytes']for x in v['parts']],'base64_part_limit':32768,'public_files':len(files),'receive_command_bytes':len(command.encode()),'negative_cases':['changed part','changed bootstrap','existing workspace','traversal','absolute','symlink'],'cloud_SSH_INSTALL_790_QA_executed':False},sort_keys=True))
# Actual published P09 bootstrap bytes are transport-only fixture: no old clock reused or executed.
actual=Path('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/resume-20261030/P09-public-originals/LOAD-bootstrap.original.PUBLIC.json')
if actual.is_file():
 import zlib
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp).resolve();v=m.build(package,actual,root/'actual',root/'remote-stage-placeholder',root/'unused-workspace');text=(root/'actual/USER_LOAD_RECEIVE_WHOLE.PUBLIC.sh').read_text();encoded=text.split('blob=base64.b64decode(',1)[1].split(');assert',1)[0].strip("'");payload=json.loads(zlib.decompress(base64.b64decode(encoded)));original=base64.b64decode(payload['bootstrap_b64'],validate=True);assert original==actual.read_bytes()and m.r.sha(original)==v['bootstrap_sha256']
  print(json.dumps({'status':'PUBLISHED_P09_BOOTSTRAP_BYTEEXACT_INLINE_ENCODING_VERIFIED_NOT_EXECUTED','bootstrap_bytes':len(original),'bootstrap_sha256':m.r.sha(original),'whole_receive_command_bytes':len(text.encode()),'old_clock_reused_as_new':False,'cloud_or_QA_executed':False},sort_keys=True))

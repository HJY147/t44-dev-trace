"""LOCAL ONLY: build four CloudAssistant upload parts and a short user receive command."""
import argparse,base64,hashlib,importlib.util,json,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('receiver',HERE/'receive_public_bundle.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def build(package,bootstrap,output,remote_parts,workspace):
 raw=Path(package).read_bytes();b=Path(bootstrap).read_bytes()
 if r.sha(raw)!=r.PACKAGE_SHA:raise ValueError('ORIGINAL_MANUAL_V4_PACKAGE_REQUIRED')
 r.validate_archive(raw);json.loads(b)
 if len(b)>16000:raise ValueError('BOOTSTRAP_TOO_LARGE_FOR_SINGLE_PASTE_USE_FILE_UPLOAD')
 out=Path(output);out.mkdir(exist_ok=False);parts=[]
 for i,offset in enumerate(range(0,len(raw),24576),1):
  chunk=raw[offset:offset+24576];name='MANUALV4.part%02d.bin'%i;(out/name).write_bytes(chunk);assert len(base64.b64encode(chunk))<=32768;parts.append({'name':name,'bytes':len(chunk),'sha256':r.sha(chunk)})
 meta={'archive_sha256':r.sha(raw),'bootstrap_sha256':r.sha(b),'bootstrap_bytes':len(b),'parts':parts}
 (out/'parts-manifest.PUBLIC.json').write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n')
 source=(HERE/'receive_public_bundle.py').read_text().split("if __name__=='__main__':",1)[0]
 payload={'source':source,'source_sha256':r.sha(source.encode()),'meta':meta,'bootstrap_b64':base64.b64encode(b).decode(),'remote_parts':str(remote_parts),'workspace':str(workspace)};compressed=zlib.compress(json.dumps(payload,separators=(',',':')).encode(),9)
 command="umask 077\npython3 -B - <<'MANUAL_PUBLIC_RECEIVE'\nimport base64,hashlib,json,zlib\nblob=base64.b64decode("+repr(base64.b64encode(compressed).decode())+");assert hashlib.sha256(blob).hexdigest()=="+repr(r.sha(compressed))+"\nD=json.loads(zlib.decompress(blob));assert hashlib.sha256(D['source'].encode()).hexdigest()==D['source_sha256']\nns={'__name__':'manual_public_receiver'};exec(compile(D['source'],'public-receiver','exec'),ns)\nprint(json.dumps(ns['receive'](D['meta'],base64.b64decode(D['bootstrap_b64'],validate=True),D['remote_parts'],D['workspace']),sort_keys=True))\nMANUAL_PUBLIC_RECEIVE\n"
 if len(command.encode())>16384:raise ValueError('RECEIVE_PASTE_EXCEEDS16K')
 (out/'USER_LOAD_RECEIVE.PUBLIC.sh').write_text(command)
 whole=dict(payload);whole['meta']={**meta,'parts':[{'name':'MANUAL_TOOL_V4.PUBLIC.tar.gz','bytes':len(raw),'sha256':r.sha(raw)}]};wholecompressed=zlib.compress(json.dumps(whole,separators=(',',':')).encode(),9)
 wholecommand=command.replace(repr(base64.b64encode(compressed).decode()),repr(base64.b64encode(wholecompressed).decode())).replace(repr(r.sha(compressed)),repr(r.sha(wholecompressed)))
 assert len(wholecommand.encode())<=16384
 (out/'USER_LOAD_RECEIVE_WHOLE.PUBLIC.sh').write_text(wholecommand)
 return {'status':'LOCAL_USER_TRANSPORT_PREPARED_NOT_SENT','part_count':len(parts),'receive_command_bytes':len(command.encode()),'whole_file_receive_command_bytes':len(wholecommand.encode()),'receive_command_sha256':r.sha(command.encode()),**meta}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--bootstrap',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--remote-parts',required=True);p.add_argument('--workspace',required=True);a=p.parse_args();print(json.dumps(build(a.package,a.bootstrap,a.output,a.remote_parts,a.workspace),sort_keys=True))

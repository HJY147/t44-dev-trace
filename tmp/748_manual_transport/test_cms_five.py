from pathlib import Path
import importlib.util,json,subprocess,tempfile,io,tarfile
D=Path(__file__).resolve().parents[2]/'agents/deployment/manual-handoff'
s=importlib.util.spec_from_file_location('cmsfive',D/'cms_five_transport.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
binary='/Users/yang/miniconda3/bin/openssl'
with tempfile.TemporaryDirectory()as tmp:
 r=Path(tmp).resolve();key=r/'synthetic-test-only.key';subprocess.run([binary,'genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',str(key)],capture_output=True,check=True)
 c=r/'recipient.PUBLIC.pem';certificate=m.cert(binary,key,c);inputs=r/'synthetic-five';inputs.mkdir();original={n:('SYNTHETIC_NOT_REAL_'+n+'\n').encode()for n in m.NAMES}
 for n,b in original.items():(inputs/n).write_bytes(b)
 cipher=r/'packet.cms';rec=m.seal(binary,inputs,c,certificate['cert_sha256'],cipher);out=r/'opened';v=m.opened(binary,cipher,Path(str(cipher)+'.PUBLIC.json'),c,certificate['cert_sha256'],key,out)
 assert all((out/('inputs/'+n)).read_bytes()==b for n,b in original.items())
 for fn in [lambda:m.cert(binary,key,c),lambda:m.seal(binary,inputs,c,certificate['cert_sha256'],cipher),lambda:m.opened(binary,cipher,Path(str(cipher)+'.PUBLIC.json'),c,certificate['cert_sha256'],key,out)]:
  try:fn();raise AssertionError('overwrite accepted')
  except ValueError:pass
 tampered=r/'tampered.cms';raw=bytearray(cipher.read_bytes());raw[-1]^=1;tampered.write_bytes(raw)
 try:m.opened(binary,tampered,Path(str(cipher)+'.PUBLIC.json'),c,certificate['cert_sha256'],key,r/'badsha');raise AssertionError('cipher mismatch accepted')
 except ValueError:pass
 # Even with a matching external SHA, CMS GCM must reject altered tag/cipher and write no plaintext directory.
 forged={**rec,'cipher_sha256':m.sha(raw)};fp=r/'tampered.PUBLIC.json';fp.write_text(json.dumps(forged))
 try:m.opened(binary,tampered,fp,c,certificate['cert_sha256'],key,r/'badtag');raise AssertionError('GCM tamper accepted')
 except ValueError:pass
 assert not(r/'badtag').exists()
 try:m.seal(binary,inputs,c,'0'*64,r/'badcert');raise AssertionError('certificate substitution accepted')
 except ValueError:pass
 for member_name,kind in [('../escape',tarfile.REGTYPE),('/absolute',tarfile.REGTYPE),('inputs/session.private.json',tarfile.SYMTYPE)]:
  buf=io.BytesIO()
  with tarfile.open(fileobj=buf,mode='w')as archive:
   member=tarfile.TarInfo(member_name);member.type=kind;member.linkname='../escape';archive.addfile(member,io.BytesIO(b''))
  badplain=buf.getvalue()
  try:m.unpack_plain(badplain,{**rec,'plain_tar_sha256':m.sha(badplain)});raise AssertionError('unsafe tar accepted')
  except ValueError:pass
 try:m.modern('/usr/bin/openssl');raise AssertionError('LibreSSL silently accepted')
 except ValueError:pass
 print(json.dumps({'status':'LOCAL_STANDARD_CMS_GCM_ROUNDTRIP_AND_NEGATIVES_PASSED','openssl':m.command(binary,['version']).decode().strip(),'synthetic_files':5,'exact_original_bytes':True,'cipher_bytes':len(cipher.read_bytes()),'negative_cases':['existing cert','existing cipher','existing opened','modified cipher SHA','modified GCM tag despite matching external SHA','substituted cert pin','tar traversal/absolute/symlink','LibreSSL no downgrade'],'cloud_or_real_credentials_used':False,'private_plaintext_printed':False},sort_keys=True))

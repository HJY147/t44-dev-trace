python3 - <<'PY'
import base64,hashlib,json,subprocess,urllib.parse,urllib.request
COMMIT = 'c1303016a053d5b718d3df30ce5911d2e002c18c'
FILES = [{'path': 'agents/deployment/v4-f7-20z-20261028/delivery-f7-2000/01-part-000.sh', 'bytes': 11337, 'sha256': 'ff3a3c2c8ece6ee9727ff7eda0eb6606547236cd21eb9b009eeaaa17396bc7b5'}, {'path': 'agents/deployment/v4-f7-20z-20261028/delivery-f7-2000/02-part-001.sh', 'bytes': 10624, 'sha256': '9966155a0e2878841c1f926689d1c80612ad6be415f4ac5388c70f55040fe0ad'}, {'path': 'agents/deployment/v4-f7-20z-20261028/delivery-f7-2000/03-part-002.sh', 'bytes': 10624, 'sha256': 'e9ef64467c8c65b983fdc91e4c43f38ae82a1fe3cba97fc832eb5b5326701c4b'}, {'path': 'agents/deployment/v4-f7-20z-20261028/delivery-f7-2000/04-part-003.sh', 'bytes': 10624, 'sha256': 'a920a0ff0eb6b5560e772fc988364b4a5df296f6771b4839786311dc7c79396d'}, {'path': 'agents/deployment/v4-f7-20z-20261028/delivery-f7-2000/05-part-004.sh', 'bytes': 5512, 'sha256': '7485c2520b01dca93791359a684c25956bef479ec6203036eb88e4a9249d9f0f'}, {'path': 'agents/deployment/v4-f7-20z-20261028/delivery-f7-2000/06-verify-install.sh', 'bytes': 3337, 'sha256': '0304b2466e3bf2b841663add790050fd286c7539c2eb79fc870d5847948b2328'}]
verified=[]
for item in FILES:
 url='https://api.github.com/repos/HJY147/t44-dev-trace/contents/'+urllib.parse.quote(item['path'],safe='/')+'?ref='+COMMIT
 request=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'t44-fixed-public-code-install'})
 with urllib.request.urlopen(request,timeout=20) as response:
  content=response.read(100001)
 if len(content)>100000: raise ValueError('BOUNDED_PUBLIC_RESPONSE_REQUIRED')
 record=json.loads(content)
 if record.get('type')!='file' or record.get('path')!=item['path'] or record.get('size')!=item['bytes'] or record.get('encoding')!='base64': raise ValueError('EXACT_FIXED_PUBLIC_FILE_REQUIRED')
 raw=base64.b64decode(''.join(record['content'].split()),validate=True)
 if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']: raise ValueError('EXACT_REVIEWED_PUBLIC_CODE_SHA_REQUIRED')
 verified.append((item['path'],raw))
# Fetch and verify every complete command before any installation mutation.
for path,raw in verified:
 result=subprocess.run(['bash'],input=raw,check=False)
 if result.returncode: raise ValueError('PUBLIC_INSTALL_STEP_FAILED_PRESERVE_PARTIAL_STATE:'+path)
print(json.dumps({'success':True,'public_code_commit':COMMIT,'steps':len(verified),'profile_dir':'/root/t44-r9/v4-code-20261028-03/profile','SUT_or_services_started':False}))
PY

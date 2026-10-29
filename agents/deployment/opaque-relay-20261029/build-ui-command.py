"""Produce a <=16KB UI shell command from only a coordinator-provided public JSON."""
import argparse,base64,json,zlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('operation',choices=['load-key','app-resource','load-resource','app-stage1','load-start','app-producer'])
p.add_argument('--public-input',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();raw=a.public_input.read_bytes() if a.public_input else b'{}'
assert len(raw)<=25000;json.loads(raw)
blob=base64.b64encode(zlib.compress(raw,9)).decode()
command="#!/bin/sh\nset -eu\numask 077\npython3 -I -B /root/t44-r9/ops-r29-01.py "+a.operation+" --public-input-zlib-b64 '"+blob+"'\n"
assert len(command.encode())+300<=16000,'DO_NOT_SEND_OVERSIZE_UI_COMMAND'
with a.output.open('xb') as f:f.write(command.encode())
print(json.dumps({'operation':a.operation,'UI_bytes_plus_300':len(command.encode())+300,'script':str(a.output.resolve()),'executed':False}))

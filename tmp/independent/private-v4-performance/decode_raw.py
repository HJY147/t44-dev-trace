"""Offline export only; no application imports, HTTP, SQL, browser or Docker operations."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import struct
import sys

FRAME = struct.Struct('<QIHHIHHII')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('--events', type=Path)
    args = parser.parse_args()
    if args.events:
        with gzip.open(args.events, 'rt') as source:
            for line in source:
                json.loads(line)
                sys.stderr.write(line)
    writer = csv.writer(sys.stdout)
    writer.writerow(['start_us','latency_us','vu','opcode','sequence','http_status','phase','failure',
                     'planned_rejection','fixture_ordinal','input_expected_version'])
    with gzip.open(args.trace,'rb') as stream:
        if stream.read(8) != b'T44PV4\x00\x01' or struct.unpack('<I',stream.read(4))[0] != FRAME.size:
            raise SystemExit('Unsupported raw format')
        while True:
            chunk=stream.read(FRAME.size)
            if not chunk:
                break
            if len(chunk)!=FRAME.size:
                raise SystemExit('Incomplete raw frame; no passing conclusion')
            started,elapsed,vu,op,seq,status,flags,ordinal,version=FRAME.unpack(chunk)
            writer.writerow([started,elapsed,vu,op,seq,status,(flags>>1)&3,bool(flags&1),bool(flags&8),ordinal,version])

if __name__=='__main__':
    main()

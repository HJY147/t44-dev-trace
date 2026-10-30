"""Validate integrated assets; --refresh updates current hashes, retaining creator hashes."""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

base = Path(__file__).parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--refresh', action='store_true')
args = parser.parse_args()
path = base / 'manifest.json'
manifest = json.loads(path.read_text())
assert len(manifest['figures']) == 18
for item in manifest['figures']:
    png = base / (item['id'] + '.png')
    svg = base / (item['id'] + '.svg')
    digest = hashlib.sha256(png.read_bytes()).hexdigest()
    svg_digest = hashlib.sha256(svg.read_bytes()).hexdigest()
    if args.refresh:
        item['sha256'] = digest
        item['integrated_svg_sha256'] = svg_digest
    else:
        assert digest == item['sha256'], item['id'] + ' PNG differs'
        assert svg_digest == item.get('integrated_svg_sha256', item['files']['svg']['sha256']), item['id'] + ' SVG differs'
    with Image.open(png) as im:
        assert list(im.size) == item['size_px']
if args.refresh:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('18 integrated PNG/SVG assets and dimensions verified; creator hashes retained')

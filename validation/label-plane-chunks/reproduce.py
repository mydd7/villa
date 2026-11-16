import argparse
import cProfile
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import pstats
import shutil
import time
import psutil
from vc_reader.reader import open_group
from vesuvius.ink_detection import label_zarr
from vesuvius.ink_detection.preprocessing import create_label_zarrs as labels

parser = argparse.ArgumentParser()
parser.add_argument('mask_tiff', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--workers', type=int, default=1)
parser.add_argument('--levels', type=int, default=6)
args = parser.parse_args()
expected = '70d5f3d7c849fdc24c04e903791adf047ec95f590246b7472e33f411ebc19a1a'
if hashlib.sha256(args.mask_tiff.read_bytes()).hexdigest() != expected:
    raise ValueError('The full published Paris4 supervision mask is required')
args.output.mkdir(exist_ok=False)
source = args.output / 'w00_supervision_mask.tif'
shutil.copyfile(args.mask_tiff, source)
profile = cProfile.Profile()
cpu_start = psutil.Process().cpu_times()
start = time.perf_counter()
profile.enable()
labels.convert_image(source, levels=args.levels, overwrite=False, chunk_workers=args.workers)
profile.disable()
seconds = time.perf_counter() - start
cpu_stop = psutil.Process().cpu_times()
with (args.output / 'profile.txt').open('w', encoding='utf-8') as output:
    pstats.Stats(profile, stream=output).strip_dirs().sort_stats('cumulative').print_stats(20)
group = open_group(source.with_suffix('.zarr'))
files = [p for p in source.with_suffix('.zarr').rglob('*') if p.is_file()]
report = {
    'seconds': seconds,
    'cpu_seconds': cpu_stop.user + cpu_stop.system - cpu_start.user - cpu_start.system,
    'peak_working_set_bytes': getattr(psutil.Process().memory_info(), 'peak_wset', None),
    'platform': platform.system(),
    'python': platform.python_version(),
    'versions': {name: importlib.metadata.version(name) for name in ['numpy', 'psutil']},
    'source_sha256': expected,
    'workers': args.workers,
    'source_files_sha256_lf': {Path(m.__file__).name: hashlib.sha256(Path(m.__file__).read_bytes().replace(b'\r\n', b'\n')).hexdigest() for m in [labels, label_zarr]},
    'levels': [{'shape': list(group[str(i)].shape), 'chunks': list(group[str(i)].chunks)} for i in range(args.levels)],
    'output_files': len(files),
    'output_bytes': sum(p.stat().st_size for p in files),
}
(args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))

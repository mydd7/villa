import argparse
import io
import json
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image
from vc_reader import Source, Storage

parser = argparse.ArgumentParser()
parser.add_argument('--expect-residue', action='store_true')
args = parser.parse_args()
url = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0800/segments/20251029010146-auto_grown_20251029010146642/mesh/20251029010146-on-20250521135224-8.64um.tifxyz/x.tif'
with urlopen(url, timeout=30) as response:
    expected = np.asarray(Image.open(io.BytesIO(response.read())))
reader = Source('PHerc0800', Storage(url, 'tiff')).open(cache_writes=False)
try:
    actual = reader.read((0, 0), expected.shape)
    temporary = Path(reader._engine().temporary_directory)
finally:
    reader.close()
np.testing.assert_array_equal(actual, expected)
result = {
    'sample': 'PHerc0800',
    'pixels_identical': True,
    'temporary_cache_removed': not temporary.exists(),
    'remaining_files': sorted(p.name for p in temporary.rglob('*') if p.is_file()) if temporary.exists() else [],
}
print(json.dumps(result, indent=2))
assert result['temporary_cache_removed'] != args.expect_residue

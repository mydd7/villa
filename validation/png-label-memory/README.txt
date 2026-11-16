PNG label pyramid memory validation

Source: PHerc. Paris4 w00_20231016151002 published supervision mask.
The input is an unchanged crop encoded losslessly as PNG; source coordinates
and SHA256 are in source.json. No synthetic labels were used.

From a villa checkout with its Python/native dependencies installed:

python reproduce.py input-mask.png before-1.json --repository . --source-ref 14f56f2b39eec158addef00466ffe64570639dd1
python reproduce.py input-mask.png after-1.json --repository .

Repeat each command in three separate processes for the min/median/max.
Run the after command with fix/png-label-volume-memory selected, and the
vesuvius Python sources loaded from that checkout (an editable installation
or PYTHONPATH=vesuvius/src). The script stages a copy of the PNG and its
output in a temporary directory, so it does not replace your existing files.
It records a stripped cProfile summary next to each JSON. Compare every
output_files mapping and the three levels, not just the timings.

Measured here on Windows x64, Ryzen 5 7500F,32 GiB, Python 3.14.7, NumPy 2.5.4.
Three pyramid levels, one chunk worker. The source was in the OS file cache.
Timing excludes imports, input staging, output verification and cleanup.
tracemalloc covers NumPy/Python allocations, not native allocations.
Process peaks are psutil peak_wset and peak_pagefile on Windows; these fields
are null on platforms where psutil does not provide them.

The Windows runtime hashes and previously proposed build/shutdown adaptations
are recorded in validation.json. No native code was changed in this PR.

All 33 OME-Zarr files are identical between every before/after run, including
metadata and compressed payloads. The pixel, shape, dtype and empty-plane
regressions also cover grayscale/RGB/RGBA PNG and uint8/uint16 arrays.

The original TIFF streaming path is unchanged. The decoded 2D source still
resides in memory. Full-segment conversion, Linux, macOS and CUDA were not run.

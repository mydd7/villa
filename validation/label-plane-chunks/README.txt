Flat label pyramids on the complete published Paris4 mask

Input: ink/phercparis4/w00_20231016151002/w00_20231016151002_supervision_mask.tif
https://huggingface.co/buckets/scrollprize/datasets/resolve/ink/phercparis4/w00_20231016151002/w00_20231016151002_supervision_mask.tif
SHA256: 70d5f3d7c849fdc24c04e903791adf047ec95f590246b7472e33f411ebc19a1a
Shape: 32249 x 51380, uint8. The entire image is converted, not a resized crop.
Six OME levels, one file worker and one native chunk worker, nearest labels.

The logical depth remains 65, with labels at Z=32. New stores use chunks
(1, 128, 128) rather than (65, 128, 128). Missing planes retain zero fill.
Only the annotated Z chunk is visited when building XY pyramid levels.
PNG/direct array inputs also retain the earlier direct-plane write fix.

Before: upstream e413746da00ba333cd90974da6b82c487cdbb641's converter, with
its original 65-plane chunk constant. It has the same TIFF-conversion code
as 14f56f2. After: the source revision recorded in validation.json.
The before runs load that unmodified converter from an extracted module
and restore its original chunk constant; after runs use the project module.
Native reader binaries are identical in both configurations, including the
Windows build adaptations recorded in validation.json. No native changes.

Measurement protocol
Separate Python processes and fresh output stores, alternating before/after.
The first pair was exploratory; reported summary statistics use the later
two pairs on the final source implementation. cProfile covers convert_image;
imports, input staging, parity checks and output inventory are outside timing.
The source is local and already in the OS file cache. No network time.
Min/median/max and raw per-process records are in validation.json.
Stripped profiles show level-zero writing and pyramid writing separately.
These are measurements on one Windows CPU, not a cross-platform speed claim.

Correctness
The six complete annotated planes are compared between the old and new
outputs, row by row. Shapes/dtypes match; hashes and counts are in parity.json.
Only Z=32 chunks are physically stored after conversion, so other Z planes
retain zero fill. 42 preprocessing tests cover real masks, odd image sizes,
uint8/uint16, nearest/rounded mean, PNG/striped/tiled TIFF paths, padded reads
used by training, old 65-plane chunks and the PNG allocation regression.
Physical chunk metadata and compressed files intentionally differ.

Reproduction
In a working project Python environment with psutil installed:
  python reproduce.py FULL_MASK_TIFF NEW_OUTPUT --workers 1 --levels 6
Run once per source version, with a new output directory for each process.
For a complete repeat, alternate the two versions and retain result.json.
The script records source file hashes and stripped profiles; source TIFF
staging is excluded from timing. It requires the exact full-mask hash above.
Use the same vc_reader native build and environment for both versions.

Tests from the villa root:
  python -m pytest vesuvius/tests/ink_detection/test_label_plane_chunks.py vesuvius/tests/ink_detection/test_label_zarr_preprocessing.py vesuvius/tests/ink_detection/test_label_pyramid_memory.py -q

Limitations
One full supervision mask measured. Mean/composite and uint16 correctness
are covered on the recorded real-mask crop, not full additional images.
Linux/macOS execution and GPU behavior are not claimed. This is faster
training-data preparation, not a change to model accuracy or recovered text.

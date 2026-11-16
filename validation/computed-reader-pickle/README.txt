Computed-reader serialization validation

A PHerc0800 rendered CT crop is written with ZarrWriter, reopened with
ZarrReader and exposed as float32 normalized computed chunks. The tests
use the native image reader and region reader. No reader or data parser
is reimplemented. The fixture provenance and hashes are in
vc_reader/tests/data/PHerc0800/source.json.

Before, the internal local chunk_bytes function prevents pickle from
serializing even a picklable user callback:7 regression tests fail and1
passes. After using a module-level adapter with functools.partial, all8
pass, including a real spawned multiprocessing worker and a PyTorch
DataLoader. The independent pipeline compares3072 float32 values per read
path. Direct, restored and spawned DataLoader outputs have the same SHA256
as the normalized CT reference; real-data-check.json records the hashes.

Two existing computed-array/writer tests and25 point/source-reader tests
also pass, with23 subtests and1 CUDA skip. Total unique active tests:35.
The local launcher checks source/native hashes and uses a new temporary
session that is removed only after its test subprocesses have terminated.

validation-excerpts.png is a genuine native Notepad capture of the saved
pytest excerpts in the accompanying text file. It is not a live terminal.
Only a rectangular crop is applied; pixels in the crop are unchanged.
The original cursor is outside that rectangle. No paths are displayed.

The current checkout supplies all Python modules; the frozen Windows
native runtime contains the previously proposed shutdown fixes2566/2422
and binding adaptation2533. Its exact provenance and binary hashes are
in validation.json. No native changes or numerical changes are in this PR.
Linux, macOS and CUDA were not run.

PHerc0800 contribution validation

Volume:
https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0800/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr/

Surface:
https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0800/segments/20251029010146-auto_grown_20251029010146642/mesh/20251029010146-on-20250521135224-8.64um.tifxyz/

Ink checkpoint:
https://huggingface.co/scrollprize/ink_9um/blob/main/hybrid_3d2d-seed42/step-075000.pth
SHA256: e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab

ink-empty-pixels.png compares actual prediction TIFFs at the same display
scale. It does not claim improved letter recognition. The input surface
volume has 21 layers at 8.64 micrometres, with the checkpoint selecting 17.
CPU inference used batch size 4, four loader threads and --no-compile.

incomplete-tiff-merge.png compares the old incomplete merge with a complete
two-part render. The corrected behavior with the incomplete input is an
error and unchanged files, not reconstruction of the missing data. The
saved error output and JSON checks accompany the image.

temporary-cache-results.png is a cropped Notepad screenshot of the saved
before/after JSON results. render-dry-run-output.png and
incomplete-tiff-merge-error.png are cropped Notepad screenshots of actual
log excerpts. The underlying text files are included. Cropping removes
application chrome and the computer-use cursor without altering the text.

native-cache-budget.json records two real-volume reads under a shared
3,000,000-byte budget. Each payload is 2,097,152 bytes. The validation also
asserted that the first payload was evicted after reading the second level.

render-dry-run.json compares planned logical source chunks with the cold
cache after each corresponding render. Metadata caching is allowed during
planning. Timings are individual validation runs, not performance claims.

Code commits:
ink-empty-pixels: 3e8d5228600fa26f5a601db0665c005c8315504b
incomplete-tiff-merge: 53ff1f6865f49d77a797289172d3c3fa76f02fb7
ink-native-cache: 05fe04429ca7fced66b1fdeaefc7212387d65d0d
windows-temporary-image-cache: f32486819cb1c71757160aa733d6df60c99502d8
render-dry-run: c14c348e94817a86c654feb664ecd362acf32408

Tests used Windows/UCRT64, GCC 16.1.0 and Python 3.14 on CPU. Local Windows
builds used the scratch shutdown fix from PR #2566; Python bindings also
used the bindings.cpp changes from PR #2533. These adaptations are separate
from the five contribution commits.

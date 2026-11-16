Shipped ink configuration path validation on Windows

The screenshot shows a native Notepad view of saved pytest output excerpts.
It is a log-viewer capture, not a live terminal execution. Application chrome
was cropped away. A black rectangle covers blank cursor-halo space; no test
result text was covered or altered. PNG metadata is empty.

Before: 1 failed and 2 passed in the shipped configuration check.
After: 3 passed and exit 0. The full ink suite reports 419 passed and 9 skipped;
its clean process exit was checked with an isolated native reader containing
existing PR #2422. The original native reader hangs after the same summary.
The frozen reader runtime was preserved. Linux and macOS were not run.

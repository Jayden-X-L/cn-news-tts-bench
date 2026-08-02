# ISCSLP 2026

This directory contains the local double-blind manuscript workspace for ISCSLP 2026.
While the paper is under review, source files, build artifacts, and the uploaded PDF are
kept locally and excluded from the public repository.

The manuscript uses `fontspec` and must be built with XeLaTeX rather than pdfLaTeX:

```bash
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

"""Coarse file-kind detection from filenames.

A dataset's *kind* decides which profiler runs. We keep it deliberately simple
and extension-based so that ingestion never has to read the whole file just to
classify it. Unknown kinds are still stored and fingerprinted — "works with any
data" means we never reject a file, we just profile what we understand.
"""
from __future__ import annotations

from pathlib import Path

# extension -> coarse kind
_EXT = {
    ".csv": "tabular",
    ".tsv": "tabular",
    ".tab": "tabular",
    ".fasta": "fasta",
    ".fa": "fasta",
    ".fna": "fasta",
    ".faa": "fasta",
    ".fastq": "fastq",
    ".fq": "fastq",
    ".vcf": "vcf",
    ".gff": "annotation",
    ".gff3": "annotation",
    ".gtf": "annotation",
    ".bed": "annotation",
    ".sam": "alignment",
    ".bam": "alignment",
    ".cram": "alignment",
    ".json": "json",
}


def _strip_gz(name: str) -> str:
    """Drop a trailing .gz so e.g. reads.fastq.gz classifies as fastq."""
    name = name.lower()
    return name[:-3] if name.endswith(".gz") else name


def detect_kind(filename: str) -> str:
    """Return the coarse kind for a filename, or 'unknown'."""
    ext = Path(_strip_gz(filename)).suffix
    return _EXT.get(ext, "unknown")


def delimiter_for(filename: str) -> str:
    """Best-guess field delimiter for a tabular file."""
    ext = Path(_strip_gz(filename)).suffix
    return "\t" if ext in (".tsv", ".tab") else ","

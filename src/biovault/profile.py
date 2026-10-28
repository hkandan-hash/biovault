"""Profilers: turn a stored file into a structured summary.

Generic tabular profiling (column dtypes, missingness, numeric ranges) plus
light-weight summaries for the bioinformatics formats a research institute sees
constantly: FASTA, FASTQ and VCF. Everything here reads with the standard
library only, so the engine runs anywhere Python does.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from .detect import delimiter_for, detect_kind


def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def profile_tabular(
    path: "str | Path", delimiter: Optional[str] = None, max_rows: Optional[int] = None
) -> dict:
    """Profile a delimited text table: row count and per-column stats."""
    path = Path(path)
    if delimiter is None:
        delimiter = delimiter_for(path.name)

    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return {"rows": 0, "n_columns": 0, "columns": [], "delimiter": delimiter}

        acc = [
            {
                "name": h,
                "n_missing": 0,
                "n_nonempty": 0,
                "n_numeric": 0,
                "n_float": 0,
                "min": None,
                "max": None,
                "sum": 0.0,
            }
            for h in header
        ]

        n_rows = 0
        for row in reader:
            n_rows += 1
            for i, col in enumerate(acc):
                val = row[i].strip() if i < len(row) else ""
                if val == "":
                    col["n_missing"] += 1
                    continue
                col["n_nonempty"] += 1
                if _is_int(val):
                    num: Optional[float] = float(val)
                    col["n_numeric"] += 1
                elif _is_float(val):
                    num = float(val)
                    col["n_numeric"] += 1
                    col["n_float"] += 1
                else:
                    num = None
                if num is not None:
                    col["min"] = num if col["min"] is None else min(col["min"], num)
                    col["max"] = num if col["max"] is None else max(col["max"], num)
                    col["sum"] += num
            if max_rows is not None and n_rows >= max_rows:
                break

    columns = []
    for col in acc:
        numeric = col["n_nonempty"] > 0 and col["n_numeric"] == col["n_nonempty"]
        if col["n_nonempty"] == 0:
            dtype = "empty"
        elif numeric:
            dtype = "float" if col["n_float"] else "integer"
        else:
            dtype = "string"
        summary = {
            "name": col["name"],
            "dtype": dtype,
            "n_nonempty": col["n_nonempty"],
            "n_missing": col["n_missing"],
        }
        if numeric:
            summary["min"] = col["min"]
            summary["max"] = col["max"]
            summary["mean"] = round(col["sum"] / col["n_nonempty"], 6)
        columns.append(summary)

    return {
        "rows": n_rows,
        "n_columns": len(header),
        "columns": columns,
        "delimiter": delimiter,
    }


def summarize_fasta(path: "str | Path") -> dict:
    """Count sequences and residues in a FASTA file."""
    lengths: list[int] = []
    current = 0
    have_seq = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if have_seq:
                    lengths.append(current)
                have_seq = True
                current = 0
            elif line:
                current += len(line)
        if have_seq:
            lengths.append(current)
    return {
        "n_sequences": len(lengths),
        "total_residues": sum(lengths),
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
    }


def summarize_fastq(path: "str | Path") -> dict:
    """Count reads in a FASTQ file (4 lines per read)."""
    n_lines = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for n_lines, _ in enumerate(f, start=1):
            pass
    return {"n_reads": n_lines // 4, "n_lines": n_lines}


def summarize_vcf(path: "str | Path") -> dict:
    """Count variant records and samples in a VCF file."""
    n_variants = 0
    samples: list[str] = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                cols = line.split()
                samples = cols[9:] if len(cols) > 9 else []
                continue
            if line.strip():
                n_variants += 1
    return {"n_variants": n_variants, "n_samples": len(samples), "samples": samples}


def profile_file(path: "str | Path", kind: Optional[str] = None) -> dict:
    """Dispatch to the right profiler based on kind (or detect from name)."""
    path = Path(path)
    kind = kind or detect_kind(path.name)
    if kind == "tabular":
        return {"kind": kind, **profile_tabular(path)}
    if kind == "fasta":
        return {"kind": kind, **summarize_fasta(path)}
    if kind == "fastq":
        return {"kind": kind, **summarize_fastq(path)}
    if kind == "vcf":
        return {"kind": kind, **summarize_vcf(path)}
    # Unknown / binary / not-yet-supported: still report what we can.
    return {"kind": kind, "size_bytes": path.stat().st_size, "profiled": False}

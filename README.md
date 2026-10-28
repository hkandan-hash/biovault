# BioVault

**A bioinformatics research data platform that works with any data.**

BioVault is the data backbone for a bioinformatics research institute: a place to
**register, store, fingerprint, and profile** datasets of *any* type — from
generic CSV/TSV tables to the sequencing formats a lab lives in (FASTA, FASTQ,
VCF). It never rejects a file; it stores and fingerprints everything, and
profiles what it understands.

This repository is **phase 1: the engine** — a tested Python package plus a CLI.
A web API and UI are planned (see [Roadmap](#roadmap)), and the engine is built
to sit underneath them unchanged.

---

## Why

A research organization drowns in files: expression tables, read sets, variant
calls, spreadsheets from collaborators. BioVault gives every dataset a stable
ID, a content fingerprint (so re-imports don't duplicate), typed metadata, and an
instant structured profile — the foundation for search, provenance, pipelines,
and access control later.

## Features (today)

- **Content-addressed registry** — SQLite catalog; every dataset has an id,
  SHA-256, size, kind, timestamp, and arbitrary JSON metadata.
- **Idempotent ingestion** — re-ingesting identical bytes returns the existing
  dataset instead of making a copy.
- **Any data** — unknown formats are still stored and fingerprinted.
- **Profilers**
  - *Tabular* (CSV/TSV): row count, per-column dtype (integer / float / string /
    empty), missing-value counts, and numeric min / max / mean.
  - *FASTA*: sequence count, total residues, min/max length.
  - *FASTQ*: read count.
  - *VCF*: variant count, sample count, sample names.
- **Zero dependencies** — standard library only; runs anywhere Python 3.9+ runs.

## Install

```bash
# from a clone, in a virtual env
pip install -e .
biovault --version
```

Or run straight from source without installing:

```bash
# PowerShell (Windows)
$env:PYTHONPATH = "src"; python -m biovault --version
# bash
PYTHONPATH=src python -m biovault --version
```

## Quickstart

```bash
biovault --home .biovault init
biovault --home .biovault ingest examples/expression.csv --meta project=demo assay=rnaseq
biovault --home .biovault ingest examples/demo.fasta
biovault --home .biovault ingest examples/demo.vcf
biovault --home .biovault list
biovault --home .biovault profile <dataset-id>
```

Example profile output for `examples/expression.csv`:

```json
{
  "kind": "tabular",
  "rows": 5,
  "n_columns": 4,
  "columns": [
    {"name": "expression", "dtype": "float", "n_nonempty": 4, "n_missing": 1,
     "min": 8.9, "max": 22.0, "mean": 14.6}
  ]
}
```

A **workspace** holds the registry and stored files. It defaults to
`~/.biovault`, or set `$BIOVAULT_HOME`, or pass `--home <dir>`.

## Architecture

```
src/biovault/
  detect.py     filename -> coarse kind (tabular / fasta / fastq / vcf / ...)
  registry.py   SQLite catalog of datasets (the source of truth)
  ingest.py     fingerprint + copy into the content store + register
  profile.py    tabular profiler + FASTA/FASTQ/VCF summaries
  cli.py        `biovault` command (init / ingest / list / show / profile)
```

The CLI is intentionally thin. The same `Registry`, `ingest_file`, and
`profile_file` functions are what a future web API will call.

## Testing

Standard-library `unittest`, no extra tooling required:

```bash
# PowerShell
python -m unittest discover -s tests -v
# bash
python -m unittest discover -s tests -v
```

## Roadmap

- **Phase 1 (this repo):** engine — registry, ingestion, profiling, CLI. ✅
- **Phase 2:** FastAPI service + upload endpoint over the same engine.
- **Phase 3:** web UI — dataset browser, profile dashboards, metadata editing.
- **Phase 4:** users, projects, and access control (toward multi-tenant org use).
- **Phase 5:** pipeline runs (QC, alignment, differential analysis) with provenance.
- **Later:** clinical/phenotype data with de-identification and compliance controls.

## Notes

Built with the Claude Code **Agent Network v2** kit (26 specialist agents +
workflows available globally in this environment). This is research tooling, not
a clinical device; it is not validated for diagnostic use.

## License

MIT.

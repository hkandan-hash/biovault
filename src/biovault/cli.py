"""BioVault command-line interface.

A thin front door over the engine. A workspace (``~/.biovault`` by default, or
``$BIOVAULT_HOME``, or ``--home``) holds the SQLite registry and the content
store.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .ingest import ingest_file
from .profile import profile_file
from .registry import Registry


def _workspace(args: argparse.Namespace) -> Path:
    return Path(
        args.home or os.environ.get("BIOVAULT_HOME") or (Path.home() / ".biovault")
    )


def _open(args: argparse.Namespace) -> "tuple[Registry, Path]":
    home = _workspace(args)
    home.mkdir(parents=True, exist_ok=True)
    return Registry(home / "registry.db"), home / "store"


def cmd_init(args: argparse.Namespace) -> int:
    home = _workspace(args)
    home.mkdir(parents=True, exist_ok=True)
    Registry(home / "registry.db").close()
    (home / "store").mkdir(exist_ok=True)
    print(f"Initialized BioVault workspace at {home}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    reg, store = _open(args)
    try:
        meta: dict = {}
        for kv in args.meta or []:
            if "=" not in kv:
                print(f"ignoring bad --meta '{kv}' (expected key=value)", file=sys.stderr)
                continue
            k, v = kv.split("=", 1)
            meta[k] = v
        ds = ingest_file(reg, args.path, store, name=args.name, metadata=meta)
    finally:
        reg.close()
    print(f"{ds.id}\t{ds.kind}\t{ds.name}\t{ds.size_bytes} bytes\tsha256={ds.sha256[:12]}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    reg, _ = _open(args)
    try:
        rows = reg.list(kind=args.kind)
    finally:
        reg.close()
    if not rows:
        print("(no datasets)")
        return 0
    print(f"{'ID':12}  {'KIND':10}  {'SIZE':>12}  NAME")
    for d in rows:
        print(f"{d.id:12}  {d.kind:10}  {d.size_bytes:>12}  {d.name}")
    print(f"\n{len(rows)} dataset(s)")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    reg, _ = _open(args)
    try:
        d = reg.get(args.id)
    finally:
        reg.close()
    if d is None:
        print(f"not found: {args.id}", file=sys.stderr)
        return 1
    print(json.dumps(d.__dict__, indent=2, default=str))
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    reg, _ = _open(args)
    try:
        d = reg.get(args.id)
    finally:
        reg.close()
    if d is None:
        print(f"not found: {args.id}", file=sys.stderr)
        return 1
    print(json.dumps(profile_file(d.stored_path, kind=d.kind), indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="biovault",
        description="BioVault — a bioinformatics research data platform that works with any data.",
    )
    p.add_argument("--version", action="version", version=f"biovault {__version__}")
    p.add_argument("--home", help="workspace dir (default: $BIOVAULT_HOME or ~/.biovault)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="create an empty workspace")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("ingest", help="register and store a file")
    sp.add_argument("path", help="file to ingest")
    sp.add_argument("--name", help="human-friendly name (default: filename)")
    sp.add_argument("--meta", nargs="*", metavar="KEY=VALUE", help="metadata key=value pairs")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("list", help="list datasets")
    sp.add_argument("--kind", help="filter by kind (tabular, fasta, fastq, vcf, ...)")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("show", help="show one dataset's record")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("profile", help="profile one dataset's contents")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_profile)

    return p


def main(argv: "list[str] | None" = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

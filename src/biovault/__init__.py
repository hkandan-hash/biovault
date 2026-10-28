"""BioVault — a bioinformatics research data platform that works with any data.

The core engine: register datasets of any type, store them with a content
fingerprint, and profile them (generic tabular + FASTA/FASTQ/VCF).
"""

__version__ = "0.1.0"

from .registry import Registry, Dataset
from .ingest import ingest_file, sha256_of
from .profile import profile_file
from .detect import detect_kind

__all__ = [
    "__version__",
    "Registry",
    "Dataset",
    "ingest_file",
    "sha256_of",
    "profile_file",
    "detect_kind",
]

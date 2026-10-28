import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401

from biovault.profile import (
    profile_file,
    profile_tabular,
    summarize_fasta,
    summarize_fastq,
    summarize_vcf,
)


class TestTabular(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name) / "d.csv"
        self.p.write_text(
            "sample_id,gene,expression,condition\n"
            "S1,BRCA1,12.4,control\n"
            "S2,BRCA1,15.1,treated\n"
            "S3,TP53,8.9,control\n"
            "S4,TP53,,treated\n"
            "S5,EGFR,22.0,treated\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_shape(self):
        prof = profile_tabular(self.p)
        self.assertEqual(prof["rows"], 5)
        self.assertEqual(prof["n_columns"], 4)

    def test_column_types_and_missing(self):
        prof = profile_tabular(self.p)
        cols = {c["name"]: c for c in prof["columns"]}
        self.assertEqual(cols["gene"]["dtype"], "string")
        self.assertEqual(cols["expression"]["dtype"], "float")
        self.assertEqual(cols["expression"]["n_missing"], 1)
        self.assertEqual(cols["expression"]["n_nonempty"], 4)

    def test_numeric_stats(self):
        cols = {c["name"]: c for c in profile_tabular(self.p)["columns"]}
        expr = cols["expression"]
        self.assertAlmostEqual(expr["min"], 8.9)
        self.assertAlmostEqual(expr["max"], 22.0)
        self.assertAlmostEqual(expr["mean"], 14.6)  # (12.4+15.1+8.9+22.0)/4

    def test_empty_file(self):
        p = Path(self.tmp.name) / "empty.csv"
        p.write_text("", encoding="utf-8")
        prof = profile_tabular(p)
        self.assertEqual(prof["rows"], 0)
        self.assertEqual(prof["columns"], [])


class TestBioFormats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fasta(self):
        p = self.dir / "g.fasta"
        p.write_text(">seq1 desc\nACGTACGTAC\nGGGG\n>seq2\nACGT\n", encoding="utf-8")
        s = summarize_fasta(p)
        self.assertEqual(s["n_sequences"], 2)
        self.assertEqual(s["total_residues"], 18)
        self.assertEqual(s["min_length"], 4)
        self.assertEqual(s["max_length"], 14)

    def test_fastq(self):
        p = self.dir / "r.fastq"
        p.write_text(
            "@r1\nACGT\n+\nIIII\n@r2\nTTTT\n+\nIIII\n", encoding="utf-8"
        )
        s = summarize_fastq(p)
        self.assertEqual(s["n_reads"], 2)

    def test_vcf(self):
        p = self.dir / "v.vcf"
        p.write_text(
            "##fileformat=VCFv4.2\n"
            "#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT S1 S2\n"
            "1 100 . A T 50 PASS . GT 0/1 1/1\n"
            "1 200 . G C 60 PASS . GT 0/0 0/1\n",
            encoding="utf-8",
        )
        s = summarize_vcf(p)
        self.assertEqual(s["n_variants"], 2)
        self.assertEqual(s["n_samples"], 2)
        self.assertEqual(s["samples"], ["S1", "S2"])

    def test_dispatch_unknown(self):
        p = self.dir / "mystery.xyz"
        p.write_text("whatever", encoding="utf-8")
        prof = profile_file(p)
        self.assertEqual(prof["kind"], "unknown")
        self.assertFalse(prof["profiled"])


if __name__ == "__main__":
    unittest.main()

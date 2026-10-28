import unittest

import _path  # noqa: F401  (sets up sys.path)

from biovault.detect import delimiter_for, detect_kind


class TestDetect(unittest.TestCase):
    def test_known_extensions(self):
        self.assertEqual(detect_kind("a.csv"), "tabular")
        self.assertEqual(detect_kind("a.tsv"), "tabular")
        self.assertEqual(detect_kind("genome.fasta"), "fasta")
        self.assertEqual(detect_kind("reads.fq"), "fastq")
        self.assertEqual(detect_kind("variants.vcf"), "vcf")
        self.assertEqual(detect_kind("ann.gff3"), "annotation")

    def test_gz_is_stripped(self):
        self.assertEqual(detect_kind("reads.fastq.gz"), "fastq")
        self.assertEqual(detect_kind("variants.vcf.gz"), "vcf")

    def test_unknown(self):
        self.assertEqual(detect_kind("mystery.xyz"), "unknown")
        self.assertEqual(detect_kind("no_extension"), "unknown")

    def test_delimiter(self):
        self.assertEqual(delimiter_for("a.csv"), ",")
        self.assertEqual(delimiter_for("a.tsv"), "\t")
        self.assertEqual(delimiter_for("a.tab"), "\t")


if __name__ == "__main__":
    unittest.main()

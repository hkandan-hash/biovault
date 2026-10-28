import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401

from biovault.ingest import ingest_file, sha256_of
from biovault.registry import Registry


class TestRegistryIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.reg = Registry(self.dir / "registry.db")
        self.store = self.dir / "store"
        self.sample = self.dir / "sample.csv"
        self.sample.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    def tearDown(self):
        self.reg.close()
        self.tmp.cleanup()

    def test_ingest_registers_and_copies(self):
        ds = ingest_file(self.reg, self.sample, self.store, metadata={"project": "demo"})
        self.assertEqual(ds.kind, "tabular")
        self.assertEqual(ds.metadata["project"], "demo")
        self.assertTrue(Path(ds.stored_path).is_file())
        self.assertEqual(ds.sha256, sha256_of(self.sample))
        self.assertEqual(self.reg.count(), 1)

    def test_get_and_list(self):
        ds = ingest_file(self.reg, self.sample, self.store)
        self.assertEqual(self.reg.get(ds.id).id, ds.id)
        self.assertEqual(len(self.reg.list()), 1)
        self.assertEqual(len(self.reg.list(kind="tabular")), 1)
        self.assertEqual(len(self.reg.list(kind="fasta")), 0)

    def test_dedup_by_content(self):
        a = ingest_file(self.reg, self.sample, self.store)
        b = ingest_file(self.reg, self.sample, self.store)  # same bytes
        self.assertEqual(a.id, b.id)
        self.assertEqual(self.reg.count(), 1)

    def test_delete(self):
        ds = ingest_file(self.reg, self.sample, self.store)
        self.assertTrue(self.reg.delete(ds.id))
        self.assertIsNone(self.reg.get(ds.id))
        self.assertFalse(self.reg.delete(ds.id))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            ingest_file(self.reg, self.dir / "nope.csv", self.store)


if __name__ == "__main__":
    unittest.main()

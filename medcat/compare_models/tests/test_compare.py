import unittest.mock
from compare import _add_all_children
from compare import get_diffs_for
from compare import (CDBCompareResults, ResultsTally,
                     ResultsTally, PerAnnotationDifferences)
import unittest
import os

from medcat.cat import CAT


class FakeCDBWithPt2Ch:

    def __init__(self, pt2ch: dict) -> None:
        self.pt2ch = pt2ch
        self.addl_info = {"pt2ch": self.pt2ch}


class FakeCATWithCDBAndPt2Ch:

    def __init__(self, pt2ch: dict) -> None:
        self.cdb = FakeCDBWithPt2Ch(pt2ch)


_PT2CH = {
        "C1": ["C11", "C12", "C13"],
        "C2": ["C21"],
        # grandchildren
        "C11": ["C111", "C112", "C113"],
        "C13": ["C131", "C132"],
        # great grandchildren
        "C132": ["C1321", "C1322"],
    }


class AddAllChildrenTests(unittest.TestCase):
    pt2ch = _PT2CH
    fake_cat = FakeCATWithCDBAndPt2Ch(pt2ch)

    _cui_filter = set(['C1', 'C2'])
    a = [c for c in pt2ch.get("", [])]
    children_1st_order = set(ch for cui in _cui_filter for ch in _PT2CH.get(cui, []))
    children_2nd_order = set(gch for ch in children_1st_order for gch in _PT2CH.get(ch, []))

    @property
    def cui_filter(self) -> set:
        return set(self._cui_filter)

    def test_adds_no_children_with_0(self):
        f = self.cui_filter  # copy
        _add_all_children(self.fake_cat, f, include_children=0)
        self.assertEqual(f, self.cui_filter)

    def test_add_first_children_with_1(self):
        f = self.cui_filter
        _add_all_children(self.fake_cat, f, include_children=1)
        self.assertGreater(f, self.cui_filter)
        self.assertEqual(f, self.cui_filter | self.children_1st_order)
        # no grandchildren
        self.assertFalse(f & self.children_2nd_order)

    def test_add_grandchildren_with_2(self):
        f = self.cui_filter
        _add_all_children(self.fake_cat, f, include_children=2)
        self.assertGreater(f, self.cui_filter)
        self.assertGreater(f, self.cui_filter | self.children_1st_order)
        self.assertEqual(f, self.cui_filter | self.children_1st_order | self.children_2nd_order)


class TrainAndCompareTests(unittest.TestCase):
    _file_dir = os.path.dirname(__file__)
    _resources_path = os.path.join(_file_dir, "resources")
    cat_path = os.path.join(_resources_path, "model_pack")
    mct_export_path_1 = os.path.join(_resources_path, "mct_export", "medcat_trainer_export.json")
    mct_export_path_glob = os.path.join(_resources_path, "mct_export", "medcat_trainer_export*.json")
    docs_file = os.path.join(_resources_path, "docs", "not_real.csv")

    # this tests that the training is called
    @classmethod
    @unittest.mock.patch("medcat.trainer.Trainer.train_supervised_raw")
    def _get_diffs(cls, mct_export_path: str, method):
        diffs = get_diffs_for(cls.cat_path, mct_export_path, cls.docs_file,
                              supervised_train_comparison_model=True)
        cls.assertTrue(cls, method.called)
        return diffs


    @classmethod
    def setUpClass(cls) -> None:
        ann_diffs1 = cls._get_diffs(cls.mct_export_path_1)
        cls.cdb_comp1, cls.tally1_1, cls.tally1_2, cls.ann_diffs1 = ann_diffs1
        ann_diffs_many = cls._get_diffs(cls.mct_export_path_glob)
        cls.cdb_comp_many, cls.tally_many_1, cls.tally_many_2, cls.ann_diffs_many = ann_diffs_many

    def test_compares_with_one_file(self):
        self.assertIsInstance(self.cdb_comp1, CDBCompareResults)
        self.assertIsInstance(self.tally1_1, ResultsTally)
        self.assertIsInstance(self.tally1_2, ResultsTally)
        self.assertIsInstance(self.ann_diffs1, PerAnnotationDifferences)

    def test_compares_with_multiple_file(self):
        self.assertIsInstance(self.cdb_comp_many, CDBCompareResults)
        self.assertIsInstance(self.tally_many_1, ResultsTally)
        self.assertIsInstance(self.tally_many_2, ResultsTally)
        self.assertIsInstance(self.ann_diffs_many, PerAnnotationDifferences)

from compare import _add_all_children
import unittest


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


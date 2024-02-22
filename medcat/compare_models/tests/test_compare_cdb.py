import compare_cdb

import unittest
EXAMPLE1 = {
        "C0": {"n01", "n02", "n03"}, # 1 non-unique (#2 CS)
        "C1": {"n11", "n12"       },

        "C3": {"n31",        "n33"}, # adds 1 CUI, 2 names

        "C5": {              "n53"}, # adds 1 CUI, 1 name
    }
EXAMPLE2 = {
        "C0": {"n01", "n02", "n03"}, # 1 non-unique (CS)
        "C1": {"n11", "n12", "n13"}, # adds 1 name
        "C2": {"n21",        "n23"}, # adds 1 CUI, 2 names

        "C4": {"n41", "n42", "n43"}, # adds 1 CUI, 3 names; 1 non-unique (CS)

        "CS": {"n01", "n42",      }, # adds 1 CUI, no names
    }
# this should be equivalent to the above
EXPECTED_VALUES_MAN = compare_cdb.DictCompareValues(total1=8,
                                                    total2=13,
                                                    not_in_1=8,     # n13, n21, n23, n41, n42, n43, "n01", "n42"
                                                    not_in_2=3,     # n31, n33, n53
                                                    joint=5,        # n01, n02, n03, n11, n12
                                                    unique_in_1=3,  # overall unique in 1st
                                                    unique_in_2=6,  # overall unique in 2nd
                                                    )

keys1 = set(EXAMPLE1.keys())
keys2 = set(EXAMPLE2.keys())
EXPECTED_KEYS = compare_cdb.DictCompareKeys(total1=len(keys1),
                                            total2=len(keys2),
                                            joint=len(keys1 & keys2),
                                            not_in_1=(len(keys1 | keys2)) - len(keys1),
                                            not_in_2=(len(keys1 | keys2)) - len(keys2),)
# this should be equivalent to the above
EXPECTED_KEYS_MAN = compare_cdb.DictCompareKeys(total1=4,    # C0, C1, C3, C5
                                                total2=5,    # C0, C1, C2, C4, CS
                                                joint=2,     # C0, C1
                                                not_in_1=3,  # C2, C4, CS
                                                not_in_2=2,  # C3, C5
                                                )
vals1 = set(e for v in EXAMPLE1.values() for e in v)
total1 = sum(len(v) for v in EXAMPLE1.values())
vals2 = set(e for v in EXAMPLE2.values() for e in v)
total2 = sum(len(v) for v in EXAMPLE2.values())
EXPECTED_VALUES = compare_cdb.DictCompareValues(total1=total1,
                                                total2=total2,
                                                not_in_1=8,  # the new/misplaced CUIs in 2nd
                                                not_in_2=3,  # the new/misplaced CUIs in 1st
                                                joint=len(vals1 & vals2),
                                                unique_in_1=3,  # overall unique in 1st
                                                unique_in_2=6,  # overall unique in 2nd
                                                )


class CompareDictTests(unittest.TestCase):

    def test_compare_keys_works(self, d1=EXAMPLE1, d2=EXAMPLE2, exp=EXPECTED_KEYS, exp_man=EXPECTED_KEYS_MAN):
        res = compare_cdb.DictCompareKeys.get(d1, d2)
        self.assertEqual(res.dict(), exp.dict())
        self.assertEqual(res.dict(), exp_man.dict())

    def test_compare_values_works(self, d1=EXAMPLE1, d2=EXAMPLE2, exp=EXPECTED_VALUES, exp_man=EXPECTED_VALUES_MAN):
        res = compare_cdb.DictCompareValues.get(d1, d2, progress=False)
        self.assertEqual(res.dict(), exp.dict())
        self.assertEqual(res.dict(), exp_man.dict())


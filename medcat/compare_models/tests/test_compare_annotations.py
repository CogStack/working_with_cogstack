import compare_annotations

import unittest


class ResultsTallyTests(unittest.TestCase):
    common = {"type_ids": ["T1"], "detected_name": "NOT IMPORTANT", 'acc': 1.0}
    cui2name = {"C1": "Concept 1",
                "C2": "Concept 2"}
    entities = [ {"entities":
                   {"0": {"start": 10, "end": 15, "cui": "C1"},
                    "1": {"start": 20, "end": 35, "cui": "C2"}}},
                  {"entities":
                   {"0": {"start": 5, "end": 15, "cui": "C2"},
                    "1": {"start": 25, "end": 30, "cui": "C1"}}}
                ]

    @classmethod
    def setUpClass(cls) -> None:
        for doc in cls.entities:
            for ent in doc['entities'].values():
                ent.update(cls.common)

    def _cui2name(self, cui: str) -> str:
        return self.cui2name[cui]

    def setUp(self) -> None:
        self.res = compare_annotations.ResultsTally(cat_data={"stats": "don't matter"},
                                               cui2name=self._cui2name)
        for entities in self.entities:
            self.res.count(entities)

    def test_filter_works(self, cuis = {"C1"}):
        self.res.filter_cuis(cuis)
        for cui in cuis:
            with self.subTest(cui):
                self.assertIn(cui, self.res.per_cui_count)
        for cui in self.cui2name:
            if cui in cuis:
                continue
            with self.subTest(cui):
                per_cui = self.res.get_for_cui(cui)
                per_cui_values = set(per_cui.values())
                self.assertEqual(len(per_cui_values), len(self.cui2name) - 1)
                self.assertEqual(per_cui_values, {"N/A"})
        self.assertEqual(set(self.res.per_cui_count), cuis)


class EntityOverlapIdenticalTests(unittest.TestCase):

    def test_identical_overlap(self, start=10, end=15):
        self.assertTrue(compare_annotations._check_overlap_internal(start, end, start, end))

class EntityOverlapFarAwayTests(unittest.TestCase):
    start1 = 10
    end1 = 15
    one = (start1, end1)
    start2 = 20
    end2 = 25
    two = (start2, end2)

    def test_no_overlap_12(self):
        self.assertFalse(compare_annotations._check_overlap_internal(*self.one, *self.two))

    def test_no_overlap_21(self):
        self.assertFalse(compare_annotations._check_overlap_internal(*self.two, *self.one))


class PartialOverlapTests(unittest.TestCase):
    start1 = 10
    end1 = 20
    one = (start1, end1)
    start2 = 15
    end2 = 25
    two = (start2, end2)

    def test_12(self):
        self.assertTrue(compare_annotations._check_overlap_internal(*self.one, *self.two))

    def test_21(self):
        self.assertTrue(compare_annotations._check_overlap_internal(*self.two, *self.one))


class IdenticalStartOverlapTests(unittest.TestCase):
    start = 10
    end1 = 20
    end2 = 25
    one = (start, end1)
    two = (start, end2)
    
    def test_12(self):
        self.assertTrue(compare_annotations._check_overlap_internal(*self.one, *self.two))

    def test_21(self):
        self.assertTrue(compare_annotations._check_overlap_internal(*self.two, *self.one))


class IdenticalEndOverlapTests(unittest.TestCase):
    start1 = 10
    start2 = 5
    end = 20
    one = (start1, end)
    two = (start2, end)
    
    def test_12(self):
        self.assertTrue(compare_annotations._check_overlap_internal(*self.one, *self.two))

    def test_21(self):
        self.assertTrue(compare_annotations._check_overlap_internal(*self.two, *self.one))


# START the annotation comparison


class NoOverlapFarAwaySameCUITests(unittest.TestCase):
    FIRST = compare_annotations.AnnotationComparisonType.FIRST_HAS
    SECOND = compare_annotations.AnnotationComparisonType.SECOND_HAS
    d1 = {"start": 10, "end": 15, "cui": 'C1'}
    d2 = {"start": 20, "end": 25, "cui": 'C1'}

    def setUp(self) -> None:
        self.c12 = compare_annotations.AnnotationComparisonType.determine(self.d1, self.d2,
                                                                          pt2ch1=None, pt2ch2=None)
        self.c21 = compare_annotations.AnnotationComparisonType.determine(self.d2, self.d1,
                                                                          pt2ch1=None, pt2ch2=None)

    def test_1st_has_12(self):
        self.assertIs(self.c12, self.FIRST)

    def test_2nd_has_21(self):
        self.assertIs(self.c21, self.SECOND)


class NoOverlapFarAwayDiffCUITests(NoOverlapFarAwaySameCUITests):

    @classmethod
    def setUpClass(cls) -> None:
        cls.d1 = dict(cls.d1, cui='C2')
        cls.d2 = dict(cls.d2, cui='C3')


class PartialOverlapSameCUITests(unittest.TestCase):
    DIFF_CONCEPT = compare_annotations.AnnotationComparisonType.PARTIAL_OVERLAP_DIFF_CONCEPT
    SAME_CONCEPT = compare_annotations.AnnotationComparisonType.PARTIAL_OVERLAP_SAME_CONCEPT
    d1 = {"start": 10, "end": 20, "cui": 'C1'}
    d2 = {"start": 15, "end": 25, "cui": 'C1'}
    expect_identical_cui = True

    def setUp(self) -> None:
        self.c12 = compare_annotations.AnnotationComparisonType.determine(self.d1, self.d2,
                                                                          pt2ch1=None, pt2ch2=None)
        self.c21 = compare_annotations.AnnotationComparisonType.determine(self.d2, self.d1,
                                                                          pt2ch1=None, pt2ch2=None)
        self.expected = self.SAME_CONCEPT if self.expect_identical_cui else self.DIFF_CONCEPT

    def test_partial_12(self):
        self.assertIs(self.c12, self.expected)

    def test_partial_21(self):
        self.assertIs(self.c21, self.expected)


class PartialOverlapDiffCUITests(PartialOverlapSameCUITests):

    @classmethod
    def setUpClass(cls) -> None:
        cls.d1 = dict(cls.d1, cui='C2')
        cls.d2 = dict(cls.d2, cui='C3')
        cls.expect_identical_cui = False


class IdenticalOverlapSameCUITests(unittest.TestCase):
    SAME = compare_annotations.AnnotationComparisonType.IDENTICAL
    DIFF = compare_annotations.AnnotationComparisonType.SAME_SPAN_DIFF_CONCEPT
    d1 = {"start": 10, "end": 20, "cui": 'C1'}
    d2 = {"start": 10, "end": 20, "cui": 'C1'}
    expect_identical_cui = True

    def setUp(self) -> None:
        self.c12 = compare_annotations.AnnotationComparisonType.determine(self.d1, self.d2,
                                                                          pt2ch1=None, pt2ch2=None)
        self.c21 = compare_annotations.AnnotationComparisonType.determine(self.d2, self.d1,
                                                                          pt2ch1=None, pt2ch2=None)
        self.expected = self.SAME if self.expect_identical_cui else self.DIFF
    
    def test_identical_12(self):
        self.assertIs(self.c12, self.expected)

    def test_identical_21(self):
        self.assertIs(self.c21, self.expected)


class IdenticalOverlapDiffCUITests(IdenticalOverlapSameCUITests):

    @classmethod
    def setUpClass(cls) -> None:
        cls.d1 = dict(cls.d1, cui='C2')
        cls.d2 = dict(cls.d2, cui='C3')
        cls.expect_identical_cui = False
        

class OverLapOneLargerSameConceptTests(unittest.TestCase):
    L1_DC = compare_annotations.AnnotationComparisonType.OVERLAPP_1ST_LARGER_DIFF_CONCEPT
    L2_DC = compare_annotations.AnnotationComparisonType.OVERLAPP_2ND_LARGER_DIFF_CONCEPT
    L1_SC = compare_annotations.AnnotationComparisonType.OVERLAPP_1ST_LARGER_SAME_CONCEPT
    L2_SC = compare_annotations.AnnotationComparisonType.OVERLAPP_2ND_LARGER_SAME_CONCEPT
    d1 = {"start": 10, "end": 25, "cui": 'C1'}
    d2 = {"start": 10, "end": 20, "cui": 'C1'}
    expect_identical_cui = True

    def setUp(self) -> None:
        self.c12 = compare_annotations.AnnotationComparisonType.determine(self.d1, self.d2,
                                                                          pt2ch1=None, pt2ch2=None)
        self.c21 = compare_annotations.AnnotationComparisonType.determine(self.d2, self.d1,
                                                                          pt2ch1=None, pt2ch2=None)
        self.expected_12 = self.L1_SC if self.expect_identical_cui else self.L1_DC
        self.expected_21 = self.L2_SC if self.expect_identical_cui else self.L2_DC

    def test_12(self):
        self.assertTrue(self.c12, self.expected_12)

    def test_21(self):
        self.assertTrue(self.c12, self.expected_21)


class OverLapOneLargerDiffConceptTests(OverLapOneLargerSameConceptTests):

    @classmethod
    def setUpClass(cls) -> None:
        cls.d1 = dict(cls.d1, cui='C2')
        cls.d2 = dict(cls.d2, cui='C3')
        cls.expect_identical_cui = False


# per document tests


class PerDocAnnotationSameTests(unittest.TestCase):
    entities = {"0": {"start": 10, "end": 25, "cui": 'C1'},
                "1": {"start": 40, "end": 55, "cui": 'C2'}}
    d = {"entities": entities}
    d1 = d
    d2 = d
    expected = compare_annotations.AnnotationComparisonType.IDENTICAL

    def test_all_same(self):
        pdad = compare_annotations.PerDocAnnotationDifferences.get(self.d1, self.d2,
                                                                   pt2ch1=None, pt2ch2=None)
        self.assertEqual(len(pdad.nr_of_comparisons), 1)
        for el in compare_annotations.AnnotationComparisonType:
            with self.subTest(f"{el}"):
                if el is self.expected:
                    self.assertIn(self.expected, pdad.nr_of_comparisons)
                else:
                    self.assertNotIn(el, pdad.nr_of_comparisons)

class PerDocAnnotationSameSpanDiffCUITests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.entities2 = {k0: {k1: v1 if k1 != "cui" else f"{v1}0" for k1, v1 in v0.items()}
                 for k0, v0 in cls.entities.items()}
        cls.d2 = {"entities": cls.entities2}
        cls.expected = compare_annotations.AnnotationComparisonType.SAME_SPAN_DIFF_CONCEPT


class PerDocAnnotationLargerSpan2ndSameCUITests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.entities2 = {k0: {k1: v1 if k1 != "end" else v1 + 10 for k1, v1 in v0.items()}
                 for k0, v0 in cls.entities.items()}
        cls.d2 = {"entities": cls.entities2}
        cls.expected = compare_annotations.AnnotationComparisonType.OVERLAPP_2ND_LARGER_SAME_CONCEPT


class PerDocAnnotationLargerSpan2ndDiffCUITests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.entities2 = {k0: {k1: v1 if k1 != "end" else v1 + 10 for k1, v1 in v0.items()}
                 for k0, v0 in cls.entities.items()}
        # change cuis
        for ent in cls.entities2.values():
            ent['cui'] += "C"
        cls.d2 = {"entities": cls.entities2}
        cls.expected = compare_annotations.AnnotationComparisonType.OVERLAPP_2ND_LARGER_DIFF_CONCEPT


class PerDocAnnotationLargerSpan1stSameCUITests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.entities2 = {k0: {k1: v1 if k1 != "end" else v1 - 2 for k1, v1 in v0.items()}
                 for k0, v0 in cls.entities.items()}
        cls.d2 = {"entities": cls.entities2}
        cls.expected = compare_annotations.AnnotationComparisonType.OVERLAPP_1ST_LARGER_SAME_CONCEPT


class PerDocAnnotationLargerSpan1stDiffCUITests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.entities2 = {k0: {k1: v1 if k1 != "end" else v1 - 2 for k1, v1 in v0.items()}
                 for k0, v0 in cls.entities.items()}
        # change cuis
        for ent in cls.entities2.values():
            ent['cui'] += "C"
        cls.d2 = {"entities": cls.entities2}
        cls.expected = compare_annotations.AnnotationComparisonType.OVERLAPP_1ST_LARGER_DIFF_CONCEPT


class PerDocAnnotatingUneventLengthsAll1stTests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        # empty d2
        cls.d2 = {"entities": {}}
        cls.expected = compare_annotations.AnnotationComparisonType.FIRST_HAS


class PerDocAnnotatingUneventLengthsAll2ndTests(PerDocAnnotationSameTests):

    @classmethod
    def setUpClass(cls) -> None:
        # empty d2
        cls.d1, cls.d2 = {"entities": {}}, cls.d1
        cls.expected = compare_annotations.AnnotationComparisonType.SECOND_HAS


class PerDocAnnotatingUnevenLengthsComplicatedTests(unittest.TestCase):
    entities1 = {"0": {"start": 10, "end": 25, "cui": 'C1'},
                 "1": {"start": 40, "end": 55, "cui": 'C2'}}
    d1 = {"entities": entities1}
    entities2 = dict(entities1,
                     **{"2": {"start": 50, "end": 60, "cui": 'C3'},
                        "3": {"start": 65, "end": 70, "cui": 'C2'}})
    d2 = {"entities": entities2}
    expected12 = {compare_annotations.AnnotationComparisonType.IDENTICAL: 2,
                  compare_annotations.AnnotationComparisonType.SECOND_HAS: 2}
    expected21 = {compare_annotations.AnnotationComparisonType.IDENTICAL: 2,
                  compare_annotations.AnnotationComparisonType.FIRST_HAS: 2}

    def test_has_expected_comparison_12(self):
        pdad = compare_annotations.PerDocAnnotationDifferences.get(self.d1, self.d2,
                                                                   pt2ch1=None, pt2ch2=None)
        self.assertEqual(pdad.nr_of_comparisons, self.expected12)

    def test_has_expected_comparison_21(self):
        pdad = compare_annotations.PerDocAnnotationDifferences.get(self.d2, self.d1,
                                                                   pt2ch1=None, pt2ch2=None)
        self.assertEqual(pdad.nr_of_comparisons, self.expected21)


# now for PerAnnotationDifferences


class PerAnnotationSameDifferencesIdenticalTests(unittest.TestCase):
    annotations = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'C1'},
            "1": {"start": 40, "end": 55, "cui": 'C2'}
                }},
        # doc2
        {"entities": {
            "0": {"start": 12, "end": 22, "cui": 'C1'},
            "1": {"start": 42, "end": 52, "cui": 'C2'}
                }},
    ]
    expected_totals = {compare_annotations.AnnotationComparisonType.IDENTICAL: 4}

    def setUp(self):
        self.pad = compare_annotations.PerAnnotationDifferences(pt2ch1=None, pt2ch2=None)
        for nr, ann in enumerate(self.annotations):
            self.pad.look_at_doc(ann, ann, f"{nr}")
        self.pad.finalise()

    def test_identical(self):
        self.assertEqual(self.pad.totals, self.expected_totals)


class PerAnnotationSomeDifferencesIdenticalTests(unittest.TestCase):
    annotations1 = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'C1'},
            "1": {"start": 40, "end": 55, "cui": 'C2'}
                }},
        # doc2
        {"entities": {
            "0": {"start": 12, "end": 22, "cui": 'C1'},
            "1": {"start": 42, "end": 52, "cui": 'C2'}
                }},
    ]
    annotations2 = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'C1'},
            "1": {"start": 40, "end": 55, "cui": 'C2'}
                }},
        # doc2
        {"entities": {
            "0": {"start": 80, "end": 88, "cui": 'C3'},
        }},
    ]
    expected_totals = {compare_annotations.AnnotationComparisonType.IDENTICAL: 2,
                       compare_annotations.AnnotationComparisonType.FIRST_HAS: 2,
                       compare_annotations.AnnotationComparisonType.SECOND_HAS: 1,
                       }
    expected_pair_order = [
        ("0", compare_annotations.AnnotationPair(one=annotations1[0]['entities']['0'],
                                                 two=annotations2[0]['entities']['0'],
                                                 comparison_type=compare_annotations.AnnotationComparisonType.IDENTICAL)),
        ("0", compare_annotations.AnnotationPair(one=annotations1[0]['entities']['1'],
                                                 two=annotations2[0]['entities']['1'],
                                                 comparison_type=compare_annotations.AnnotationComparisonType.IDENTICAL)),
        ("1", compare_annotations.AnnotationPair(one=annotations1[1]['entities']['0'],
                                                 two=None,
                                                 comparison_type=compare_annotations.AnnotationComparisonType.FIRST_HAS)),
        ("1", compare_annotations.AnnotationPair(one=annotations1[1]['entities']['1'],
                                                 two=None,
                                                 comparison_type=compare_annotations.AnnotationComparisonType.FIRST_HAS)),
        ("1", compare_annotations.AnnotationPair(one=None,
                                                 two=annotations2[1]['entities']['0'],
                                                 comparison_type=compare_annotations.AnnotationComparisonType.SECOND_HAS)),
    ]

    def setUp(self):
        self.pad = compare_annotations.PerAnnotationDifferences(pt2ch1=None, pt2ch2=None)
        for nr, (ann1, ann2) in enumerate(zip(self.annotations1, self.annotations2)):
            self.pad.look_at_doc(ann1, ann2, f"{nr}")
        self.pad.finalise()

    def test_identical(self):
        self.assertEqual(self.pad.totals, self.expected_totals)

    def assertCorrectPairs(self, list_of_pairs: list):
        self.assertEqual(len(list_of_pairs), len(self.expected_pair_order))
        for nr, (pair, expected_pair) in enumerate(zip(list_of_pairs, self.expected_pair_order)):
            with self.subTest(f"{nr}"):
                self.assertEqual(pair, expected_pair)

    def test_iteration(self):
        list_of_pairs = list(self.pad.iter_ann_pairs(omit_identical=False))
        self.assertCorrectPairs(list_of_pairs)

    def test_iteration_omit_identical(self):
        list_of_pairs = list(self.pad.iter_ann_pairs(omit_identical=True))
        # check with pop
        for expected in self.expected_pair_order:
            if expected[1].comparison_type == compare_annotations.AnnotationComparisonType.IDENTICAL:
                continue
            with self.subTest(f"{expected}"):
                self.assertEqual(list_of_pairs.pop(0), expected)

    def test_iteration_filter_all(self, doc_list = ['0', '1']):
        list_of_pairs = list(self.pad.iter_ann_pairs(docs=doc_list, omit_identical=False))
        self.assertCorrectPairs(list_of_pairs)

    def test_iteration_filter_none(self, docs=[]):
        list_of_pairs = list(self.pad.iter_ann_pairs(docs=docs, omit_identical=False))
        self.assertEqual(list_of_pairs, docs)

    def test_iteration_filter_some(self, doc='1'):
        list_of_pairs = list(self.pad.iter_ann_pairs(docs=[doc], omit_identical=False))
        # check has only this document
        doc_numbers = set([pair[0] for pair in list_of_pairs])
        self.assertEqual(doc_numbers, {doc})
        # check that is has an entry for each annotation in doc
        expected_annotations = [ann for ann in self.expected_pair_order if ann[0] == doc]
        self.assertEqual(len(expected_annotations), len(list_of_pairs))
        # check has correct pairs
        # pop the first off list every time
        for doc_name, expected_pair in self.expected_pair_order:
            if doc_name != doc:
                continue
            with self.subTest(f"{doc_name}: {expected_pair}"):
                self.assertEqual(list_of_pairs.pop(0), (doc_name, expected_pair))


class FindsParentsTest(unittest.TestCase):
    pt2ch = {
        # children
        'c1': ['c10', 'c11'],
        'c2': ['c20', 'c21', 'c22'],
        'c3': ['c30'],
        # grandchildren
        'c10': ['c100', 'c101'],
        'c30': ['c300'],
        # great grandchildren
        'c300': ['c3001', 'c3002', 'c3003']
        }
    annotations = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'c1'}
                }},
    ]
    annotations_child = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'c10'},
                }},
    ]
    annotations_grandchild = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'c101'},
                }},
    ]
    annotations_ggc1 = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'c3'},
                }},
    ]
    annotations_ggc2 = [
        # doc1
        {"entities": {
            "0": {"start": 10, "end": 25, "cui": 'c3003'},
                }},
    ]

    def _set_up_for(self, anns1: list, anns2: list
                    ) -> compare_annotations.PerAnnotationDifferences:
        pad = compare_annotations.PerAnnotationDifferences(pt2ch1=self.pt2ch,
                                                           pt2ch2=self.pt2ch)
        for nr, (ann1, ann2) in enumerate(zip(anns1, anns2)):
            pad.look_at_doc(ann1, ann2, f"{nr}")
        pad.finalise()
        return pad

    def setUp(self):
        # reg->child
        self.reg_child = self._set_up_for(self.annotations, self.annotations_child)
        # reg->grandchild
        self.reg_grandchild = self._set_up_for(self.annotations, self.annotations_grandchild)
        # child->grandchild
        self.child_grandchild = self._set_up_for(self.annotations_child, self.annotations_grandchild)
        # the opposite direction
        # child->reg
        self.child_reg = self._set_up_for(self.annotations_child, self.annotations)
        # grandchild->reg
        self.grandchild_reg = self._set_up_for(self.annotations_grandchild, self.annotations)
        # grandchild->child
        self.grandchild_child = self._set_up_for(self.annotations_grandchild, self.annotations_child)
        # great-granchild->reg
        self.ggc_reg = self._set_up_for(self.annotations_ggc1, self.annotations_ggc2)

    def assertCorrectRecognition(self, pad: compare_annotations.PerAnnotationDifferences,
                                 exp_type: compare_annotations.AnnotationComparisonType):
        self.assertEqual(len(pad.totals), 1)
        self.assertIn(exp_type, pad.totals)

    def test_child_recognised(self):
        self.assertCorrectRecognition(self.reg_child,
                                      compare_annotations.AnnotationComparisonType.SAME_PARENT)

    def test_child_recognised_reverse(self):
        self.assertCorrectRecognition(self.child_reg,
                                      compare_annotations.AnnotationComparisonType.SAME_PARENT)

    def test_grandchild_recognised_from_child(self):
        self.assertCorrectRecognition(self.child_grandchild,
                                      compare_annotations.AnnotationComparisonType.SAME_PARENT)

    def test_grandchild_recognised_from_child_reverse(self):
        self.assertCorrectRecognition(self.grandchild_child,
                                      compare_annotations.AnnotationComparisonType.SAME_PARENT)

    def test_grandchild_recognised(self):
        self.assertCorrectRecognition(self.reg_grandchild,
                                      compare_annotations.AnnotationComparisonType.SAME_GRANDPARENT)

    def test_grandchild_recognised_reverse(self):
        self.assertCorrectRecognition(self.grandchild_reg,
                                      compare_annotations.AnnotationComparisonType.SAME_GRANDPARENT)

    def test_great_grandchildren_not_recognised(self):
        self.assertCorrectRecognition(self.ggc_reg,
                                      compare_annotations.AnnotationComparisonType.SAME_SPAN_DIFF_CONCEPT)

from utils.clinical_note_splitter import normalize_date, split_one_note, split_clinical_notes

import unittest


class DateNormalizingTest(unittest.TestCase):
    # examples from docstring
    example_1 = "28 Feb 2013 04:50"
    example_2 = "Thu 28 Feb 2013 04:50"
    example_3 = "28-Feb-2013 04:50"
    examples = [(example_1, -100, -1, -2), (example_2, -2, -2, -3), (example_3, -3, -3, -4)]
    expected_output = example_1

    def test_works_examples(self):
        for example, _id, start, end in self.examples:
            with self.subTest(example):
                got = normalize_date(example, _id, start, end)
                self.assertEqual(got, self.expected_output)

    def test_no_works_nonsense(self, nonsense="Today Is Wednesday"):
        got = normalize_date(nonsense, -10, -10, -20)
        self.assertNotEqual(got, self.expected_output)
        self.assertNotEqual(nonsense, got)


class SplitOneNoteTest(unittest.TestCase):
    id = -101
    # each subsequent date should be later than previous
    # and each one is expected to have one 'entered on -'
    example = r"""Something happened
    Then there was war.
    entered on -
01 Feb 2022 01:02
    And winter came.
    entered on -
01 Feb 2024 09:59
    And then there was light!
    entered on -
01 Feb 2024 19:59
    entered on -
    """
    # add middle date to avoid doubling on 'entered on -'
    # and bump year so that the subsequent dates are later
    example2 = example + '\n'*3 + "01 Feb 2024 09:59" + '\n' + example.replace("2024", "2026")
    standard_split = 3
    extended_split = 7

    def test_note_splits(self):
        got = split_one_note(self.id, self.example)
        self.assertEqual(len(got), self.standard_split)

    def test_note_splits2(self):
        got = split_one_note(self.id, self.example2)
        self.assertEqual(len(got), self.extended_split)



class SplitClinicalNotesTest(unittest.TestCase):
    example = {
        "KEY1": SplitOneNoteTest.example,
        "KEY2": SplitOneNoteTest.example.replace("Feb", "march").replace("then", "therefore"),
        "KEY3": SplitOneNoteTest.example2,
    }

    def test_notes_split(self):
        got = split_clinical_notes(self.example)
        for key in self.example:
            with self.subTest(key):
                self.assertEqual(len(got[key]),
                                 SplitOneNoteTest.standard_split if
                                 key != "KEY3" else
                                 SplitOneNoteTest.extended_split)

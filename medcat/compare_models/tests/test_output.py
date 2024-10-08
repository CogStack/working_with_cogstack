import output

import contextlib
import io
import sys

import unittest


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield
    sys.stdout = save_stdout


class CompareDictTests(unittest.TestCase):
    example_dict = {"k1": "v1",
                    "k2": "v2",
                    "k3": {"sk1": 1.0}}
    example_dict2 = {'pretty_name': 'Genus Quercus',
                     'cui': '53347009',
                     'type_ids': ['81102976'],
                     'types': [''],
                     'source_value': 'Oak',
                     'detected_name': 'oak',
                     'acc': 0.6368384509248382,
                     'context_similarity': 0.6368384509248382,
                     'start': 43,
                     'end': 46,
                     'icd10': [],
                     'ontologies':
                     ['20220803_SNOMED_UK_CLINICAL_EXT'],
                     'snomed': [],
                     'id': 3,
                     'meta_anns': {
                         'Presence': {'value': 'True', 'confidence': 0.999996542930603, 'name': 'Presence'},
                         'Subject': {'value': 'Patient', 'confidence': 0.9396798014640808, 'name': 'Subject'},
                         'Time': {'value': 'Recent', 'confidence': 0.9999940395355225, 'name': 'Time'}
                         }
                    }
    expected_nulled_dict2 = {'pretty_name': '',
                             'cui': '',
                             'type_ids': '',
                             'types': '',
                             'source_value': '',
                             'detected_name': '',
                             'acc': '',
                             'context_similarity': '',
                             'start': '',
                             'end': '',
                             'icd10': '',
                             'ontologies': '',
                             'snomed': '',
                             'id': '',
                             'meta_anns': {}
                            }

    def setUp(self) -> None:
        self.nulled = output._get_nulled_copy(self.example_dict)
        self.nulled2 = output._get_nulled_copy(self.example_dict2)

    def test_compare_dicts_works_1st_None(self):
        with nostdout():
            output.compare_dicts(None, self.example_dict)

    def test_compare_dicts_works_2nd_None(self):
        with nostdout():
            output.compare_dicts(self.example_dict, None)

    def test_expected_nulled_real(self):
        self.assertEqual(self.nulled2, self.expected_nulled_dict2)

    def test_compare_dicts_1st_only_real(self):
        with nostdout():
            output.compare_dicts(self.example_dict2, None)

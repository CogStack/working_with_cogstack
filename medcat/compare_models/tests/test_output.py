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

    def setUp(self) -> None:
        self.nulled = output._get_nulled_copy(self.example_dict)

    def test_compare_dicts_works_1st_None(self):
        with nostdout():
            output.compare_dicts(None, self.example_dict)

    def test_compare_dicts_works_2nd_None(self):
        with nostdout():
            output.compare_dicts(self.example_dict, None)

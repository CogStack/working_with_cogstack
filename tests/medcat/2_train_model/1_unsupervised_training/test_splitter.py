import unittest

import tempfile
import os
import sys
import pandas as pd

_FILE_DIR = os.path.dirname(__file__)

# because this project isn't (at least of of writing this)
# set up as a python project, there are no __init__.py
# files in each folder
# as such, in order to gain access to the relevant module,
# I'll need to add the path manually
_WWC_BASE_FOLDER = os.path.join(_FILE_DIR, "..", "..", "..", "..")
MEDCAT_EVAL_MCT_EXPORT_FOLDER = os.path.abspath(os.path.join(_WWC_BASE_FOLDER, "medcat", "2_train_model", "1_unsupervised_training"))
sys.path.append(MEDCAT_EVAL_MCT_EXPORT_FOLDER)
# now we are able to import splitter

import splitter

FILE_TO_SPLIT = os.path.join(_WWC_BASE_FOLDER, "tests", "medcat", "resources", "example_file_to_split.csv")
NR_OF_LINES_IN_FILE = 125
NR_OF_COLUMNS_IN_FILE = 20


class SplitFileTests(unittest.TestCase):
    # lines per file - we want 4 rows, on average
    nr_of_lines = 4 * NR_OF_LINES_IN_FILE // NR_OF_COLUMNS_IN_FILE
    # NOTE: If the number of lines is not a multiple of the number of lines
    #       the expected number of files needs to be one greater
    files_expected = NR_OF_LINES_IN_FILE // nr_of_lines
    
    @classmethod
    def setUpClass(cls):
        cls.temp_folder = tempfile.TemporaryDirectory()
        cls.save_format = os.path.join(cls.temp_folder.name, "split_%03d.csv")
        # do the splitting
        splitter.split_file(FILE_TO_SPLIT, cls.nr_of_lines, cls.save_format)

    @classmethod
    def tearDownClass(cls):
        cls.temp_folder.cleanup()

    def test_has_correct_number_of_files(self):
        files = list(os.listdir(self.temp_folder.name))
        found = len(files)
        self.assertEqual(found, self.files_expected)

    def test_contains_same_content(self):
        df_orig = pd.read_csv(FILE_TO_SPLIT)
        file_names = [os.path.join(self.temp_folder.name, fn) for fn in os.listdir(self.temp_folder.name)]
        # need to sort for order
        files_to_read = sorted(file_names)
        to_concat = [pd.read_csv(f) for f in files_to_read]
        df_split = pd.concat(to_concat, ignore_index=True)
        for nr, (lo, ls) in enumerate(zip(df_orig.iterrows(), df_split.iterrows())):
            for pnr, (p1, p2) in enumerate(zip(lo, ls)):
                with self.subTest(f"L-{nr}; P-{pnr}"):
                    if isinstance(p1, pd.Series):
                        self.assertTrue(p1.equals(p2))
                    else:
                        self.assertEqual(p1, p2)

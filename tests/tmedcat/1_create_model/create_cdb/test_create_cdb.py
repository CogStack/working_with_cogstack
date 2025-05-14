import os
import sys
import shutil

import medcat.cdb
from medcat.storage.serialisers import deserialise

_FILE_DIR = os.path.dirname(__file__)

# because this project isn't (at least of of writing this)
# set up as a python project, there are no __init__.py
# files in each folder
# as such, in order to gain access to the relevant module,
# I'll need to add the path manually
_WWC_BASE_FOLDER = os.path.join(_FILE_DIR, "..", "..", "..", "..")
MEDCAT_EVAL_MCT_EXPORT_FOLDER = os.path.abspath(os.path.join(_WWC_BASE_FOLDER, "medcat", "1_create_model", "create_cdb"))
sys.path.append(MEDCAT_EVAL_MCT_EXPORT_FOLDER)
# now we are able to import create_cdb and/or create_umls_cdb

import unittest
from unittest.mock import patch

# SNOMED pre-cdb csv
PRE_CDB_CSV_PATH_SNOMED = os.path.join(_WWC_BASE_FOLDER, "tests", "tmedcat", "resources", "example_cdb_input_snomed.csv")
PRE_CDB_CSV_PATH_UMLS = os.path.join(_WWC_BASE_FOLDER, "tests", "tmedcat", "resources", "example_cdb_input_umls.csv")


def get_mock_input(output: str):
    def mock_input(prompt: str):
        return output
    return mock_input


class CreateCDBTest(unittest.TestCase):

    def setUp(self) -> None:
        self.output_cdb = None

    def tearDown(self) -> None:
        if self.output_cdb is not None and os.path.exists(self.output_cdb):
            shutil.rmtree(self.output_cdb)

    def assertHasCDB(self, path: str):
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".dat"))
        cdb: CDB = deserialise(path)
        self.assertIsInstance(cdb, medcat.cdb.CDB)

    def test_snomed_cdb_creation(self):
        # Replace the 'input' function with 'mock_input'
        with patch('builtins.input', side_effect=get_mock_input(PRE_CDB_CSV_PATH_SNOMED)):
            import create_cdb
        self.output_cdb = create_cdb.output_cdb
        self.assertHasCDB(self.output_cdb)

    def test_umls_cdb_creation(self):
        with patch('builtins.input', side_effect=get_mock_input(PRE_CDB_CSV_PATH_UMLS)):
            import create_umls_cdb
        self.output_cdb = create_umls_cdb.output_cdb
        self.assertHasCDB(self.output_cdb)

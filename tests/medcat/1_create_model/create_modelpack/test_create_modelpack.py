import os
import sys

import unittest
# import unittest.mock

import tempfile


# relative to file path
_FILE_DIR = os.path.dirname(__file__)
# because this project isn't (at least of of writing this)
# set up as a python project, there are no __init__.py
# files in each folder
# as such, in order to gain access to the relevant module,
# I'll need to add the path manually
_WWC_BASE_FOLDER = os.path.join(_FILE_DIR, "..", "..", "..", "..")
MEDCAT_CREATE_MODELPACK_FOLDER = os.path.abspath(os.path.join(_WWC_BASE_FOLDER, "medcat", "1_create_model", "create_modelpack"))
sys.path.append(MEDCAT_CREATE_MODELPACK_FOLDER)
# now we are able to import create_modelpack

import create_modelpack

RESOURCES_FOLDER = os.path.join(_WWC_BASE_FOLDER, "tests", "medcat", "resources")
DEFAULT_CDB_PATH = os.path.join(RESOURCES_FOLDER, "cdb.dat")
DEFAULT_VOCAB_PATH = os.path.join(RESOURCES_FOLDER, "vocab.dat")


class CreateModelPackTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tempfolder = tempfile.TemporaryDirectory()
        cls.model_pack_name = "TEMP_MODEL_PACK"
        cls.partial_model_pack_path = os.path.join(cls.tempfolder.name, cls.model_pack_name)

    @classmethod
    def tearDownClass(cls):
        cls.tempfolder.cleanup()

    def test_a(self):
        model_pack_name = create_modelpack.load_cdb_and_save_modelpack(
            DEFAULT_CDB_PATH, self.model_pack_name,
            self.tempfolder.name, DEFAULT_VOCAB_PATH)
        self.assertTrue(model_pack_name.startswith(self.model_pack_name))
        model_pack_path = os.path.join(self.tempfolder.name, model_pack_name)
        self.assertTrue(os.path.exists(model_pack_path))

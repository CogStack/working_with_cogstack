import os
import sys

import medcat.vocab

_FILE_DIR = os.path.dirname(__file__)

# because this project isn't (at least of of writing this)
# set up as a python project, there are no __init__.py
# files in each folder
# as such, in order to gain access to the relevant module,
# I'll need to add the path manually
_WWC_BASE_FOLDER = os.path.join(_FILE_DIR, "..", "..", "..", "..")
MEDCAT_EVAL_MCT_EXPORT_FOLDER = os.path.abspath(os.path.join(_WWC_BASE_FOLDER, "medcat", "1_create_model", "create_vocab"))
sys.path.append(MEDCAT_EVAL_MCT_EXPORT_FOLDER)
# now we are able to import create_cdb and/or create_umls_cdb

import unittest
from unittest.mock import patch, mock_open


VOCAB_INPUT_PATH = os.path.abspath(os.path.join(_WWC_BASE_FOLDER, "models", "vocab", "vocab_data.txt"))
VOCAB_OUTPUT_PATH = os.path.abspath(os.path.join(_WWC_BASE_FOLDER, "models", "vocab", "vocab.dat"))
VOCAB_INPUT = [
    "house	34444	 0.3232 0.123213 1.231231"
    "dog	14444	0.76762 0.76767 1.45454"
]

orig_open = open


def custom_open(file, mode="r", *args, **kwargs):
    if 'r' in mode:
        return mock_open(read_data="\n".join(VOCAB_INPUT))(file, mode, *args, **kwargs)
    return orig_open(file, mode, *args, **kwargs)


class CreateVocabTest(unittest.TestCase):
    temp_vocab_path = "temp_vocab_for_test_create_vocab"

    def setUp(self) -> None:
        if os.path.exists(VOCAB_OUTPUT_PATH):
            os.rename(VOCAB_OUTPUT_PATH, self.temp_vocab_path)
            self.moved = True
        else:
            self.moved = False

    def tearDown(self) -> None:
        if os.path.exists(VOCAB_OUTPUT_PATH):
            os.remove(VOCAB_OUTPUT_PATH)
        if self.moved:
            os.rename(self.temp_vocab_path, VOCAB_OUTPUT_PATH)

    def test_creating_vocab(self):
        with patch('builtins.open', side_effect=custom_open):
            import create_vocab
        vocab_path = os.path.join(create_vocab.vocab_dir, "vocab.dat")
        self.assertEqual(os.path.abspath(vocab_path), VOCAB_OUTPUT_PATH)
        self.assertTrue(os.path.exists(vocab_path))
        vocab = medcat.vocab.Vocab.load(vocab_path)
        self.assertIsInstance(vocab, medcat.vocab.Vocab)

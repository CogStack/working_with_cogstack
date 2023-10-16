import os

from medcat.vocab import Vocab
from medcat.cdb import CDB
from medcat.cat import CAT

# relative to file path
_FILE_DIR = os.path.dirname(__file__)
# relative path to working_with_cogstack folder
_REL_PATH = os.path.join("..", "..", "..")
_BASE_PATH = os.path.join(_FILE_DIR, _REL_PATH)
# absolute path to working_with_cogstack folder
BASE_PATH = os.path.abspath(_BASE_PATH)

model_name = "<NAME OF MODEL HERE>"  # Change to specific cdb of interest

cdb_model_path = os.path.join(BASE_PATH, "models", "cdb")
cdb_model = os.path.join(cdb_model_path, f"{model_name}.dat")

vocab_model_path = os.path.join(BASE_PATH, "models", "vocab")
modelpack_path = os.path.join(BASE_PATH, "models", "modelpack")
modelpack_name = "<NAME OF output MODELPACK HERE>.dat"  # Change to the name of your model

# Load cdb
cdb = CDB.load(cdb_model)

# Set cdb configuration
# technically we already created this during the cdb creation
cdb.config.ner['min_name_len'] = 2
cdb.config.ner['upper_case_limit_len'] = 3
cdb.config.general['spell_check'] = True
cdb.config.linking['train_count_threshold'] = 10
cdb.config.linking['similarity_threshold'] = 0.3
cdb.config.linking['train'] = True
cdb.config.linking['disamb_length_limit'] = 4
cdb.config.general['full_unlink'] = True

# Load vocab
vocab = Vocab.load(vocab_model_path)

# Initialise the model
cat = CAT(cdb=cdb, config=cdb.config, vocab=vocab)

# Create and save model pack
cat.create_model_pack(save_dir_path=modelpack_path, model_pack_name=modelpack_name)


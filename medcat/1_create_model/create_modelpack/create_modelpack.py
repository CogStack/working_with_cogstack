import os

from medcat.vocab import Vocab
from medcat.cdb import CDB
from medcat.cat import CAT
from medcat.storage.serialisers import deserialise

# relative to file path
_FILE_DIR = os.path.dirname(__file__)
# relative path to working_with_cogstack folder
_REL_PATH = os.path.join("..", "..", "..")
_BASE_PATH = os.path.join(_FILE_DIR, _REL_PATH)
# absolute path to working_with_cogstack folder
BASE_PATH = os.path.abspath(_BASE_PATH)

DEFAULT_CDB_FOLDER = os.path.join(BASE_PATH, "models", "cdb")

DEFAULT_VOCAB_FOLDER = os.path.join(BASE_PATH, "models", "vocab")
DEFAULT_VOCAB_PATH = os.path.join(DEFAULT_VOCAB_FOLDER, 'vocab.dat')

DEFAULT_MODELPACK_FOLDER = os.path.join(BASE_PATH, "models", "modelpack")

model_name = "<NAME OF MODEL HERE>"  # Change to specific cdb of interest
modelpack_name = "<NAME OF output MODELPACK HERE>.dat"  # Change to the name of your model

def load_cdb_and_save_modelpack(cdb_path: str,
                                modelpack_name: str,
                                modelpack_path: str = DEFAULT_MODELPACK_FOLDER,
                                vocab_path: str = DEFAULT_VOCAB_PATH) -> str:
    """Load a CDB and save it as a model pack along with the default Vocab.

    Args:
        cdb_path (str): The CDB path to load.
        modelpack_name (str): The model pack name to write to.
        modelpack_path (str): The folder to write the model pack to.
            Defaults to `DEFAULT_MODELPACK_FOLDER`.
        vocab_path (str): The vocab path. Defaults to `DEFAULT_VOCAB_PATH`.

    Returns:
        str: The model pack path.
    """
    # Load cdb
    cdb: CDB
    try:
        cdb = deserialise(cdb_path)
    except NotADirectoryError:
        from medcat.utils.legacy.convert_cdb import get_cdb_from_old
        cdb = get_cdb_from_old(cdb_path)

    # Set cdb configuration
    # technically we already created this during the cdb creation
    cdb.config.components.ner.min_name_len = 2
    cdb.config.components.ner.upper_case_limit_len = 3
    cdb.config.general.spell_check = True
    cdb.config.components.linking.train_count_threshold = 10
    cdb.config.components.linking.similarity_threshold = 0.3
    cdb.config.components.linking.train = True
    cdb.config.components.linking.disamb_length_limit = 4
    cdb.config.general.full_unlink = True

    # Load vocab
    vocab: Vocab
    try:
        vocab = deserialise(vocab_path)
    except NotADirectoryError:
        from medcat.utils.legacy.convert_vocab import get_vocab_from_old
        vocab = get_vocab_from_old(vocab_path)

    # Initialise the model
    cat = CAT(cdb=cdb, config=cdb.config, vocab=vocab)

    # Create and save model pack
    return cat.save_model_pack(modelpack_path, pack_name=modelpack_name)


def load_cdb_and_save_modelpack_in_def_location(cdb_name: str,
                                                modelpack_name: str) -> str:
    cdb_path = os.path.join(DEFAULT_CDB_FOLDER, cdb_name)
    return load_cdb_and_save_modelpack(cdb_path, modelpack_name,
                                       DEFAULT_MODELPACK_FOLDER,
                                       DEFAULT_VOCAB_PATH)

def main():
    load_cdb_and_save_modelpack_in_def_location(model_name, modelpack_name)

if __name__ == "__main__":
    main()

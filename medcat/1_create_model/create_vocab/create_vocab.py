from medcat.vocab import Vocab
import os

vocab = Vocab()

# relative to file path
_FILE_DIR = os.path.dirname(__file__)
# relative path to working_with_cogstack folder
_REL_PATH = os.path.join("..", "..", "..")
_BASE_PATH = os.path.join(_FILE_DIR, _REL_PATH)
# absolute path to working_with_cogstack folder
BASE_PATH = os.path.abspath(_BASE_PATH)
vocab_dir = os.path.join(BASE_PATH, "models", "vocab")

# the vocab.txt file need to be in the tab sep format: <token>\t<word_count>\t<vector_embedding_separated_by_spaces>
# Current vocab uses pre-calculated vector embedding from Word2Vec, future use embeddings calculated from BERT tokeniser
# embeddings of 300 dimensions is standard

vocab.add_words(os.path.join(vocab_dir, 'vocab_data.txt'), replace=True)
vocab.make_unigram_table()
vocab.save(os.path.join(vocab_dir + "vocab.dat"))

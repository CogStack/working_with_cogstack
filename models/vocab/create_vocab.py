from medcat.vocab import Vocab
import os

vocab = Vocab()

model_dir = "data/medcat_models/vocab"

# the vocab.txt file need to be in the tab sep format: <token>\t<word_count>\t<vector_embedding_separated_by_spaces>
# Current vocab uses pre-calculated vector embedding from Word2Vec, future use embeddings calculated from BERT tokeniser
# embeddings of 300 dimensions is standard

vocab.add_words(os.path.join(model_dir, 'vocab_data.txt'), replace=True)
vocab.make_unigram_table()
vocab.save(os.path.join(model_dir + "vocab.dat"))

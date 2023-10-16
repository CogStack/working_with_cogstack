from medcat.cat import CAT
import pandas as pd
import os
import logging

# python medcat/2_train_model/1_unsupervised_training/splitter.py
# medcat/2_train_model/1_unsupervised_training/all_notes.csv medcat/2_train_model/1_unsupervised_training/split_notes_5M_%d.csv 5000000
#

all_notes_file = 'all_notes.csv' # CHANGE AS NEEDED

# in my case, I needed to split the notes into parts. Otherwise, the work just crashed at some point
# I chose to split into 19 parts, around 5000000 lines at a time.
split_format = 'split_notes_5M_%d.csv'
nr_of_lines = 5000000

from splitter import split_file

if not os.path.exists(split_format%1):
    print(f'\n\nSplitting file into {nr_of_lines} line at a time. This will probably take some time\n\n')
    split_file(all_notes_file, nr_of_lines, split_format)
    print('\n\nDone with the split!\n\n')
else:
    print('\n\nNB!Expecting the split files to already exist\n\n')

data_dir = '.' # CHANGE AS NEEDED


# relative to file path
_FILE_DIR = os.path.dirname(__file__)
# relative path to working_with_cogstack folder
_REL_PATH = os.path.join("..", "..", "..")
_BASE_PATH = os.path.join(_FILE_DIR, _REL_PATH)
# absolute path to working_with_cogstack folder
BASE_PATH = os.path.abspath(_BASE_PATH)

model_dir = os.path.join(BASE_PATH, "data", "medcat_models", "modelpack")

modelpack = 'umls_model2_zip_0d4ccc7b9ae1ecd2.zip' # CHANGE AS NEEDED
model_pack_path = os.path.join(model_dir, modelpack)

output_modelpack = 'umls_self_train_model'  # Save name for new model

# Load modelpack
print('Loading modelpack')
cat = CAT.load_model_pack(model_pack_path)
cat.log.addHandler(logging.StreamHandler()) # add console output

print('STATS:')
cat.cdb.print_stats()

# CHANGE AS NEEDED - if the number of spligt files is different
all_data_files = [f'split_notes_5M_{nr}.csv' for nr in range(1, 20)]  # file containing training material.
for i, data_file in enumerate(all_data_files):
    # Load training data
    print('Load data for', i, 'from', data_file)
    data = pd.read_csv(os.path.join(data_dir, data_file))
    cat.train(data.text.values, progress_print=100)

    print('Stats now, after', i)
    cat.cdb.print_stats()

    # save modelpack
    cat.create_model_pack(save_dir_path=model_dir, model_pack_name=f"{output_modelpack}_{i}")

# save modelpack - ALL
cat.create_model_pack(save_dir_path=model_dir, model_pack_name=output_modelpack)


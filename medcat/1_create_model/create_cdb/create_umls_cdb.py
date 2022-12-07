import os
import pandas as pd
from medcat.config import Config
from medcat.cdb_maker import CDBMaker

pd.options.mode.chained_assignment = None

# this is expected to be output from medcat.utils.preprocess_umls
# i.e not the raw UMLS files
csv_path = input("Enter specific UMLS pre-cdb csv found in the path data/umls: ")
release = '2022AA' # or as appropriate

if not os.path.exists('models'):
    os.makedirs('models')
    print("Creating a 'models' folder to store model")

model_dir = './models/'
output_cdb = model_dir + f"{release}_UMLS_cdb.dat"
csv = pd.read_csv(csv_path)

# Remove null values
sctid_null_index = csv[csv['name'].isnull()].index.copy()
csv['name'].iloc[sctid_null_index] = "N/A"

csv = csv.drop_duplicates(keep='first').reset_index(drop=True)


# Setup config
config = Config()
config.general['spacy_model'] = 'en_core_web_md'
config.cdb_maker['remove_parenthesis'] = 1
config.general['cdb_source_name'] = f'UMLS_{release}'

maker = CDBMaker(config)


# Create your CDB
# Add more cdbs to the list
csv_paths = [csv_path]
cdb = maker.prepare_csvs(csv_paths, full_build=True) 

# Add type_id pretty names to cdb
cdb.config.linking['filters']['cuis'] = set(csv['cui'].tolist())  # Add all cuis to filter out legacy terms.

# save model
cdb.save(output_cdb)
print(f"CDB Model saved successfully as: {output_cdb}")

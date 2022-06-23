import os
import pandas as pd
from medcat.config import Config
from medcat.cdb_maker import CDBMaker

pd.options.mode.chained_assignment = None

csv_path = input("Enter specific SNOMED pre-cdb csv found in the path data/snomed: ")
release = csv_path[-12:-4]

if not os.path.exists('models'):
    os.makedirs('models')
    print("Creating a 'models' folder to store model")

model_dir = './models/'
output_cdb = model_dir + f"{release}_SNOMED_cdb.dat"
csv = pd.read_csv(csv_path)

# Remove null values
sctid_null_index = csv[csv['name'].isnull()].index.copy()
csv['name'].iloc[sctid_null_index] = "N/A"

# Only filter acronyms for specific Semantic tags
csv['acronym'] = csv[~csv['description_type_ids'].str.
                     contains("assessment scale|"
                              "core metadata concept|"
                              "metadata|"
                              "foundation metadata concept"
                              "|OWL metadata concept")]['name'].str.\
    extract("([A-Z]{2,6}) - ", expand=True)

print("Cleaning acronyms...")
for i, row in csv[(~csv['acronym'].isnull()) & (csv['name_status'] == 'A')][['name', 'acronym']].iterrows():
    if row['name'][0:len(row['acronym'])] == row['acronym']:
        csv['name'].iloc[i] = row['acronym']

print("acronyms complete")

csv = csv.drop_duplicates(keep='first').reset_index(drop=True)
csv.pop('acronym')


# Setup config
config = Config()
config.general['spacy_model'] = 'en_core_web_md'
config.cdb_maker['remove_parenthesis'] = 1
config.general['cdb_source_name'] = f'SNOMED_{release}'

maker = CDBMaker(config)


# Create your CDB
# Add more cdbs to the list
csv_paths = [csv_path]
cdb = maker.prepare_csvs(csv_paths, full_build=True)

# Add type_id pretty names to cdb
cdb.addl_info['type_id2name'] = pd.Series(csv.description_type_ids.values, index=csv.type_ids.astype(str)).to_dict()
cdb.linking['filters']['cuis'] = set(csv['cui'].tolist())  # Add all cuis to filter out legacy terms.

# save model
cdb.save(output_cdb)
print(f"CDB Model saved successfully as: {output_cdb}")





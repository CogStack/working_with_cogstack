import os
import zipfile
import pandas as pd
from umls_downloader import download_umls
from tqdm.autonotebook import tqdm

api_key = ''
version = '2022AA'
outfile = f'{version}_UMLS_english.csv'

umls_rows = []
path = download_umls(version=version, api_key=api_key)
with zipfile.ZipFile(path) as zip_file:
    with zip_file.open("MRCONSO.RRF", mode='r') as file:
        with tqdm(total=sum(1 for _ in file), unit='line') as pbar:
            file.seek(0) # reset file pointer to the begining of the file
            for line in file:
                umls_rows.append(line.decode('UTF-8').split('|')[:-1])
                pbar.update(1)
columns = [
    'CUI',
    'LAT',
    'TS',
    'LUI',
    'STT',
    'SUI',
    'ISPREF',
    'AUI',
    'SAUI',
    'SCUI',
    'SDUI',
    'SAB',
    'TTY',
    'CODE',
    'STR',
    'SRL',
    'SUPPRESS',
    'CVF',
]

umls_df = pd.DataFrame(columns=columns, data=umls_rows)
eng_umls = umls_df[umls_df['LAT'] == 'ENG']
del umls_df
outfile = f'{version}_UMLS_english.csv'
eng_umls.to_csv(outfile, index=False)
print(f'file saved as {outfile}')

medcat_csv_mapper = {
    'CUI':'cui',
    'STR':'name',
    'SAB':'ontologies',
    'ISPREF':'name_status',
    'TUI':'type_ids',
}




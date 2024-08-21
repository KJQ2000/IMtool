import os, shutil
import pandas as pd
import sys
import openpyxl as opxl
import dictionary as dic
from models import Database
import logging

db = Database(os.environ["DATABASE_URL"])

import_dir = dic.IMPORT_DIR

files_to_import = []

insert_values = []
char_limit = dic.BATCH_INSERT_LIMIT


for filename in os.listdir(import_dir):
    if filename.endswith('.xlsx'):
        files_to_import.append(os.path.join(import_dir, filename))
    elif filename.endswith('.csv'):
        files_to_import.append(os.path.join(import_dir, filename))

for file in files_to_import:
    if file.endswith('.csv'):
        df = pd.read_csv(file)

    elif file.endswith('.xlsx'):
        df = pd.read_excel(file)
    for index, row in df.iterrows():
        value_tuple = str(tuple(row))
        if len(', '.join(str(insert_values)) + value_tuple) > char_limit:
            db.batch_insert(table='stock',values=insert_values)
            insert_values = []
        value_tuple = list(tuple(row))
        insert_values.append(value_tuple)
    try:
        db.batch_insert(table='users',values=insert_values)
        shutil.move(file, dic.SUCCESS_IMPORT_DIR+str(file.split('/')[-1])) 
    except Exception as e:
        shutil.move(file, dic.FAILED_IMPORT_DIR+str(file.split('/')[-1])) 
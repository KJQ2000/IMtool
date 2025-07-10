from dotenv import load_dotenv
import os
import shutil
import pandas as pd
import sys
import openpyxl as opxl
import logging

import dictionary as dic
from models import Database

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

TABLE = {
    'usr': 'users',
    'book': 'booking',
    'cust': 'customer',
    'stk': 'stock',
    'sale': 'sale',
    'slm': 'salesman',
    'pur': 'purchase',
    'cpat': 'category_pattern_mapping'
}


def process_import_files(import_dir, db, char_limit):
    files_to_import = []

    # Collect all CSV and XLSX files
    for filename in os.listdir(import_dir):
        if filename.endswith(('.xlsx', '.csv')):
            files_to_import.append(os.path.join(import_dir, filename))

    for file in files_to_import:
        try:
            # Read file based on extension
            if file.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            table = TABLE.get(str(df.columns[0].split('_')[0]).lower())
            if not table:
                raise ValueError(f"Unknown table prefix in columns: {df.columns[0]}")

            file_name = os.path.basename(file)
            insert_values = []
            df_columns = df.columns.tolist()

            for index, row in df.iterrows():
                value_tuple = list(tuple(row))
                test_length = len(', '.join(map(str, insert_values + [value_tuple])))
                if test_length > char_limit:
                    db.batch_insert(table=table, values=insert_values, columns=df_columns)
                    insert_values = []

                insert_values.append(value_tuple)

            # Final insert
            if insert_values:
                db.batch_insert(table=table, values=insert_values, columns=df_columns)

            shutil.move(file, os.path.join(dic.SUCCESS_IMPORT_DIR, file_name))
            logging.info(f"Imported and moved: {file_name}")

        except Exception as e:
            shutil.move(file, os.path.join(dic.FAILED_IMPORT_DIR, os.path.basename(file)))
            logging.error(f"Failed to import {file}: {e}", exc_info=True)


def main():
    try:
        # db = Database(os.environ["DATABASE_URL"])
        # db = Database(os.environ["DEV_DATABASE_URL"])
        db = Database(
            host=os.environ("HOST"),
            port=os.environ("PORT"),
            database=os.environ("DATABASE"),
            user=os.environ("USER"),
            password=os.environ("PASSWORD")
        )
        import_dir = dic.IMPORT_DIR
        char_limit = dic.BATCH_INSERT_LIMIT

        logging.info("Starting import process...")
        process_import_files(import_dir, db, char_limit)
        logging.info("Import process completed.")

    except Exception as e:
        logging.error("Fatal error during import.", exc_info=True)


if __name__ == "__main__":
    main()


# import os, shutil
# import pandas as pd
# import sys
# import openpyxl as opxl
# import dictionary as dic
# from models import Database
# import logging

# db = Database(os.environ["DATABASE_URL"])

# import_dir = dic.IMPORT_DIR

# files_to_import = []

# insert_values = []
# char_limit = dic.BATCH_INSERT_LIMIT

# TABLE = {
#     'usr' : 'users',
#     'book' : 'booking',
#     'cust' : 'customer',
#     'stk' : 'stock',
#     'sale' : 'sale',
#     'slm' : 'salesman',
#     'pur' : 'purchase',
#     'cpat'  :'category_pattern_mapping'
# }


# for filename in os.listdir(import_dir):
#     if filename.endswith('.xlsx'):
#         files_to_import.append(os.path.join(import_dir, filename))
#     elif filename.endswith('.csv'):
#         files_to_import.append(os.path.join(import_dir, filename))

# for file in files_to_import:
#     if file.endswith('.csv'):
#         df = pd.read_csv(file)

#     elif file.endswith('.xlsx'):
#         df = pd.read_excel(file)

#     table = TABLE.get(str(df.columns[0].split('_')[0]).lower())
#     file_name = os.path.basename(file)
#     for index, row in df.iterrows():
#         value_tuple = str(tuple(row))
#         if len(', '.join(str(insert_values)) + value_tuple) > char_limit:
#             df_columns = df.columns.tolist()
#             db.batch_insert(table=table,values=insert_values,columns=df_columns)
#             insert_values = []
#         value_tuple = list(tuple(row))
#         insert_values.append(value_tuple)
#     try:
#         db.batch_insert(table=table,values=insert_values,columns=df_columns)
#         shutil.move(file, os.path.join(dic.SUCCESS_IMPORT_DIR,file_name)) 
#     except Exception as e:
#         shutil.move(file, os.path.join(dic.FAILED_IMPORT_DIR,file_name)) 
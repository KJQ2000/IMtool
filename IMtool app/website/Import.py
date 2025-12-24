from dotenv import load_dotenv
import os
import shutil
import pandas as pd
import sys
import openpyxl as opxl
import logging
import numpy as np
import json

import dictionary as dic
from models import Database

load_dotenv()

# ------------------------
# Logging
# ------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------
# Custom Exceptions
# ------------------------
class ImportValidationError(Exception):
    """Raised for business-rule validation failures"""
    pass

# ------------------------
# Table Prefix Mapping
# ------------------------
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

# ------------------------
# Core Import Logic
# ------------------------
def process_import_files(import_dir, db, char_limit):
    files_to_import = []
    success_row = 0

    # Collect files
    for filename in os.listdir(import_dir):
        if filename.endswith(('.xlsx', '.csv')):
            files_to_import.append(os.path.join(import_dir, filename))

    if not files_to_import:
        raise ImportValidationError("No import files found")

    for file in files_to_import:
        iter_count = 0
        insert_values = []

        try:
            # ------------------------
            # Read file
            # ------------------------
            if file.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, engine="openpyxl")

            if df.empty:
                raise ImportValidationError("Uploaded file is empty")

            # ------------------------
            # Determine table
            # ------------------------
            table_prefix = str(df.columns[0]).split('_')[0].lower()
            table = TABLE.get(table_prefix)

            if not table:
                raise ImportValidationError(
                    f"Unknown table prefix in column: {df.columns[0]}"
                )

            # ------------------------
            # Stock-specific logic
            # ------------------------
            if table == 'stock':
                df['stk_type'] = df['stk_type'].str.upper()
                df['pur_code'] = df['pur_code'].str.upper()

                distinct_pur = db.select(
                    table='purchase',
                    columns=[
                        'pur_id',
                        'pur_code',
                        'pur_gold_cost',
                        'pur_gold_cost_999',
                        'pur_date'
                    ]
                )

                if distinct_pur is None or distinct_pur.empty:
                    raise ImportValidationError(
                        "Purchase master table is empty"
                    )

                merged = pd.merge(
                    df,
                    distinct_pur,
                    on='pur_code',
                    how='left'
                )

                missing_mask = merged['pur_id'].isna()
                if missing_mask.any():
                    missing_codes = (
                        merged.loc[missing_mask, 'pur_code']
                        .unique()
                        .tolist()
                    )
                    raise ImportValidationError(
                        f"Missing purchase reference for pur_code(s): {missing_codes}"
                    )

                conditions = [
                    merged['stk_gold_type'] == 916,
                    merged['stk_gold_type'] == 999
                ]
                choices = [
                    merged['pur_gold_cost'],
                    merged['pur_gold_cost_999']
                ]

                merged['stk_pur_id'] = merged['pur_id']
                merged['stk_gold_cost'] = np.select(
                    conditions,
                    choices,
                    default=None
                )
                merged['stk_pur_date'] = merged['pur_date']
                merged['stk_status'] = 'IN STOCK'

                merged.drop(
                    columns=[
                        'pur_id',
                        'pur_gold_cost',
                        'pur_gold_cost_999',
                        'pur_date',
                        'pur_code'
                    ],
                    inplace=True
                )

                df = merged.copy()

            # ------------------------
            # Batch insert
            # ------------------------
            df_columns = df.columns.tolist()

            for _, row in df.iterrows():
                value_tuple = list(tuple(row))
                test_length = len(', '.join(map(str, insert_values + [value_tuple])))

                if test_length > char_limit:
                    db.batch_insert(
                        table=table,
                        values=insert_values,
                        columns=df_columns
                    )
                    success_row += iter_count
                    insert_values = []
                    iter_count = 0

                insert_values.append(value_tuple)
                iter_count += 1

            # Final batch
            if insert_values:
                db.batch_insert(
                    table=table,
                    values=insert_values,
                    columns=df_columns
                )
                success_row += iter_count

            # ------------------------
            # Move file on success
            # ------------------------
            shutil.move(
                file,
                os.path.join(dic.SUCCESS_IMPORT_DIR, os.path.basename(file))
            )
            logging.info(f"Imported successfully: {os.path.basename(file)}")

        except ImportValidationError:
            shutil.move(
                file,
                os.path.join(dic.FAILED_IMPORT_DIR, os.path.basename(file))
            )
            logging.warning(f"Validation failed for {file}")
            raise

        except Exception:
            shutil.move(
                file,
                os.path.join(dic.FAILED_IMPORT_DIR, os.path.basename(file))
            )
            logging.error("Unexpected import error", exc_info=True)
            raise

    return success_row

# ------------------------
# Entry Point
# ------------------------
def main():
    try:
        db = Database(
            host=os.environ["HOST"],
            port=os.environ["PORT"],
            database=os.environ["DATABASE"],
            user=os.environ["USER"],
            password=os.environ["PASSWORD"]
        )

        logging.info("Starting import process...")

        success_record = process_import_files(
            dic.IMPORT_DIR,
            db,
            dic.BATCH_INSERT_LIMIT
        )

        print(json.dumps({
            "status": "success",
            "success_row": success_record
        }))

    except ImportValidationError as e:
        print(json.dumps({
            "status": "failed",
            "message": str(e),
            "success_row": 0
        }))
        sys.exit(1)

    except Exception:
        print(json.dumps({
            "status": "failed",
            "message": "Unexpected system error during import",
            "success_row": 0
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()


## Original Code
# from dotenv import load_dotenv
# import os
# import shutil
# import pandas as pd
# import sys
# import openpyxl as opxl
# import logging
# import numpy as np
# import json

# import dictionary as dic
# from models import Database

# load_dotenv()

# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# # ------------------------
# # Custom Exceptions
# # ------------------------
# class ImportValidationError(Exception):
#     """Raised for business-rule validation failures"""
#     pass

# TABLE = {
#     'usr': 'users',
#     'book': 'booking',
#     'cust': 'customer',
#     'stk': 'stock',
#     'sale': 'sale',
#     'slm': 'salesman',
#     'pur': 'purchase',
#     'cpat': 'category_pattern_mapping'
# }


# def process_import_files(import_dir, db, char_limit):
#     files_to_import = []
#     success_row = 0
#     iter_count = 0

#     # Collect all CSV and XLSX files
#     for filename in os.listdir(import_dir):
#         if filename.endswith(('.xlsx', '.csv')):
#             files_to_import.append(os.path.join(import_dir, filename))

#     for file in files_to_import:
#         try:
#             # Read file based on extension
#             if file.endswith('.csv'):
#                 df = pd.read_csv(file)
#             else:
#                 df = pd.read_excel(file, engine="openpyxl")

#             table = TABLE.get(str(df.columns[0].split('_')[0]).lower())
#             if not table:
#                 raise ValueError(f"Unknown table prefix in columns: {df.columns[0]}")
            
#             if table == 'stock':
#                 df['stk_type'] = df['stk_type'].str.upper()
#                 df['pur_code'] = df['pur_code'].str.upper()
#                 distinct_pur = db.select(table='purchase',columns=['pur_id','pur_code','pur_gold_cost','pur_gold_cost_999','pur_date'])
#                 if distinct_pur is None:
#                     raise ValueError(
#                         f"Missing purchase reference for all pur_code"
#                     )
#                 merged = pd.merge(df,distinct_pur,on='pur_code',how='left')
                
#                 # Check Missing PUR_ID
#                 missing_mask = merged['pur_id'].isna()
#                 if missing_mask.any():
#                     missing_rows = merged.loc[missing_mask, 'pur_code'].unique().tolist()
#                     raise ValueError(
#                         f"Missing purchase reference for pur_code(s): {missing_rows}"
#                     )
                
#                 ## stk_gold_cost conditions
#                 conditions = [
#                     merged['stk_gold_type'] == 916,
#                     merged['stk_gold_type'] == 999
#                 ]
#                 choices = [
#                     merged['pur_gold_cost'],
#                     merged['pur_gold_cost_999']
#                 ]
                
#                 merged['stk_pur_id'] = merged['pur_id']
#                 merged['stk_gold_cost'] = np.select(conditions, choices, default=None)
#                 merged['stk_pur_date'] = merged['pur_date']
#                 merged['stk_status'] = 'IN STOCK'
#                 merged.drop(columns=['pur_id','pur_gold_cost','pur_code','pur_gold_cost_999','pur_date'],inplace=True)
#                 df = merged.copy()

#             file_name = os.path.basename(file)
#             insert_values = []
#             df_columns = df.columns.tolist()

#             for index, row in df.iterrows():
#                 value_tuple = list(tuple(row))
#                 test_length = len(', '.join(map(str, insert_values + [value_tuple])))
#                 if test_length > char_limit:
#                     insert_result = db.batch_insert(table=table, values=insert_values, columns=df_columns)
#                     insert_values = []
#                     if insert_result :
#                         success_row += iter_count
#                         iter_count = 0

#                 insert_values.append(value_tuple)
#                 iter_count += 1

#             # Final insert
#             if insert_values:
#                 success_row += iter_count
#                 db.batch_insert(table=table, values=insert_values, columns=df_columns)

#             shutil.move(file, os.path.join(dic.SUCCESS_IMPORT_DIR, file_name))
#             logging.info(f"Imported and moved: {file_name}")
#             return success_row

#         except Exception as e:
#             shutil.move(file, os.path.join(dic.FAILED_IMPORT_DIR, os.path.basename(file)))
#             logging.error(f"Failed to import {file}: {e}", exc_info=True)
#             raise ValueError(
#                 f"Failed to import {file}: {e}"
#             )


# def main():
#     try:
#         # db = Database(os.environ["DATABASE_URL"])
#         # db = Database(os.environ["DEV_DATABASE_URL"])
#         db = Database(
#             host=os.environ["HOST"],
#             port=os.environ["PORT"],
#             database=os.environ["DATABASE"],
#             user=os.environ["USER"],
#             password=os.environ["PASSWORD"]
#             )
#         import_dir = dic.IMPORT_DIR
#         char_limit = dic.BATCH_INSERT_LIMIT

#         logging.info("Starting import process...")
#         success_record = process_import_files(import_dir, db, char_limit)        
#         logging.info("Import process completed.")
        
#         print(json.dumps({
#             "status": "success",
#             "success_row": success_record
#         }))

#     except Exception as e:
#         logging.error("Fatal error during import.", exc_info=True)
#         print(json.dumps({
#             "status": "failed",
#             "success_row": 0
#         }))
#         sys.exit(1)


# if __name__ == "__main__":
#     main()
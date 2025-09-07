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
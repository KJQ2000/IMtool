DATABASE_URL = 'postgresql://JunQiang:UBjUWi4UNOlyiMQy22_ZsQ@konghin-imtool-7458.6xw.aws-ap-southeast-1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full'
SCHEMA = 'konghin'


USER_SEQ = 'usr_id_seq'
BOOKING_SEQ = 'book_id_seq'
CUSTOMER_SEQ = 'cust_id_seq'
STOCK_SEQ = 'stk_id_seq'
SALE_SEQ = 'sale_id_seq'
SALESMAN_SEQ = 'slm_id_seq'
PURCHASE_SEQ = 'pur_id_seq'


IMPORT_DIR = r'./IMTool app/system_files/Import/'
SUCCESS_IMPORT_DIR = r'./IMTool app/system_files/Import/ARCHIVED/SUCCESS/'
FAILED_IMPORT_DIR = r'./IMTool app/system_files/Import/ARCHIVED/FAILED/'
BATCH_INSERT_LIMIT = 1000

LOG_DIR = r'./IMTool app/system_files/Log/'
# from CockroachDB_Connection import Database
# import json
# import os
# import numpy as np
# import pandas as pd

# db = Database(os.environ["DATABASE_URL"])

# result = db.select('stock',where='1=1 limit 1')

# print(json.loads(result.to_json(orient='records',date_format='iso')))

a = ['','None']

a = ["'null'" if item in ('','None') else item for item in a]

print(a)
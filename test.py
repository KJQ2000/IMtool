from CockroachDB_Connection import Database
import json
import os
import numpy as np
import pandas as pd

db = Database(os.environ["DATABASE_URL"])

result = db.select('stock',json=True)

print(result)
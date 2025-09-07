# from models import Database
import psycopg2
from psycopg2 import sql
import os
import dictionary as dic
import math

class BarcodeGenerator:
    def __init__(self):
        pass
        # self.conn = psycopg2.connect(database_url)
        # self.db = Database(database_url)

    def generate(self, gp, labor, unique_key):
        gp_code = self._gp_encryptor(float(gp))
        labor_code = self._labor_encryptor(float(labor))

        prefix = chr(64 + int(unique_key[:2])%26)
        
        unique_key = unique_key[-4:]

        return f"{prefix}{gp_code}{labor_code}{unique_key}"

    @staticmethod
    def _gp_encryptor(gp):
        gp = int(math.ceil(gp))
        """Encrypts the gp value."""
        gp_first_digit = int(str(gp)[0])
        return chr(64 + gp_first_digit) + str(gp)[1:]

    @staticmethod
    def _labor_encryptor(labor):
        """Encrypts the labor value."""
        labor = int(math.ceil(labor))
        # result = int(
        #     ''.join(
        #         str(int(x) + 1)[-1] if x.isdigit() else x for x in labor
        #     )
        # )
        return f"{labor:04}"
    
    # def get_uk(self):
    #     unique_key = self.db.select(
    #         table='metadata', 
    #         columns=['metadata_value'], 
    #         where="metadata_key='unique_key'"
    #     )[0].get('metadata_value')
        
    #     return unique_key
    
    # def update_uk(self,num=1):
    #     unique_key = int(self.db.select(
    #         table='metadata', 
    #         columns=['metadata_value'], 
    #         where="metadata_key='unique_key'"
    #     )[0].get('metadata_value'))
        
    #     unique_key += num
        
    #     unique_key = unique_key%10000
        
    #     unique_key = f"{unique_key:04}"
        
    #     self.db.update(table='metadata', set_columns= ['metadata_value'],set_values=[unique_key],where="metadata_key='unique_key'") 
        
    #     return None
    
# # Example usage
# if __name__ == "__main__":
#     database_url = os.environ["DATABASE_URL"]
#     barcode_gen = BarcodeGenerator(database_url)
#     gp = 375
#     labor = 280
#     barcode = barcode_gen.generate(gp, labor)
#     print('Barcode:',barcode)
#     barcode_gen.update_uk()


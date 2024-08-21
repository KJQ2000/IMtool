import os
import psycopg2
from psycopg2 import sql
import logging
import dictionary as dic
import numpy as np
from datetime import datetime
import pandas as pd
import json


SEQUENCES = {
    'users': dic.USER_SEQ,
    'booking': dic.BOOKING_SEQ,
    'customer': dic.CUSTOMER_SEQ,
    'stock': dic.STOCK_SEQ,
    'sale': dic.SALE_SEQ,
    'salesman': dic.SALESMAN_SEQ,
    'purchase': dic.PURCHASE_SEQ
}

PREFIX = {
    'users': 'USR',
    'booking': 'BOOK',
    'customer': 'CUST',
    'stock': 'STK',
    'sale': 'SALE',
    'salesman': 'SLM',
    'purchase': 'PUR'
}

log_file = dic.LOG_DIR + str(datetime.now().strftime("%Y_%m_%d")) + '.log'

logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Database:
    """
    A class to handle operations on a PostgreSQL database, including selecting, inserting, updating, and deleting records.
    
    Attributes:
        conn (psycopg2.extensions.connection): Connection to the PostgreSQL database.
        cursor (psycopg2.extensions.cursor): Cursor to execute database operations.
        schema (str): Schema name used for the database operations.
    
    Methods:
        select(table: str, columns: list = None, where: str = None, json: bool = False) -> pd.DataFrame or str:
            Selects data from a specified table and returns it as a DataFrame or JSON.
        
        insert(table: str, values: list, columns: list = None) -> None:
            Inserts a new record into a specified table.
        
        update(table: str, set_columns: list, set_values: list, where: str) -> None:
            Updates records in a specified table based on a condition.
        
        delete(table: str, where: str) -> None:
            Deletes records from a specified table based on a condition.
        
        get_nextval(sequence_name: str) -> int:
            Retrieves the next value from a specified sequence.
        
        batch_insert(table: str, values: list, columns: list = None) -> None:
            Inserts multiple records into a specified table in a single batch operation.
    
    """

    def __init__(self, database_url: str):
        """
        Initializes the Database class with a connection to the PostgreSQL database.
        
        Args:
            database_url (str): URL connection string for the PostgreSQL database.
        """
        self.conn = psycopg2.connect(database_url)
        self.cursor = self.conn.cursor()
        self.schema = 'konghin'

    def select(self, table: str, columns: list = None, where: str = None, js: bool = False):
        """
        Selects data from a specified table.

        Args:
            table (str): The table name from which to select data.
            columns (list, optional): List of column names to select. If None, selects all columns. Defaults to None.
            where (str, optional): SQL condition for filtering rows. Defaults to None.
            json (bool, optional): If True, returns the result as a JSON string. If False, returns as a DataFrame. Defaults to False.

        Returns:
            pd.DataFrame or str: A DataFrame of the selected data or a JSON string if json is True. Returns None if an error occurs.
        """
        if columns:
            query = sql.SQL("SELECT {columns} FROM {schema}.{table}").format(
                columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(table)
            )
        else:
            query = sql.SQL("SELECT * FROM {schema}.{table}").format(
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(table)
            )

        if where:
            query += sql.SQL(" WHERE {where}").format(where=sql.SQL(where))

        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            df = pd.DataFrame(np.array(results))
            colnames = [desc[0] for desc in self.cursor.description]
            df.columns = colnames
            logging.info(f"Successfully selected data from {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            if js:
                return json.loads(df.to_json(orient='records'))
            else:
                return df
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            return None

    def insert(self, table: str, values: list, columns: list = None) -> None:
        """
        Inserts a new record into a specified table.

        Args:
            table (str): The table name into which the data will be inserted.
            values (list): List of values to insert into the table.
            columns (list, optional): List of column names corresponding to the values. If None, inserts into all columns. Defaults to None.

        Returns:
            None
        """
        base_query = sql.SQL("INSERT INTO {schema}.{table}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table)
        )

        sequence_name = SEQUENCES.get(table.lower())

        if sequence_name is None:
            logging.error(f"Table not found. Please ensure you entered the correct table name.")
            self.conn.rollback()
            return None
        else:
            seq = self.get_nextval(sequence_name)

        pk = str(PREFIX.get(table)) + '_' + str(seq)

        if columns:
            query = base_query + sql.SQL(" ({id_col}, {columns}) VALUES ({id}, {values})").format(
                id_col=sql.Identifier(str(PREFIX.get(table)) + '_id'),
                columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
                id=sql.Placeholder(),
                values=sql.SQL(', ').join(sql.Placeholder() * len(values))
            )
        else:
            query = base_query + sql.SQL(" VALUES ({id}, {values})").format(
                id=sql.Placeholder(),
                values=sql.SQL(', ').join(sql.Placeholder() * len(values))
            )

        values = [pk] + values

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logging.info(f"Successfully inserted data into {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            logging.info(f"Values: {values}")
        except (psycopg2.Error, psycopg2.DatabaseError) as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()

    def update(self, table: str, set_columns: list, set_values: list, where: str) -> None:
        """
        Updates records in a specified table based on a condition.

        Args:
            table (str): The table name where the data will be updated.
            set_columns (list): List of column names to be updated.
            set_values (list): List of values to set for the corresponding columns.
            where (str): SQL condition to specify which records to update.

        Returns:
            None
        """
        set_clause = sql.SQL(', ').join(
            sql.SQL("{col} = {val}").format(col=sql.Identifier(col), val=sql.Placeholder())
            for col in set_columns
        )
        query = sql.SQL("UPDATE {schema}.{table} SET {set_clause} WHERE {where}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table),
            set_clause=set_clause,
            where=sql.SQL(where)
        )

        try:
            self.cursor.execute(query, set_values)
            self.conn.commit()
            logging.info(f"Successfully updated data in {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            logging.info(f"Values: {set_values}")
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()


    def delete(self, table: str, where: str) -> None:
        """
        Deletes records from a specified table based on a condition.

        This method executes a DELETE SQL statement to remove records from the given table that match the specified condition.
        After executing the statement, the changes are committed to the database.

        Args:
            table (str): The name of the table from which to delete records.
            where (str): The SQL condition used to specify which records to delete (e.g., "id = 5").

        Returns:
            None

        Raises:
            psycopg2.Error: If there is a database-related error (e.g., syntax error in the SQL statement).
            Exception: For any other unexpected errors during execution.

        Logs:
            - Success: Logs a message indicating successful deletion, including the executed SQL query.
            - Error: Logs detailed error information if the deletion fails, including the SQL query and the error details.
        """
        query = sql.SQL("DELETE FROM {schema}.{table} WHERE {where}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table),
            where=sql.SQL(where)
        )

        try:
            self.cursor.execute(query)
            self.conn.commit()
            logging.info(f"Successfully deleted data from {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()


    def get_nextval(self, sequence_name: str):
        """
        Retrieves the next value from a specified sequence.

        This method executes a SQL query to fetch the next value from the provided sequence. The sequence is used for generating unique identifiers.

        Args:
            sequence_name (str): The name of the sequence to get the next value from.

        Returns:
            int: The next value of the sequence. Returns None if there is an error.

        Raises:
            psycopg2.Error: If there is a database-related error (e.g., sequence does not exist).
            Exception: For any other unexpected errors during execution.

        Logs:
            - Success: Logs the next value of the sequence along with the query executed.
            - Error: Logs detailed error information if fetching the next value fails, including the query and the error details.
        """
        query = sql.SQL("SELECT nextval('{schema}.{seq}')").format(
            schema=sql.Identifier(dic.SCHEMA),
            seq=sql.Identifier(sequence_name)
        )

        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()[0]
            logging.info(f"Next value of sequence {sequence_name}: {result}")
            return result
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            return None


    def get_nextval(self, sequence_name: str):
        """
        Retrieves the next value from a specified sequence.

        This method executes a SQL query to fetch the next value from the provided sequence. The sequence is used for generating unique identifiers.

        Args:
            sequence_name (str): The name of the sequence to get the next value from.

        Returns:
            int: The next value of the sequence. Returns None if there is an error.

        Raises:
            psycopg2.Error: If there is a database-related error (e.g., sequence does not exist).
            Exception: For any other unexpected errors during execution.

        Logs:
            - Success: Logs the next value of the sequence along with the query executed.
            - Error: Logs detailed error information if fetching the next value fails, including the query and the error details.
        """
        query = sql.SQL("SELECT nextval('{schema}.{seq}')").format(
            schema=sql.Identifier(dic.SCHEMA),
            seq=sql.Identifier(sequence_name)
        )

        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()[0]
            logging.info(f"Next value of sequence {sequence_name}: {result}")
            return result
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            return None

    
    def __del__(self):
        """
        Destructor method to clean up database resources.

        This method closes the cursor and connection to the database when the Database object is destroyed.
        
        Returns:
            None

        Logs:
            - This method does not include logging, but it's important to ensure proper cleanup of resources.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    

if __name__ == '__main__':
    db = Database(os.environ["DATABASE_URL"])
    
#     # Example usage
    # db.insert(table='abcd', values=['kjunqiang@gmail.com', '11115354', 'JunQiang'])
#     # db.insert(table='users', values=['yckng00@gmail.com', '00121800', 'YinChew'])
#     # db.update('users', set_columns=['username'], set_values=['qwer'], where='id=3')
#     stock = db.select('stock')
#     print(pd.DataFrame(stock))
#     # db.select('users', columns=['username'], where='id=3')
#     # db.delete('users', where='id=3')
#     # db.batch_insert(table='users', values=[['abcd@gmail.com', '1234567', 'abcd'], ['efgh@gmail.com', 'abcdefg', 'efgh'], ['ijkl@gmail.com', 'abcd1234', 'abcdefgh1234']])
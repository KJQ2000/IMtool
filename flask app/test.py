# import os
# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

# engine = create_engine('cockroachdb://junqiang:e9W8uEXxKAljcwc4z3h5Xg@konghin-6756.6xw.aws-ap-southeast-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require')

# conn = engine.connect()

# metadata = MetaData()

# # Reflect the existing table schema from the database
# metadata.reflect(bind=engine)

# # Access the existing table
# users_table = metadata.tables['user']

# # # Define a table
# # users_table = Table(
# #     'users',  # Table name
# #     metadata,
# #     Column('id', Integer, primary_key=True),
# #     Column('name', String),
# #     Column('age', Integer)
# # )

# # Define the existing table
# users_table = Table('user', metadata, autoload=True, autoload_with=engine)

# # # Insert data into the table
# # insert_stmt = users_table.insert().values(name='Alice', age=25)
# # conn.execute(insert_stmt)

# # Select data from the table
# select_stmt = users_table.select()
# result = conn.execute(select_stmt).fetchall()
# print("All users:")
# for row in result:
#     print(row)

# # # Update data in the table
# # update_stmt = users_table.update().where(users_table.c.name == 'Alice').values(age=40,id=1)
# # conn.execute(update_stmt)

# # Close the connection
# conn.close()
import mysql.connector
from mysql.connector import Error

def create_database(host_name, user_name, user_password, database_name):
    connection = None
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            password=user_password
        )
        print("Connection to MySQL server successful")
        
        cursor = connection.cursor()
        # Create a new database
        cursor.execute(f"CREATE DATABASE {database_name}")
        print(f"Database '{database_name}' created successfully")
        
    except Error as e:
        print(f"Error: '{e}'")
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("MySQL connection closed")

# Usage
host_name = "localhost"
user_name = "konghin"  # Replace with your MySQL username
user_password = "konghin1928"  # Replace with your MySQL password
database_name = "konghin_IMT"

create_database(host_name, user_name, user_password, database_name)

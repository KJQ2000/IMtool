import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])

with conn.cursor() as cur:
    cur.execute("SELECT now()")
    res = cur.fetchall()
    conn.commit()
    print(res)

# import os
# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

# engine = create_engine('postgresql://junqiang:e9W8uEXxKAljcwc4z3h5Xg@konghin-6756.6xw.aws-ap-southeast-1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full')

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
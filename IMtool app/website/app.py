from flask import Flask, render_template, request
import os
import psycopg2
from psycopg2 import sql



app = Flask(__name__)

conn = psycopg2.connect(os.environ["DATABASE_URL"])

def authenticate(email,password):

    with conn.cursor() as cur:
        query = sql.SQL("SELECT * FROM konghin.users WHERE email = %s AND password = %s;")
        cur.execute(query, (email,password))
        res = cur.fetchone()
        conn.commit()
        return True


@app.route("/")
def home():
    return render_template("login.html")
    
@app.route('/login', methods=['POST'])
def login():

    username = request.form['email']
    password = request.form['password']
    if authenticate(username, password)==True:
        return f"Welcome, {username}!"
    else:
        return "Invalid credentials, please try again."

if __name__ == "__main__":
    app.run(debug=True)

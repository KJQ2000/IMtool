from flask import Flask, render_template, request
import os
import psycopg2
from psycopg2 import sql
from models import User


app = Flask(__name__)

conn = psycopg2.connect(os.environ["DATABASE_URL"])


@app.route("/")
def home():
    return render_template("login.html")
    
@app.route('/login', methods=['POST'])
def login():
    username = request.form['email']
    password = request.form['password']
    user = User(conn)
    if user.authenticate(username, password)==True:
        return render_template("base.html")
    else:
        return "Invalid credentials, please try again."

if __name__ == "__main__":
    app.run(debug=True)

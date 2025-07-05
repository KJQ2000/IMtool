from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, flash, jsonify
import os, re, logging
from datetime import datetime
import psycopg2
from psycopg2 import sql
from models import Database
import dictionary as dic
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess
from barcode import BarcodeGenerator
from werkzeug.datastructures import ImmutableMultiDict
import pandas as pd
import numpy as np
from decimal import Decimal
from werkzeug.datastructures import MultiDict

load_dotenv()

ALLOWED_EXTENSIONS = {'csv','xlsx'}

app = Flask(__name__)
app.secret_key = b'k0ngh1n888'

# flask_env_python = r'C:\Users\keong\anaconda3\envs\flask_env\python.exe'

log_file = dic.LOG_DIR+str(datetime.now().strftime("%Y_%m_%d"))+'.log'

# Set the folder for uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['CURRENT_DIR'] = dic.CURRENT_DIR

logging.basicConfig(filename=log_file,level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# conn = psycopg2.connect(os.environ["DATABASE_URL"])
# db = Database(os.environ["DATABASE_URL"])

conn = psycopg2.connect(os.environ["DEV_DATABASE_URL"])
db = Database(os.environ["DEV_DATABASE_URL"])

@app.route("/")
def home():
    return render_template("login.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        if authenticate(email, password)==True:
            session['loggedin'] = True
            session['email'] = email
            logging.info(f"{email} successfully login at {datetime.now()}")
            stocks = db.select('stock', js=True)
            # logging.info(stocks)
            # stocks =[('STK_100001', 'Bracelet', Decimal('12.8'), Decimal('14.5'), None, Decimal('120'), None, datetime.date(2024, 1, 1), None, Decimal('345'), None, 'IN STOCK', None, 'cartier', '916')]
            if stocks:
                return render_template("stocks.html", stocks=stocks)
            return render_template("stocks.html")
        else:
            msg = "Incorrect username/password!"
            return render_template("login.html", msg=msg)
    else:
        return render_template("login.html", msg='')

def authenticate(email, password):

    with conn.cursor() as cur:
        query = sql.SQL("SELECT * FROM konghin.users WHERE usr_email = %s AND usr_password = %s;")
        cur.execute(query, (email,password))
        res = cur.fetchone()
        conn.commit()
        
        if res:
            # username = res[3]
            return True
        else:
            return False
            

def logout():
    # Remove session data, this will log the user out
   logging.info(f"{session['email']} logout at {datetime.now()}")
   
   session.pop('loggedin', None)
   session.pop('email', None)
   
   # Redirect to login page
   return redirect('login.html')

# this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'username' in request.form:
        # Create variables for easy access
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        with conn.cursor() as cur:
            query = sql.SQL("SELECT * FROM konghin.users WHERE usr_email = %s;")
            cur.execute(query, (email, ))
            res = cur.fetchone()

            # If account exists show error and validation checks
            if res:
                # msg = 'Account already exists!'
                flash('Account already exists!', category='warning')
                return render_template('register.html')
                
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                # msg = 'Invalid email address!'
                flash('Invalid email address!', category='warning')
                return render_template('register.html')
            
            elif not re.match(r'[A-Za-z0-9]+', username):
                # msg = 'Username must contain only characters and numbers!'
                flash('Username must contain only characters and numbers!', category='warning')
                return render_template('register.html')
            
            elif not username or not password or not email:
                # msg = 'Please fill out the form!'
                flash('Please fill out the form!', category='warning')
                return render_template('register.html')
            else:
                # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
                cur.execute('INSERT INTO konghin.users VALUES (%s, %s, %s, %s)', ('asd', email, password, username,))
                conn.commit()
                flash('Account created! Please proceed to login page to login.', category='success')
                return render_template('register.html')
                # msg = 'You have successfully registered!'

        
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

        # if user:
        #     flash('Email already exists.', category='error')
        # elif len(email) < 4:
        #     flash('Email must be greater than 3 characters.', category='error')
        # elif len(first_name) < 2:
        #     flash('First name must be greater than 1 character.', category='error')
        # elif password1 != password2:
        #     flash('Passwords don\'t match.', category='error')
        # elif len(password1) < 7:
        #     flash('Password must be at least 7 characters.', category='error')
        # else:
        #     new_user = User(email=email, first_name=first_name, password=generate_password_hash(
        #         password1, method='sha256'))
        #     db.session.add(new_user)
        #     db.session.commit()
        #     login_user(new_user, remember=True)
        #     flash('Account created!', category='success')
        #     return redirect(url_for('views.home'))

@app.route("/stocks")
def stocks():
    # stocks as default home page
    if 'loggedin' in session:
        stocks = db.select('stock', js=True)
        # print(stocks)
        if stocks:
            return render_template("stocks.html", stocks=stocks)
        return render_template("stocks.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/stocks/<category>/<pattern>", methods=["GET", "POST"])
def stocksFilter(category, pattern):
    # Check if the user is logged in
    if 'loggedin' in session:
        # Handle the POST request
        if request.method == "POST":
            if category and pattern:
                stocks = db.select(table='stock', where="stk_type='{category}' AND stk_pattern='{pattern}'".format(category=category, pattern=pattern), js=True)

                # Check if stocks exist after filtering
                if stocks:
                    return render_template("stocks.html", stocks=stocks)
                else:
                    return render_template("stocks.html", message="No stocks found for the given criteria.")
        
        # Default GET request, fetch all stocks
        stocks = db.select('stock', js=True)
        if stocks:
            return render_template("stocks.html", stocks=stocks)

        return render_template("stocks.html", message="No stocks available.")
    
    # User is not logged in, redirect to the login page
    return redirect('login.html')

# @app.route("/addstocks")
# def addstocks():
#     # stocks as default home page
#     if 'loggedin' in session:
#         return render_template("addstocks.html")

#     # User is not loggedin redirect to login page
#     return redirect('login.html')

@app.route('/add-stocks', methods=['GET', 'POST'])
def add_stock():
    if 'loggedin' in session:
        if request.method == 'POST':
            # print(list(request.form.keys()))
            # print(list(request.form.values()))

            # do here ... get the pur_date for the pur_id from purchase table to input into the stock table
            # stk_pur_date
            try:
                db.insert(table='stock',columns=list(request.form.keys()),values=list(request.form.values()))
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            stocks = db.select('stock', js=True)
            if stocks:
                return render_template("stocks.html", stocks=stocks)
            return render_template("stocks.html")
        
        purchases = db.select('purchase', js=True)
        # update the logic to get the latest created at 
        latest_purchase = db.select(table='purchase',columns=['pur_id', 'pur_date'],where='1=1 order by pur_created_at desc limit 1',js=True)[0]
        # latest_purchase = Purchase.objects.order_by('-created_at').first()

        return render_template("addstocks.html", purchases=purchases, latest_purchase=latest_purchase)
    return redirect('login.html')
    
@app.route('/update-stock/<stock_id>', methods=['GET'])
def edit_stock(stock_id):
    if 'loggedin' in session:
        stock = db.select('stock', where="stk_id='{stk_id}'".format(stk_id=stock_id),js=True)
        purchases = db.select('purchase', js=True)
        if stock[0]['stk_pur_date']:
            pur_date_object = datetime.fromisoformat(stock[0].get('stk_pur_date').replace('Z', '+00:00'))
            # datetime.fromisoformat(pur_date_string.replace('Z', '+00:00'))
            stock[0]['stk_pur_date'] = pur_date_object.strftime('%Y-%m-%d')
        if stock[0]['stk_sell_date']:
            sale_date_object = datetime.fromisoformat(stock[0].get('stk_sell_date').replace('Z', '+00:00'))
            stock[0]['stk_sell_date'] = sale_date_object.strftime('%Y-%m-%d')
        # if stock[0]['stk_book_date']:
        #     sale_date_object = datetime.fromisoformat(stock[0].get('stk_book_date').replace('Z', '+00:00'))
        #     stock[0]['stk_book_date'] = sale_date_object.strftime('%Y-%m-%d')
        return render_template('updatestock.html', stock=stock[0], purchases=purchases)
    return redirect('login.html')

@app.route('/updatestock', methods=['POST'])
def update_stock_view():
    # print(request.form)
    if 'loggedin' in session:
        try:
            # do here ..., if the pur_id has updated then need to get the new pur_date from purchase table and update in stock table
            db.update(table='stock',set_columns=list(request.form.keys()),set_values=list(request.form.values()), where="stk_id='{stk_id}'".format(stk_id=request.form['stk_id']))
        except ValueError:
            return "Invalid input. Please check your data and try again.", 400
        stocks = db.select('stock', js=True)
        if stocks:
            return render_template("stocks.html", stocks=stocks)
        return render_template("stocks.html")
    return redirect('login.html')

@app.route('/delete/<stock_id>', methods=['POST'])
def deletestock(stock_id):
    # stk_id = request.form.get('stk_id')
    stk_id = stock_id
    if stk_id:
        # Your logic to delete the product with the given stk_id
        # Example:
        # product = Product.query.filter_by(stk_id=stk_id).first()
        # if product:
        #     db.session.delete(product)
        #     db.session.commit()
        
        # After deletion, redirect to the stocks page or any other appropriate page
        db.delete('stock',where="stk_id='{stk_id}'".format(stk_id=stk_id))
        stocks = db.select('stock', js=True)
        if stocks:
            return render_template("stocks.html", stocks=stocks)
        return render_template("stocks.html")
    return 'Stock ID is missing', 400

@app.route('/batch-import-stock', methods=['GET', 'POST'])
def uploadFile():
    if request.method == 'POST':
        f = request.files.get('file')
 
        data_filename = secure_filename(f.filename)
 
        f.save(os.path.join(dic.IMPORT_DIR,data_filename))
 
        session['uploaded_data_file_path'] = os.path.join(dic.IMPORT_DIR,data_filename)
        result = subprocess.run(['python', dic.PY_IMPORT_FILE], capture_output=True, text=True)
        # Log outputs
        logging.info("STOCK IMPORT STDOUT:\n%s", result.stdout)
        if result.stderr:
            logging.error("STOCK IMPORT STDERR:\n%s", result.stderr)
        logging.info("STOCK IMPORT RETURN CODE: %s", result.returncode)
        stocks = db.select('stock', js=True)
        if stocks:
            return render_template("stocks.html", stocks=stocks)
        return render_template("stocks.html")
    return 'FAILED'

@app.route('/batch-import-purchase', methods=['GET', 'POST'])
def uploadPurchaseFile():
    if request.method == 'POST':
        f = request.files.get('file')
 
        data_filename = secure_filename(f.filename)
 
        f.save(os.path.join(dic.IMPORT_DIR,data_filename))
 
        session['uploaded_data_file_path'] = os.path.join(dic.IMPORT_DIR,data_filename)
        result = subprocess.run(['python', dic.PY_IMPORT_FILE], capture_output=True, text=True)
        # Log outputs
        logging.info("PURCHASE IMPORT STDOUT:\n%s", result.stdout)
        if result.stderr:
            logging.error("PURCHASE IMPORT STDERR:\n%s", result.stderr)
        logging.info("PURCHASE IMPORT RETURN CODE: %s", result.returncode)
        purchases = db.select('purchase', js=True)
        if purchases:
            return render_template("purchases.html", purchases=purchases)
        return render_template("purchases.html")
    return 'FAILED'

@app.route('/your-endpoint', methods=['POST'])
def handle_data():
    data = request.json
    return jsonify({"status": "success", "data": data})

@app.route("/purchases")
def purchases():
    if 'loggedin' in session:
        purchases = db.select('purchase', js=True)
        if purchases:
            return render_template("purchases.html", purchases=purchases)
        return render_template("purchases.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/addpurchases")
def addpurchases():
    if 'loggedin' in session:
        return render_template("addpurchases.html")

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/add-purchases", methods = ['GET', 'POST'])
def add_purchases():
    if 'loggedin' in session:
        if request.method == 'POST':
            # perform add purchase
            try:
                form_dict = request.form.to_dict()
                cash_amt = (form_dict.get('pur_total_cash_amt', 0))
                trade_in_amt = (form_dict.get('pur_total_trade_in_amt', 0))
                total_amt = (form_dict.get('pur_total_amt', 0))

                if cash_amt:
                    pass
                else:
                    cash_amt = 0

                if trade_in_amt:
                    pass
                else:
                    trade_in_amt = 0

                if total_amt:
                    pass
                else:
                    total_amt = 0
                
                if float(cash_amt) + float(trade_in_amt) >= float(total_amt):
                    form_dict['pur_payment_status'] = 'PAID'
                elif float(cash_amt) + float(trade_in_amt) == 0:
                    form_dict['pur_payment_status'] = 'NOT PAID'
                else:
                    form_dict['pur_payment_status'] = 'IN PAYMENT'
                
                new_form = MultiDict(form_dict)

                # Step 3: Convert it back to MultiDict
                new_form = MultiDict(form_dict)
                db.insert(table='purchase',columns=list(new_form.keys()),values=list(new_form.values()))
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            purchases = db.select('purchase', js=True)
            if purchases:
                return render_template("purchases.html", purchases=purchases)
            return render_template("purchases.html")

        # else fetch salesman data
        salesmen = db.select(table="salesman", js=True)
        return render_template("addpurchases.html", salesmen=salesmen)

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/update-purchase/<pur_id>', methods=['GET'])
def edit_purchase(pur_id):
    if 'loggedin' in session:
        purchase = db.select('purchase', where="pur_id='{pur_id}'".format(pur_id=pur_id),js=True)
        if purchase[0]['pur_date']:
            pur_date_object = datetime.fromisoformat(purchase[0].get('pur_date').replace('Z', '+00:00'))
            # datetime.fromisoformat(pur_date_string.replace('Z', '+00:00'))
            purchase[0]['pur_date'] = pur_date_object.strftime('%Y-%m-%d')
        if purchase[0]['pur_billing_date']:
            pur_billing_date_object = datetime.fromisoformat(purchase[0].get('pur_billing_date').replace('Z', '+00:00'))
            purchase[0]['pur_billing_date'] = pur_billing_date_object.strftime('%Y-%m-%d')
        salesmen = db.select(table="salesman", js=True)
        return render_template('updatepurchase.html', purchase=purchase[0], salesmen=salesmen)
    return redirect('login.html')

@app.route('/updatepurchase', methods=['POST'])
def update_purchase_view():
    # print(request.form)
    # print(request.form['pur_id'])
    if 'loggedin' in session:
        try:
            form_dict = request.form.to_dict()
            cash_amt = (form_dict.get('pur_total_cash_amt', 0))
            trade_in_amt = (form_dict.get('pur_total_trade_in_amt', 0))
            total_amt = (form_dict.get('pur_total_amt', 0))

            if cash_amt:
                pass
            else:
                cash_amt = 0

            if trade_in_amt:
                pass
            else:
                trade_in_amt = 0

            if total_amt:
                pass
            else:
                total_amt = 0
            
            if float(cash_amt) + float(trade_in_amt) >= float(total_amt):
                form_dict['pur_payment_status'] = 'PAID'
            elif float(cash_amt) + float(trade_in_amt) == 0:
                form_dict['pur_payment_status'] = 'NOT PAID'
            else:
                form_dict['pur_payment_status'] = 'IN PAYMENT'
            
            new_form = MultiDict(form_dict)
            db.update(table='purchase',set_columns=list(new_form.keys()),set_values=list(new_form.values()), where="pur_id='{pur_id}'".format(pur_id=request.form['pur_id']))
        except Exception as e:
            return e
            # return "Invalid input. Please check your data and try again.", 400
        purchases = db.select('purchase', js=True)
        if purchases:
            return render_template("purchases.html", purchases=purchases)
        return render_template("purchases.html")
    return redirect('login.html')

@app.route('/delete-purchase/<pur_id>', methods=['POST'])
def deletepurchase(pur_id):
    if pur_id:
        db.delete('purchase',where="pur_id='{pur_id}'".format(pur_id=pur_id))
        purchases = db.select('purchase', js=True)
        if purchases:
            return render_template("purchases.html", purchases=purchases)
        return render_template("purchases.html")
    return 'Purchase ID is missing', 400

@app.route("/sales")
def sales():
    if 'loggedin' in session:
        sales = db.select('sale', js=True)
        if sales:
            return render_template("sales.html", sales=sales)
        return render_template("sales.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/add-sales", methods = ['GET','POST'])
def add_sales():
    if 'loggedin' in session:
        if request.method == 'POST':
            # perform add salesman
            try:
                db.insert(table='sale',columns=list(request.form.keys()),values=list(request.form.values()))

                # get data from sale table
                keys_needed = ['sale_sold_date', 'sale_gold_sell', 'sale_labor_sell']
                update_dict = {key:request.form[key] for key in keys_needed}
                key_changes = {'sale_sold_date': 'stk_sell_date', 'sale_gold_sell': 'stk_gold_sell','sale_labor_sell': 'stk_labor_sell'}
                new_update_dict = {key_changes.get(k, k): v for k, v in update_dict.items()}
                
                # Temporarily set as this stock id
                # stk_id = 'STK_100004'
                stk_id = request.form.get('stk_id')
                stk_data = db.select('stock', columns=['stk_weight','stk_gold_cost','stk_labor_cost'], where=f"stk_id='{stk_id}'")
                
                # calculate profit
                sold_price = request.form.get('sale_price')
                stk_profit = float(sold_price) - ((float(stk_data[0]['stk_weight'])*float(stk_data[0]['stk_gold_cost']))+float(stk_data[0]['stk_labor_cost']))
                
                # add needed data to dictionary
                new_update_dict['stk_status'] = 'SOLD'
                new_update_dict['stk_profit'] = stk_profit
                new_update_dict['stk_sale_id'] = str('SALE_'+str(db.get_currval(dic.SALE_SEQ)))
                db.update(table = 'stock',set_columns=list(new_update_dict.keys()),set_values=list(new_update_dict.values()), where=f"stk_id='{stk_id}'")
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            sales = db.select('sale', js=True)
            if sales:
                return render_template("sales.html", sales=sales)
            return render_template("sales.html")

        customers = db.select('customer', js=True)
        stocks = db.select('stock', where="stk_status='IN STOCK'", js=True)
        return render_template("addsales.html", customers=customers, stocks=stocks, stockIds="stk01")

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/update-sale/<sale_id>', methods=['GET', 'POST'])
def edit_sale(sale_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            try:
                # Get data from the form
                stk_ids = request.form.getlist('stk_id')
                sale_gold_sell = request.form.getlist('sale_gold_sell')
                sale_labor_sell = request.form.getlist('sale_labor_sell')
                sale_weight = request.form.getlist('sale_weight')
                sale_price = request.form.getlist('sale_price')
                
                sum_dict = {
                    'sale_labor_sell_total': sum(float(value) for value in sale_labor_sell if value.strip()),
                    'sale_weight_total': sum(float(value) for value in sale_weight if value.strip()),
                    'sale_price_total': sum(float(value) for value in sale_price if value.strip())
                }

                # print(request.form.keys())

                # print('sale_official_receipt:',request.form['sale_official_receipt'])
                # print('sale_cust_id:',request.form['sale_cust_id'])
                # print('sale_receipt_no:',request.form['sale_receipt_no'])
                # print('sale_sold_date:',request.form['sale_sold_date'])
                # print('stk_ids:',stk_ids)
                # print('sale_gold_sell:',sale_gold_sell)
                # print('sale_labor_sell:',sale_labor_sell)
                # print('sale_weight:',sale_weight)
                # print('sale_price:',sale_price)
                
                # reset old stocks to in stock if its been removed from update sale
                old_stk_ids = list(map(lambda x: x['stk_id'], db.select(table='stock',columns=['stk_id'],where="stk_sale_id='{sale_id}'".format(sale_id = sale_id),js=True)))
                new_stk_id = set(stk_ids)
                result = [item for item in old_stk_ids if item not in new_stk_id]
                
                if len(result)>0:
                    for stockID in result:
                        db.update(table='stock',set_columns=['stk_status','stk_sale_id','stk_weight_sell','stk_labor_sell','stk_gold_sell','stk_sell_date','stk_profit'],set_values=['IN STOCK',None,None,None,None,None,None],where="stk_id='{stk_id}'".format(stk_id = stockID))

                # update sale table
                db.update(table='sale',set_columns=['sale_receipt_no','sale_cust_id','sale_sold_date','sale_labor_sell','sale_gold_sell','sale_price','sale_weight','sale_official_receipt']
                        ,set_values=[request.form['sale_receipt_no'],request.form['sale_cust_id'],request.form['sale_sold_date'],sum_dict['sale_labor_sell_total'],sale_gold_sell[0],sum_dict['sale_price_total'],sum_dict['sale_weight_total'],request.form['sale_official_receipt']],
                        where="sale_id='{sale_id}'".format(sale_id=sale_id))
                
                # update stock table to SOLD status
                for i in range(len(stk_ids)):
                    db.cursor.execute(f"select stk_weight*stk_gold_cost+stk_labor_cost from konghin.stock where stk_id = '{stk_ids[i]}'")
                    cost = float(db.cursor.fetchone()[0])
                    profit = (float(sale_weight[i])*float(sale_gold_sell[i])+float(sale_labor_sell[i]))-cost
            
                    
                    db.update(table='stock'
                            ,set_columns=['stk_status','stk_sale_id','stk_weight_sell','stk_labor_sell','stk_gold_sell','stk_sell_date','stk_profit']
                            ,set_values=['SOLD',sale_id,sale_weight[i],sale_labor_sell[i],sale_gold_sell[i],request.form['sale_sold_date'],float(profit)]
                            ,where="stk_id='{stk_id}'".format(stk_id = stk_ids[i]))
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            sales = db.select('sale', js=True)
            if sales:
                return render_template("sales.html", sales=sales)
            return render_template("sales.html")
        else:
            sale = db.select('sale', where="sale_id='{sale_id}'".format(sale_id=sale_id),js=True)
            
            if sale[0]['sale_sold_date']:
                sale_date_object = datetime.fromisoformat(sale[0].get('sale_sold_date').replace('Z', '+00:00'))
                sale[0]['sale_sold_date'] = sale_date_object.strftime('%Y-%m-%d')
            customers = db.select(table="customer", js=True)
            stock_entries = db.select('stock', where="stk_sale_id='{sale_id}'".format(sale_id=sale_id),js=True)
            
            for i in range(len(stock_entries)):
                stock_entries[i]['sale_price'] = (stock_entries[i]['stk_gold_sell']*stock_entries[i]['stk_weight_sell']) + stock_entries[i]['stk_labor_sell']

            sold_stk_ids = [item['stk_id'] for item in stock_entries]
            joined_ids = ', '.join(f"'{stk_id}'" for stk_id in sold_stk_ids)
            stocks = db.select('stock', where=f"stk_status='IN STOCK' OR stk_id IN ({joined_ids})", js=True)
            return render_template('updatesale.html', sale=sale[0], customers=customers, stocks=stocks, stock_entries=stock_entries)

    return redirect('login.html')


@app.route('/delete-sale/<sale_id>', methods=['POST'])
def deletesale(sale_id):
    if sale_id:
        db.delete('sale',where="sale_id='{sale_id}'".format(sale_id=sale_id))
        sales = db.select('sale', js=True)
        if sales:
            return render_template("sales.html", sales=sales)
        return render_template("sales.html")
    return 'Sale ID is missing', 400

@app.route("/salesmen")
def salesmen():
    # stocks as default home page
    if 'loggedin' in session:
        salesmen = db.select('salesman', js=True)
        if salesmen:
            return render_template("salesmen.html", salesmen=salesmen)
        return render_template("salesmen.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/add-salesman", methods = ['GET','POST'])
def add_salesman():
    if 'loggedin' in session:
        if request.method == 'POST':
            # perform add salesman
            try:
                db.insert(table='salesman',columns=list(request.form.keys()),values=list(request.form.values()))
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            salesmen = db.select('salesman', js=True)
            if salesmen:
                return render_template("salesmen.html", salesmen=salesmen)
            return render_template("salesmen.html")

        return render_template("addsalesmen.html")

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/update-salesman/<slm_id>', methods=['GET'])
def edit_salesman(slm_id):
    if 'loggedin' in session:
        salesman = db.select('salesman', where="slm_id='{slm_id}'".format(slm_id=slm_id),js=True)

        return render_template('updatesalesman.html', salesman=salesman[0])
    return redirect('login.html')

@app.route('/updatesalesman', methods=['POST'])
def update_salesman_view():
    if 'loggedin' in session:
        try:
            db.update(table='salesman',set_columns=list(request.form.keys()),set_values=list(request.form.values()), where="slm_id='{slm_id}'".format(slm_id=request.form['slm_id']))
        except ValueError:
            return "Invalid input. Please check your data and try again.", 400
        salesmen = db.select('salesman', js=True)
        if salesmen:
            return render_template("salesmen.html", salesmen=salesmen)
        return render_template("salesmen.html")
    return redirect('login.html')

@app.route('/delete-salesman/<slm_id>', methods=['POST'])
def deletesalesman(slm_id):
    if slm_id:
        db.delete('salesman',where="slm_id='{slm_id}'".format(slm_id=slm_id))
        salesmen = db.select('salesman', js=True)
        if salesmen:
            return render_template("salesmen.html", salesmen=salesmen)
        return render_template("salesmen.html")
    return 'Salesman ID is missing', 400

@app.route("/customers")
def customers():
    # stocks as default home page
    if 'loggedin' in session:
        customers = db.select('customer', js=True)
        if customers:
            return render_template("customers.html", customers=customers)
        return render_template("customers.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/add-customer", methods = ['GET','POST'])
def add_customer():
    if 'loggedin' in session:
        if request.method == 'POST':
            # perform add salesman
            # print(request.form)
            try:
                db.insert(table='customer',columns=list(request.form.keys()),values=list(request.form.values()))
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            customers = db.select('customer', js=True)
            if customers:
                return render_template("customers.html", customers=customers)
            return render_template("customers.html")

        return render_template("addcustomers.html")

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/update-customer/<cust_id>', methods=['GET'])
def edit_customer(cust_id):
    if 'loggedin' in session:
        customers = db.select('customer', where="cust_id='{cust_id}'".format(cust_id=cust_id),js=True)

        return render_template('updatecustomer.html', customer=customers[0])
    return redirect('login.html')

@app.route('/updatecustomer', methods=['POST'])
def update_customer_view():
    if 'loggedin' in session:
        try:
            db.update(table='customer',set_columns=list(request.form.keys()),set_values=list(request.form.values()), where="cust_id='{cust_id}'".format(cust_id=request.form['cust_id']))
        except ValueError:
            return "Invalid input. Please check your data and try again.", 400
        customers = db.select('customer', js=True)
        if customers:
            return render_template("customers.html", customers=customers)
        return render_template("customers.html")
    return redirect('login.html')

@app.route('/delete-customer/<cust_id>', methods=['POST'])
def deletecustomer(cust_id):
    if cust_id:
        db.delete('customer',where="cust_id='{cust_id}'".format(cust_id=cust_id))
        customers = db.select('customer', js=True)
        if customers:
            return render_template("customers.html", customers=customers)
        return render_template("customers.html")
    return 'Customer ID is missing', 400

@app.route("/bookings")
def bookings():
    # stocks as default home page
    if 'loggedin' in session:
        bookings = db.select('booking', js=True)
        if bookings:
            return render_template("bookings.html", bookings=bookings)
        return render_template("bookings.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/add-booking", methods = ['GET','POST'])
def add_booking():
    if 'loggedin' in session:
        if request.method == 'POST':
            # perform add booking

            # print(request.form)
            # Define the specific fields you want to insert into the database
            stk_ids = request.form.getlist('stk_id')
            book_gold_prices = request.form.getlist('stk_gold_book')
            book_labor_prices = request.form.getlist('stk_labor_book')
            book_weights = request.form.getlist('stk_weight_book')
            stk_book_prices = request.form.getlist('stk_book_price')
            
            
            sum_dict = {
                'book_labor_price_total': sum(float(value) for value in book_labor_prices if value.strip()),
                'book_weight_total': sum(float(value) for value in book_weights if value.strip()),
                'book_price_total': sum(float(value) for value in stk_book_prices if value.strip())
            }
            fields_to_insert_to_booking_table = ['book_cust_id', 'book_receipt_no', 'book_date', 'book_gold_price', 'book_labor_price', 'book_weight' ,'book_price', 'book_remaining']
            
            # Extract the values for the specified fields
            # values_to_insert = [request.form[field] for field in fields_to_insert_to_booking_table]
            values_to_insert = []
            for field in fields_to_insert_to_booking_table:
                if field == 'book_gold_price':
                    values_to_insert.append(request.form['stk_gold_book'])
                elif field not in ['book_labor_price', 'book_weight', 'book_price']:
                    values_to_insert.append(request.form[field])
                else:
                    values_to_insert.append(sum_dict[f"{field}_total"])
                        
            # add book_status
            fields_to_insert_to_booking_table.append('book_status')
            values_to_insert.append('BOOKED')
            # Insert the data into the booking table
            
            try:
                # insert all information to booking table
                db.insert(table='booking', columns=fields_to_insert_to_booking_table, values=values_to_insert)
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            
            # add first payment record to book payment table


            # edit here: update the book_id in stock table, change the stock status to "BOOKED" not "IN STOCK"
            
            booking_id = 'BOOK_'+ str(db.get_currval(dic.BOOKING_SEQ))
  
            # Define the mapping
            key_mapping = {
                'bp_payment': 'bp_payment',
                'book_date': 'bp_payment_date',
                'booking_id': 'bp_book_id'
            }

            # Retrieve data from the form
            form_data = request.form.to_dict()

            # Transform the data using the mapping
            payment_data = {
                new_key: form_data[old_key] 
                for old_key, new_key in key_mapping.items() 
                if old_key in form_data
            }
            payment_data['bp_book_id'] = booking_id
            payment_data['bp_status'] = 'PAID'

            try:
                # insert book payment table (bp_payment, bp_payment_date, bp_book_id, bp_last_update?, bp_created_at?)
                db.insert(table='book_payment',columns=list(payment_data.keys()),values=list(payment_data.values()))

            except ValueError:
                return "Invalid input. Please check your data and try again.", 400

            # # do ...
            for i in range(len(stk_ids)):
                try:
                    stock_data = {
                                    'stk_gold_book':book_gold_prices[i],
                                    'stk_labor_book':book_labor_prices[i],
                                    'stk_weight_book':book_weights[i],
                                    'stk_book_price':stk_book_prices[i],
                                    'stk_status':'BOOKED',
                                    'stk_book_id':booking_id
                                }
                    # update stock table (stk_gold_sell, stk_labor_sell, stk_status, stk_book_id)
                    db.update(table='stock',set_columns=list(stock_data.keys()),set_values=list(stock_data.values()),where=f"stk_id='{stk_ids[i]}'")

                except ValueError:
                    return "Invalid input. Please check your data and try again.", 400
            
            bookings = db.select('booking', js=True)
            if bookings:
                return render_template("bookings.html", bookings=bookings)
            return render_template("bookings.html")

        customers = db.select('customer', js=True)
        stocks = db.select('stock', where="stk_status='IN STOCK'", js=True)
        return render_template("addbookings.html", customers=customers, stocks=stocks)

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/update-booking/<book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            # Get data from the form
            stk_ids = request.form.getlist('stk_id')
            stk_gold_book = request.form.getlist('stk_gold_book')
            stk_labor_book = request.form.getlist('stk_labor_book')
            stk_weight_book = request.form.getlist('stk_weight_book')
            stk_book_price = request.form.getlist('stk_book_price')
                        
            # print('book_cust_id',request.form['book_cust_id'])
            # print('book_receipt_no:',request.form['book_receipt_no'])
            # print('book_date:',request.form['book_date'])
            # print('stk_ids:',stk_ids)
            # print('sale_gold_book:',stk_gold_book)
            # print('sale_labor_sell:',stk_labor_book)
            # print('sale_weight:',stk_weight_book)
            # print('sale_price:',stk_book_price)
            
            # reset old stocks to in stock if its been removed from update booking
            old_stk_ids = list(map(lambda x: x['stk_id'], db.select(table='stock',columns=['stk_id'],where="stk_book_id='{book_id}'".format(book_id = book_id),js=True)))
            new_stk_id = set(stk_ids)
            result = [item for item in old_stk_ids if item not in new_stk_id]
            
            for stockID in result:
                db.update(table='stock',set_columns=['stk_status','stk_book_id','stk_weight_book','stk_labor_book','stk_gold_book','stk_book_price'],set_values=['IN STOCK',None,None,None,None,None],where="stk_id='{stk_id}'".format(stk_id = stockID))


            # update booking table
            sum_dict = {
                'book_labor_price': sum(float(value) for value in stk_labor_book if value.strip()),
                'book_weight': sum(float(value) for value in stk_weight_book if value.strip()),
                'book_price': sum(float(value) for value in stk_book_price if value.strip())
            }
            
            db.cursor.execute(f"select sum(bp_payment) from konghin.book_payment where bp_book_id = '{book_id}'")
            bp_sum = float(db.cursor.fetchone()[0])
            
            book_remaining = sum_dict['book_price'] - bp_sum

            
            db.update(table='booking',set_columns=['book_gold_price','book_labor_price','book_weight','book_price','book_cust_id','book_receipt_no','book_remaining']
                      ,set_values=[stk_gold_book[0],sum_dict['book_labor_price'],sum_dict['book_weight'],sum_dict['book_price'],request.form['book_cust_id'],request.form['book_receipt_no'],book_remaining],
                      where="book_id='{book_id}'".format(book_id=book_id))
            
            # update stock table to BOOKED status
            for i in range(len(stk_ids)):
                db.update(table='stock'
                          ,set_columns=['stk_status','stk_book_id','stk_weight_book','stk_labor_book','stk_gold_book','stk_book_price']
                          ,set_values=['BOOKED',book_id,stk_weight_book[i],stk_labor_book[i],stk_gold_book[i],stk_book_price[i]]
                          ,where="stk_id='{stk_id}'".format(stk_id = stk_ids[i]))
            
            bookings = db.select('booking', js=True)
            if bookings:
                return render_template("bookings.html", bookings=bookings)
            return render_template("bookings.html")
        else:
            booking = db.select('booking', where="book_id='{book_id}'".format(book_id=book_id),js=True)
            if booking[0]['book_date']:
                book_date_object = datetime.fromisoformat(booking[0].get('book_date').replace('Z', '+00:00'))
                # datetime.fromisoformat(pur_date_string.replace('Z', '+00:00'))
                booking[0]['book_date'] = book_date_object.strftime('%Y-%m-%d')
            customers = db.select(table="customer", js=True)
            # stocks = db.select(table="stock", js=True)
            stock_entries = db.select('stock', where="stk_book_id='{book_id}'".format(book_id=book_id),js=True)
            booked_stk_ids = [item['stk_id'] for item in stock_entries]
            joined_ids = ', '.join(f"'{stk_id}'" for stk_id in booked_stk_ids)
            stocks = db.select('stock', where=f"stk_status='IN STOCK' OR stk_id IN ({joined_ids})", js=True)

            return render_template('updatebooking.html', booking=booking[0], customers=customers, stocks=stocks, stock_entries=stock_entries)
    return redirect('login.html')

@app.route('/delete-booking/<book_id>', methods=['POST'])
def deletebooking(book_id):
    if book_id:
        db.delete('booking',where="book_id='{book_id}'".format(book_id=book_id))
        bookings = db.select('booking', js=True)
        if bookings:
            return render_template("bookings.html", bookings=bookings)
        return render_template("bookings.html")
    return 'Book ID is missing', 400

@app.route("/bookpayments")
def bookpayments():
    # stocks as default home page
    if 'loggedin' in session:
        
        return render_template("bookpayments.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/book-bookpayment/<book_id>", methods = ['GET'])
def book_bookpayments(book_id):
    if 'loggedin' in session:
        bookpayments = db.select('book_payment', where="bp_book_id='{book_id}'".format(book_id=book_id), js=True)
        bookings = db.select('booking', where="book_id='{book_id}'".format(book_id=book_id), js=True)
        
        if bookpayments:
            return render_template("bookpayments.html", bookpayments=bookpayments, bookings=bookings)
        return render_template("bookpayments.html", bookings=bookings)
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/add-bookpayment/<book_id>", methods = ['GET', 'POST'])
def add_bookpayments(book_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            # do ... need to update new_booking_payment to booking table and add one more row to to booking payment table with book id and update the book payment_status to completed 
            # bookpayments = db.select('book_payment', where="bp_book_id='{book_id}'".format(book_id=book_id), js=True)
            # if bookpayments:
            #     return render_template("bookpayments.html", bookpayments=bookpayments)
            
            # add book payment table
            # print(request.form)
            
            bp_payment_date = request.form.get('bp_payment_date')
            bp_payment = request.form.get('bp_payment')
            new_book_remaining = request.form.get('new_book_remaining')
            # book_remaining = request.form.get('book_remaining')
            # print(book_id)
            # print(new_book_remaining)

            db.insert(table='book_payment',columns=['bp_payment','bp_book_id','bp_payment_date','bp_status'],values=[float(bp_payment),book_id,bp_payment_date,'PAID'])
            
            # update booking table
            db.update(table='booking',set_columns=['book_remaining'],set_values=[int(float(new_book_remaining))],where=f"book_id='{book_id}'")
            
            bookpayments = db.select('book_payment', where="bp_book_id='{book_id}'".format(book_id=book_id), js=True)
            bookings = db.select('booking', where="book_id='{book_id}'".format(book_id=book_id), js=True)
            
            if bookpayments:
                return render_template("bookpayments.html", bookpayments=bookpayments, bookings=bookings)
            
        bookings = db.select('booking', where="book_id='{book_id}'".format(book_id=book_id), js=True)
        if bookings:
            return render_template("addbookpayment.html", bookings=bookings)
        return render_template("addbookpayment.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/cancel-bookpayment/<bp_book_id>/<bp_id>', methods=['POST'])
def cancelbookpayment(bp_book_id, bp_id):
    if bp_id:

        db.update(table = 'book_payment',set_columns=['bp_status'],set_values=['CANCELLED'],where=f"bp_id = '{bp_id}'")
        old_rem_price = float(db.select(table='booking',columns=['book_remaining'],where=f"book_id='{bp_book_id}'")[0]['book_remaining'])
        book_payment_price = float(db.select(table='book_payment',columns=['bp_payment'],where=f"bp_id = '{bp_id}'")[0]['bp_payment'])
        new_rem_price = old_rem_price+book_payment_price
        db.update(table='booking',set_columns=['book_remaining','book_status'],set_values=[new_rem_price,'BOOKED'],where=f"book_id='{bp_book_id}'")
        
        
        bookpayments = db.select('book_payment', where= f"bp_book_id ='{bp_book_id}'", js=True)
        bookings = db.select('booking', where="book_id='{book_id}'".format(book_id=bp_book_id), js=True)
        if bookpayments:
            return render_template("bookpayments.html", bookpayments=bookpayments, bookings=bookings)
        return render_template("bookpayments.html", bookings=bookings)
    return 'Book Payment ID is missing', 400

@app.route('/cancel-booking/<book_id>', methods=['POST'])
def cancelbooking(book_id):
    if book_id:
        # do ...
        # update all book payments to cancelled
        # update the booking to cancelled
        bookings = db.select('booking', js=True)
        if bookings:
            return render_template("bookings.html", bookings=bookings)
        return render_template("bookings.html")
    return 'Book ID is missing', 400

@app.route('/close-booking/<book_id>', methods=['GET'])
def closebookpayment(book_id):    
    remaining = float(db.select(table='booking',columns=['book_remaining'],where=f"book_id='{book_id}'")[0]['book_remaining'])
    
    # add book payment
    db.insert(table='book_payment',columns=['bp_payment','bp_book_id','bp_payment_date','bp_status'],values=[remaining,book_id,datetime.now(),'PAID'])
    
    # update booking table
    db.update(table='booking',set_columns= ['book_remaining','book_status'], set_values= [0,'COMPLETED'],where=f"book_id='{book_id}'")
    
    bookings = db.select('booking', where="book_id='{book_id}'".format(book_id=book_id), js=True)
    customers = db.select(table="customer", js=True)
    stock_entries = db.select('stock', where="stk_book_id='{book_id}'".format(book_id=book_id))
    for i in range(len(stock_entries)):
        stock_entries[i]['sale_price'] = (stock_entries[i]['stk_gold_book']*stock_entries[i]['stk_weight_book']) + stock_entries[i]['stk_labor_book']
    booked_stk_ids = [item['stk_id'] for item in stock_entries]
    joined_ids = ', '.join(f"'{stk_id}'" for stk_id in booked_stk_ids)
    stocks = db.select('stock', where=f"stk_status='IN STOCK' OR stk_id IN ({joined_ids})", js=True)
    return render_template('addsales(booking).html', booking=bookings[0], customers=customers, stocks=stocks, stock_entries=stock_entries)

@app.route('/submit_sale', methods=['POST'])
def submit_sale():
    # Get data from the form
    stk_ids = request.form.getlist('stk_id')
    sale_gold_sell = request.form.getlist('sale_gold_sell')
    sale_labor_sell = request.form.getlist('sale_labor_sell')
    sale_weight = request.form.getlist('sale_weight')
    sale_price = request.form.getlist('sale_price')
    sum_dict = {
        'sale_labor_sell_total': sum(float(value) for value in sale_labor_sell if value.strip()),
        'sale_weight_total': sum(float(value) for value in sale_weight if value.strip()),
        'sale_price_total': sum(float(value) for value in sale_price if value.strip())
    }
    columns = ['sale_official_receipt', 'sale_cust_id', 'sale_receipt_no', 'sale_sold_date', 'sale_gold_sell', 'sale_labor_sell', 'sale_weight', 'sale_price']
    values = []
    
    # prepare data for sale table
    for key in columns:
        if key not in ['sale_labor_sell', 'sale_weight', 'sale_price']:
            values.append(request.form[key])
        else:
            values.append(sum_dict[f"{key}_total"])
            
    try:
        db.insert(table='sale',columns=columns,values=values)
        # get data from sale table
        
        for i in range(len(stk_ids)):
            
            stk_dict = {
                'stk_sell_date':request.form['sale_sold_date'],
                'stk_gold_sell':sale_gold_sell[i],
                'stk_labor_sell':sale_labor_sell[i],
                'stk_weight_sell':sale_weight[i],
            }
            stk_data = db.select('stock', columns=['stk_weight','stk_gold_cost','stk_labor_cost'], where=f"stk_id='{stk_ids[i]}'")
            # calculate profit
            sold_price = sale_price[i]
            stk_profit = float(sold_price) - ((float(stk_data[0]['stk_weight'])*float(stk_data[0]['stk_gold_cost']))+float(stk_data[0]['stk_labor_cost']))
            
            # add needed data to dictionary
            stk_dict['stk_status'] = 'SOLD'
            stk_dict['stk_profit'] = stk_profit
            stk_dict['stk_sale_id'] = str('SALE_'+str(db.get_currval(dic.SALE_SEQ)))
            
            # print(i)
            # print(stk_dict)
            
            db.update(table = 'stock',set_columns=list(stk_dict.keys()),set_values=list(stk_dict.values()), where=f"stk_id='{stk_ids[i]}'")
            
            # print('sold_price:',sold_price)
            # print('stk_weight:',float(stk_data[0]['stk_weight']))
            # print('stk_gold_cost:',float(stk_data[0]['stk_gold_cost']))
            # print('stk_labor_cost:',float(stk_data[0]['stk_labor_cost']))
            # print(stk_profit)
            # print(stk_dict)
            
    except ValueError:
        return "Invalid input. Please check your data and try again.", 400
    
    sales = db.select('sale', js=True)
    if sales:
        return render_template("sales.html", sales=sales)
    return render_template("sales.html")

@app.route("/dashboard")
def dashboard():
    # stocks as default home page
    if 'loggedin' in session:
        # categories = db.select('category_pattern_mapping',js=True)
        categories = [
            {'cpat_category': 'NECKLACE', 'cpat_image_path': '.\static\pattern\goldnecklace.jpg'},
            {'cpat_category': 'RING', 'cpat_image_path': '.\static\pattern\goldring.jpg'},
            {'cpat_category': 'BRACELET', 'cpat_image_path': '.\static\pattern\goldbracelet.jpg'},
            {'cpat_category': 'BANGLE', 'cpat_image_path': '.\static\pattern\goldbangle.jpg'},
            {'cpat_category': 'EARING', 'cpat_image_path': '.\static\pattern\goldearing.jpg'},
            {'cpat_category': 'PENDANT', 'cpat_image_path': '.\static\pattern\goldpendant.jpg'},
            {'cpat_category': 'ANKLET', 'cpat_image_path': '.\static\pattern\goldanklet.jpg'}
            # Add more patterns as needed
        ]
        return render_template("dashboard.html", categories=categories)
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/add-pattern", methods=["GET", "POST"])
def add_pattern():
    if 'loggedin' in session:
        if request.method == "POST":
            
            image = request.files['cpat_image_path']
            # Check if file is valid
            if image and allowed_file(image.filename):
                # Secure the filename
                filename = secure_filename(image.filename)
                imageName = request.form['cpat_category']+'_'+request.form['cpat_pattern']+'.'+image.filename.rsplit('.', 1)[1].lower()
                image_path = os.path.join(dic.IMG_STORE_DIR, imageName)
                
                # Save the image to the uploads folder
                image.save(image_path)
                
                img_path_to_insert = f'\static\pattern\{imageName}'
                
                columns_to_insert = list(request.form.keys())
                columns_to_insert.extend(request.files.keys())
                values_to_insert  = list(request.form.values())
                values_to_insert.append(img_path_to_insert)

                try:
                    db.insert(table='category_pattern_mapping',columns=columns_to_insert,values=values_to_insert)
                except ValueError:
                    return "Invalid input. Please check your data and try again.", 400
                    
        return render_template("patterns.html")
    
    # If not logged in, redirect to login page
    return redirect('/login')

@app.route("/view-category/<category>", methods = ['POST'])
def view_category(category):
    if category:
        patterns = db.select('category_pattern_mapping',where="cpat_category='{category}'".format(category=category))
        return render_template("patternsDashboard.html", patterns=patterns)
    return 'Category is missing', 400
    
@app.route("/patterns")
def patterns():
    # stocks as default home page
    if 'loggedin' in session:
        patterns = db.select('category_pattern_mapping',js=True)
        # patterns = [
        #     {'cpat_id': '1', 'category': 'Necklace', 'pattern': '水波', 'image': 'static/img/goldnecklace.jpg'},
        #     {'cpat_id': '2', 'category': 'Necklace', 'pattern': '单扣', 'image': 'static/img/pattern2.jpg'},
        #     {'cpat_id': '3', 'category': 'Necklace', 'pattern': '通单扣', 'image': 'static/img/pattern3.jpg'},
        #     # Add more patterns as needed
        # ]
        if patterns:
            return render_template("patterns.html", patterns=patterns)
        return render_template("patterns.html")
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/update-pattern/<pattern_id>', methods=['GET'])
def edit_pattern(pattern_id):
    
    if 'loggedin' in session:
        pattern = db.select('category_pattern_mapping', where="cpat_id='{ptn_id}'".format(ptn_id=pattern_id),js=True)
        # print(pattern[0])

        return render_template('updatepattern.html', pattern=pattern[0])
    return redirect('login.html')

@app.route('/updatepattern', methods=['POST'])
def update_pattern_view():
    # print(request.form)
    if 'loggedin' in session:
        try:
            # Replace image
            image = request.files['cpat_image_path']
            # print("image.filename:",image.filename)
            # Check if file is valid
            if image and allowed_file(image.filename):
                # old_image_path = list(db.select(table='category_pattern_mapping',columns=['cpat_image_path'],where="cpat_id='{cpat_id}'".format(cpat_id=request.form['cpat_id']),js=True)[0].values())[0]
                # os.remove(old_image_path)
                
                # Secure the filename
                filename = secure_filename(image.filename)
                imageName = request.form['cpat_category']+'_'+request.form['cpat_pattern']+'.'+image.filename.rsplit('.', 1)[1].lower()
                image_path_save = os.path.join(dic.IMG_STORE_DIR, imageName)
                # image_path_store = os.path.join('static','pattern', imageName)
                
                image_path_store = f'\static\pattern\{imageName}'
                
                # Save the image to the uploads folder
                image.save(image_path_save)
                
                db.update(table='category_pattern_mapping',set_columns=['cpat_image_path'],set_values=[image_path_store],where = "cpat_id='{cpat_id}'".format(cpat_id=request.form['cpat_id']))             
                # print(image_path)

        except ValueError:
            return "Invalid input. Please check your data and try again.", 400
        patterns = db.select('category_pattern_mapping', js=True)
        return render_template("patterns.html", patterns=patterns)
    return redirect('login.html')

@app.route('/delete-pattern/<cpat_id>', methods=['POST'])
def deletepattern(cpat_id):
    if cpat_id:
        db.delete('category_pattern_mapping',where="cpat_id='{cpat_id}'".format(cpat_id=cpat_id))
        patterns = db.select('category_pattern_mapping', js=True)
        if patterns:
            return render_template("patterns.html", patterns=patterns)
        return render_template("patterns.html")
    return 'CPAT ID is missing', 400

@app.route('/post-export-data', methods=['POST'])
def handle_export_data():
    try:
        data=request.get_json()
        print(data)
        
    except Exception as e:
        print(e)
    stocks = db.select('stock', js=True)
    if stocks:
        return render_template("stocks.html", stocks=stocks)
    return render_template("stocks.html")

@app.route('/process-barcode-data', methods=['POST'])
def process_barcode_data():
    data=request.get_json()
    processed_data = []
    barcode_export = pd.DataFrame(data)
    stk_id_to_convert = str(barcode_export['Stock ID'].to_list())[1:-1]
    
    # print(stk_id_to_convert)
    
    query = """
        SELECT 
            stk.stk_id,
            stk.stk_barcode,
            stk.stk_weight,
            COALESCE(stk.stk_length, stk.stk_size) AS stk_length_size,
            stk.stk_returned,
            slm.slm_name,
            '''' || TO_CHAR(p.pur_date, 'MMYY') AS stk_pur_monthyear
        FROM konghin.stock stk
        LEFT JOIN konghin.purchase p ON stk.stk_pur_id = p.pur_id
        LEFT JOIN konghin.salesman slm ON p.pur_slm_id = slm.slm_id
        WHERE stk.stk_id IN ({stk_id})
    """.format(stk_id=stk_id_to_convert)  # Parameterized query
    
    # print(query)

    processed_data = db.select_raw(query).to_dict(orient='records')
    
    # processed_data = barcode_export[['Stock ID','Stock Barcode', 'Stock Weight (g)','Stock Size','Stock Length (cm)','Stock Returned']].to_json(orient='records')
    
    db.update(table='stock',set_columns=['stk_printed'],set_values=['1'],where = "stk_id in ({stk_id})".format(stk_id=stk_id_to_convert))

    processed_data = list(processed_data)
    
    # print('\n\n\n PROCESSED DATA \n\n\n')
    # print(processed_data)

    return jsonify({'status': 'success', 'data': processed_data}), 200
    
# @app.route('/print-invoice/<sale_id>', methods=['GET'])
# def print_invoice(sale_id):
#     # Fetch sale details and stock entries from the database
#     # sale = get_sale_by_id(sale_id)  # Replace with actual logic to get sale from the database
#     # stock_entries = get_stock_entries_by_sale_id(sale_id)  # Replace with actual logic to get stock entries
#     print('\n\nsale id\n\n')
#     print(sale_id)

#     sale = db.select(table='sale', where=f"sale_id='{sale_id}'")
#     if sale[0]['sale_sold_date']:
#         sale_date_object = datetime.fromisoformat(sale[0].get('sale_sold_date').replace('Z', '+00:00'))
#         sale[0]['sale_sold_date'] = sale_date_object.strftime('%Y-%m-%d')
#     customer = db.select(table="customer", where="cust_id='{sale_cust_id}'".format(sale_cust_id=sale[0]["sale_cust_id"])) 
#     print(sale[0]["sale_cust_id"])
#     print(sale_id)
#     print(customer)
#     query = f"""
#             select 
#             stk_id,
#             CONCAT(stk_type, ' ', stk_pattern, ' ', COALESCE(stk_length::STRING, stk_size::STRING)) as sale_desc,
#             stk_gold_sell , 
#             stk_labor_sell ,
#             stk_weight_sell, 
#             stk_gold_sell * stk_weight_sell + stk_labor_sell as sale_price 
#             from konghin.stock where stk_sale_id='{sale_id}'
#         """

#     stock_entries = db.select_raw(query)
#     print('\n\nstock_entries\n\n')
#     print(stock_entries)
#     # stock_entries = db.select('stock', where="stk_sale_id='{sale_id}'".format(sale_id=sale_id))
#     # for i in range(len(stock_entries)):
#     #     stock_entries[i]['sale_price'] = (stock_entries[i]['stk_gold_sell']*stock_entries[i]['stk_weight_sell']) + stock_entries[i]['stk_labor_sell']

#     # sold_stk_ids = [item['stk_id'] for item in stock_entries]
#     # joined_ids = ', '.join(f"'{stk_id}'" for stk_id in sold_stk_ids)
#     # stocks = db.select('stock', where=f"stk_status='IN STOCK' OR stk_id IN ({joined_ids})", js=True)
#     # return render_template('updatesale.html', sale=sale[0], customers=customers, stocks=stocks, stock_entries=stock_entries)

#     # Render the invoice template
#     # return render_template('invoice.html', sale=sale[0], stock_entries=stock_entries)
#     return render_template('invoice.html', sale=sale[0], stock_entries=stock_entries, customer=customer)

@app.route('/print-invoice/<sale_id>', methods=['GET'])
def print_invoice(sale_id):
    # Fetch sale details and stock entries from the database
    # sale = get_sale_by_id(sale_id)  # Replace with actual logic to get sale from the database
    # stock_entries = get_stock_entries_by_sale_id(sale_id)  # Replace with actual logic to get stock entries
    
    sale = db.select('sale', where="sale_id='{sale_id}'".format(sale_id=sale_id),js=True)
    if sale[0]['sale_sold_date']:
        sale_date_object = datetime.fromisoformat(sale[0].get('sale_sold_date').replace('Z', '+00:00'))
        sale[0]['sale_sold_date'] = sale_date_object.strftime('%Y-%m-%d')
    customer = db.select(table="customer", where="cust_id='{sale_cust_id}'".format(sale_cust_id=sale[0]["sale_cust_id"]), js=True) 
    query = f"""
            select 
            stk_id,
            CONCAT(stk_type, ' ', stk_pattern, ' ', COALESCE(stk_length::STRING, stk_size::STRING)) as sale_desc,
            stk_gold_sell , 
            stk_labor_sell ,
            stk_weight_sell, 
            stk_gold_sell * stk_weight_sell + stk_labor_sell as sale_price 
            from konghin.stock where stk_sale_id='{sale_id}'
        """

    stock_entries = list(db.select_raw(query).to_dict(orient='records'))
    # print('\n\nstock_entries select raw\n\n')
    # print(stock_entries)
    # print(type(stock_entries))

    # stock_entries = db.select('stock', where="stk_sale_id='{sale_id}'".format(sale_id=sale_id))
    # for i in range(len(stock_entries)):
    #     stock_entries[i]['sale_price'] = (stock_entries[i]['stk_gold_sell']*stock_entries[i]['stk_weight_sell']) + stock_entries[i]['stk_labor_sell']
    
    # print('\n\nstock_entries\n\n')
    # print(stock_entries)
    # print(type(stock_entries))
    # return render_template('updatesale.html', sale=sale[0], customers=customers, stocks=stocks, stock_entries=stock_entries)

    # Render the invoice template
    return render_template('invoice.html', sale=sale[0], stock_entries=stock_entries, customer=customer[0])


if __name__ == "__main__":
    app.run(debug=True)

# stk_returned, stk_tag
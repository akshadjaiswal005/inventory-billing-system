from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3, os, secrets
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('SHOPSTOCK_DB', os.path.join(BASE_DIR, 'shopstock.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret-key')


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','cashier')));
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE NOT NULL, name TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0), quantity INTEGER NOT NULL CHECK(quantity >= 0), tax_rate REAL NOT NULL DEFAULT 0 CHECK(tax_rate >= 0 AND tax_rate <= 100), low_stock_threshold INTEGER NOT NULL DEFAULT 5 CHECK(low_stock_threshold >= 0), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_no TEXT UNIQUE NOT NULL, cashier_id INTEGER NOT NULL REFERENCES users(id), subtotal REAL NOT NULL, tax_total REAL NOT NULL, total REAL NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS bill_items(id INTEGER PRIMARY KEY AUTOINCREMENT, bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE, product_id INTEGER REFERENCES products(id), product_name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price REAL NOT NULL, tax_rate REAL NOT NULL, line_subtotal REAL NOT NULL, line_tax REAL NOT NULL, line_total REAL NOT NULL);
        ''')
        count = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if count == 0:
            con.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', ('admin', generate_password_hash('Admin@123'), 'admin'))
            con.execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', ('cashier', generate_password_hash('Cashier@123'), 'cashier'))
        if con.execute('SELECT COUNT(*) FROM products').fetchone()[0] == 0:
            con.executemany('INSERT INTO products(sku,name,price,quantity,tax_rate,low_stock_threshold) VALUES(?,?,?,?,?,?)', [
                ('SKU-1001','Notebook',50,100,0,10), ('SKU-1002','Ball Pen',10,200,0,20), ('SKU-1003','Water Bottle',120,25,18,5)])


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            if request.path.startswith('/api/'):
                return jsonify(error='Authentication required'), 401
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if session.get('role') not in roles:
                if request.path.startswith('/api/'):
                    return jsonify(error='Insufficient permissions'), 403
                flash('You do not have permission to perform that action.', 'error')
                return redirect(url_for('dashboard'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def wants_json():
    return request.path.startswith('/api/') or request.is_json

@app.after_request
def security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'same-origin')
    return response

@app.route('/')
def index():
    return redirect(url_for('dashboard') if session.get('user_id') else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        with db() as con:
            user = con.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'], session['username'], session['role'] = user['id'], user['username'], user['role']
            flash('Welcome back, ' + user['username'] + '!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    with db() as con:
        products = con.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        low = con.execute('SELECT COUNT(*) FROM products WHERE quantity <= low_stock_threshold').fetchone()[0]
        sales = con.execute("SELECT COALESCE(SUM(total),0) FROM bills WHERE date(created_at)=date('now','localtime')").fetchone()[0]
        bills = con.execute("SELECT COUNT(*) FROM bills WHERE date(created_at)=date('now','localtime')").fetchone()[0]
        recent = con.execute('SELECT b.*,u.username FROM bills b JOIN users u ON u.id=b.cashier_id ORDER BY b.id DESC LIMIT 5').fetchall()
    return render_template('dashboard.html', products=products, low=low, sales=sales, bills=bills, recent=recent)

@app.route('/products')
@login_required
def products_page():
    q = request.args.get('q','').strip()
    with db() as con:
        products = con.execute('SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? ORDER BY name', (f'%{q}%',f'%{q}%')).fetchall()
    return render_template('products.html', products=products, q=q)

@app.route('/products/new', methods=['GET','POST'])
@roles_required('admin')
def product_new():
    if request.method == 'POST':
        data = request.form
        try:
            sku, name = data.get('sku','').strip(), data.get('name','').strip()
            price, qty, tax, threshold = float(data.get('price','')), int(data.get('quantity','')), float(data.get('tax_rate','0')), int(data.get('low_stock_threshold','5'))
            if not sku or not name or price < 0 or qty < 0 or not 0 <= tax <= 100 or threshold < 0: raise ValueError()
            with db() as con:
                con.execute('INSERT INTO products(sku,name,price,quantity,tax_rate,low_stock_threshold) VALUES(?,?,?,?,?,?)', (sku,name,price,qty,tax,threshold))
            flash('Product added successfully.', 'success'); return redirect(url_for('products_page'))
        except sqlite3.IntegrityError:
            flash('SKU must be unique.', 'error')
        except (ValueError, TypeError):
            flash('Enter valid product details. Price, quantity and threshold cannot be negative; tax must be 0–100.', 'error')
    return render_template('product_form.html', product=None)

@app.route('/products/<int:product_id>/edit', methods=['GET','POST'])
@roles_required('admin')
def product_edit(product_id):
    with db() as con: product = con.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone()
    if not product: flash('Product not found.','error'); return redirect(url_for('products_page'))
    if request.method == 'POST':
        d=request.form
        try:
            vals=(d.get('sku','').strip(),d.get('name','').strip(),float(d.get('price','')),int(d.get('quantity','')),float(d.get('tax_rate','0')),int(d.get('low_stock_threshold','5')))
            if not vals[0] or not vals[1] or vals[2]<0 or vals[3]<0 or not 0<=vals[4]<=100 or vals[5]<0: raise ValueError()
            with db() as con: con.execute('UPDATE products SET sku=?,name=?,price=?,quantity=?,tax_rate=?,low_stock_threshold=? WHERE id=?',(*vals,product_id))
            flash('Product updated.','success'); return redirect(url_for('products_page'))
        except sqlite3.IntegrityError: flash('SKU must be unique.','error')
        except (ValueError,TypeError): flash('Invalid product details.','error')
    return render_template('product_form.html', product=product)

@app.route('/products/<int:product_id>/delete', methods=['POST'])
@roles_required('admin')
def product_delete(product_id):
    with db() as con:
        # Preserve historical bill line items by preventing deletion of referenced products.
        used=con.execute('SELECT COUNT(*) FROM bill_items WHERE product_id=?',(product_id,)).fetchone()[0]
        if used:
            flash('This product is referenced by a bill and cannot be deleted. Set its quantity to zero instead.','error')
        else:
            cur=con.execute('DELETE FROM products WHERE id=?',(product_id,))
            flash('Product deleted.' if cur.rowcount else 'Product not found.','success' if cur.rowcount else 'error')
    return redirect(url_for('products_page'))

@app.route('/inventory')
@login_required
def inventory_page():
    with db() as con: products=con.execute('SELECT * FROM products ORDER BY quantity ASC,name').fetchall()
    return render_template('inventory.html', products=products)

@app.route('/billing', methods=['GET','POST'])
@roles_required('admin','cashier')
def billing_page():
    with db() as con: products=con.execute('SELECT * FROM products WHERE quantity>0 ORDER BY name').fetchall()
    if request.method=='POST':
        try:
            raw=request.form.get('items','[]')
            import json
            items=json.loads(raw)
            if not isinstance(items,list) or not items: raise ValueError('Add at least one item.')
            subtotal=tax_total=0.0; calculated=[]
            with db() as con:
                # Validate all lines and stock before making any inventory changes.
                for item in items:
                    pid=int(item.get('product_id')); qty=int(item.get('quantity'))
                    if qty<=0: raise ValueError('Quantity must be positive.')
                    p=con.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
                    if not p: raise ValueError('Product not found.')
                    if p['quantity']<qty: raise ValueError(f"Insufficient stock for {p['name']}.")
                    line_sub=round(p['price']*qty,2); line_tax=round(line_sub*p['tax_rate']/100,2); line_total=round(line_sub+line_tax,2)
                    subtotal+=line_sub; tax_total+=line_tax
                    calculated.append((p,qty,line_sub,line_tax,line_total))
                receipt='RCT-'+datetime.now().strftime('%Y%m%d%H%M%S')+'-'+secrets.token_hex(2).upper()
                cur=con.execute('INSERT INTO bills(receipt_no,cashier_id,subtotal,tax_total,total) VALUES(?,?,?,?,?)',(receipt,session['user_id'],round(subtotal,2),round(tax_total,2),round(subtotal+tax_total,2)))
                bill_id=cur.lastrowid
                for p,qty,ls,lt,tot in calculated:
                    con.execute('INSERT INTO bill_items(bill_id,product_id,product_name,quantity,unit_price,tax_rate,line_subtotal,line_tax,line_total) VALUES(?,?,?,?,?,?,?,?,?)',(bill_id,p['id'],p['name'],qty,p['price'],p['tax_rate'],ls,lt,tot))
                    con.execute('UPDATE products SET quantity=quantity-? WHERE id=?',(qty,p['id']))
            flash('Bill created: '+receipt,'success'); return redirect(url_for('bill_detail',bill_id=bill_id))
        except (ValueError, TypeError, KeyError) as e: flash(str(e) or 'Invalid bill data.','error')
        except Exception: app.logger.exception('Bill creation failed'); flash('Could not create bill. Check input and try again.','error')
    return render_template('billing.html', products=products)

@app.route('/bills')
@roles_required('admin')
def bills_page():
    with db() as con: bills=con.execute('SELECT b.*,u.username FROM bills b JOIN users u ON u.id=b.cashier_id ORDER BY b.id DESC').fetchall()
    return render_template('bills.html', bills=bills)

@app.route('/bills/<int:bill_id>')
@login_required
def bill_detail(bill_id):
    with db() as con:
        bill=con.execute('SELECT b.*,u.username FROM bills b JOIN users u ON u.id=b.cashier_id WHERE b.id=?',(bill_id,)).fetchone()
        items=con.execute('SELECT * FROM bill_items WHERE bill_id=?',(bill_id,)).fetchall()
    if not bill: flash('Bill not found.','error'); return redirect(url_for('dashboard'))
    if session.get('role')!='admin' and bill['cashier_id']!=session.get('user_id'):
        flash('You can only view bills you created.','error'); return redirect(url_for('dashboard'))
    return render_template('bill_detail.html', bill=bill, items=items)

@app.route('/reports')
@roles_required('admin')
def reports_page():
    period=request.args.get('period','daily')
    date_filter={'daily':"date(created_at)=date('now','localtime')",'weekly':"date(created_at)>=date('now','-6 days','localtime')",'monthly':"strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime')"}.get(period)
    if not date_filter: period='daily'; date_filter="date(created_at)=date('now','localtime')"
    with db() as con:
        summary=con.execute(f'SELECT COUNT(*) bills, COALESCE(SUM(subtotal),0) subtotal, COALESCE(SUM(tax_total),0) tax, COALESCE(SUM(total),0) total FROM bills WHERE {date_filter}').fetchone()
        top=con.execute('SELECT product_name,SUM(quantity) quantity,SUM(line_total) revenue FROM bill_items GROUP BY product_name ORDER BY quantity DESC LIMIT 5').fetchall()
    return render_template('reports.html', period=period, summary=summary, top=top)

# REST API endpoints used by Postman. JSON APIs share the same SQLite data.
@app.route('/api/products', methods=['GET'])
@login_required
def api_products():
    with db() as con: rows=con.execute('SELECT * FROM products ORDER BY id').fetchall()
    return jsonify([dict(r) for r in rows]), 200

@app.route('/api/products/<int:product_id>', methods=['GET','PUT','DELETE'])
@roles_required('admin')
def api_product_detail(product_id):
    with db() as con: p=con.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone()
    if not p: return jsonify(error='Product not found'),404
    if request.method=='GET': return jsonify(dict(p)),200
    if request.method=='DELETE':
        with db() as con:
            if con.execute('SELECT COUNT(*) FROM bill_items WHERE product_id=?',(product_id,)).fetchone()[0]: return jsonify(error='Product is referenced by a bill'),409
            con.execute('DELETE FROM products WHERE id=?',(product_id,))
        return '',204
    data=request.get_json(silent=True) or {}
    try:
        sku=str(data.get('sku',p['sku'])).strip(); name=str(data.get('name',p['name'])).strip(); price=float(data.get('price',p['price'])); quantity=int(data.get('quantity',p['quantity'])); tax=float(data.get('tax_rate',p['tax_rate'])); threshold=int(data.get('low_stock_threshold',p['low_stock_threshold']))
        if not sku or not name or price<0 or quantity<0 or not 0<=tax<=100 or threshold<0: raise ValueError()
        with db() as con: con.execute('UPDATE products SET sku=?,name=?,price=?,quantity=?,tax_rate=?,low_stock_threshold=? WHERE id=?',(sku,name,price,quantity,tax,threshold,product_id))
        with db() as con: updated=con.execute('SELECT * FROM products WHERE id=?',(product_id,)).fetchone()
        return jsonify(dict(updated)),200
    except sqlite3.IntegrityError: return jsonify(error='SKU must be unique'),409
    except (ValueError,TypeError): return jsonify(error='Invalid product fields'),400

@app.route('/api/products', methods=['POST'])
@roles_required('admin')
def api_product_create():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return jsonify(error='JSON object required'),400
    try:
        sku=str(data.get('sku','')).strip(); name=str(data.get('name','')).strip(); price=float(data.get('price')); quantity=int(data.get('quantity')); tax=float(data.get('tax_rate',0)); threshold=int(data.get('low_stock_threshold',5))
        if not sku or not name or price<0 or quantity<0 or not 0<=tax<=100 or threshold<0: raise ValueError()
        with db() as con:
            cur=con.execute('INSERT INTO products(sku,name,price,quantity,tax_rate,low_stock_threshold) VALUES(?,?,?,?,?,?)',(sku,name,price,quantity,tax,threshold)); pid=cur.lastrowid
            p=con.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
        return jsonify(dict(p)),201
    except sqlite3.IntegrityError: return jsonify(error='SKU must be unique'),409
    except (ValueError,TypeError): return jsonify(error='Invalid or missing product fields'),400

@app.route('/api/inventory/low-stock', methods=['GET'])
@roles_required('admin','cashier')
def api_low_stock():
    with db() as con: rows=con.execute('SELECT * FROM products WHERE quantity<=low_stock_threshold ORDER BY quantity').fetchall()
    return jsonify([dict(r) for r in rows]),200

@app.route('/api/bills', methods=['GET','POST'])
@roles_required('admin','cashier')
def api_bills():
    if request.method=='GET':
        with db() as con: rows=con.execute('SELECT id,receipt_no,cashier_id,subtotal,tax_total,total,created_at FROM bills ORDER BY id DESC').fetchall()
        return jsonify([dict(r) for r in rows]),200
    data=request.get_json(silent=True) or {}; items=data.get('items')
    if not isinstance(items,list) or not items: return jsonify(error='items must be a non-empty array'),400
    subtotal=tax_total=0.0; calculated=[]
    try:
        with db() as con:
            for item in items:
                pid=int(item['product_id']); qty=int(item['quantity'])
                if qty<=0: raise ValueError('Quantity must be positive')
                p=con.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
                if not p: raise ValueError('Product not found')
                if p['quantity']<qty: raise RuntimeError('Insufficient stock for '+p['name'])
                ls=round(p['price']*qty,2); lt=round(ls*p['tax_rate']/100,2); total=round(ls+lt,2)
                subtotal+=ls; tax_total+=lt; calculated.append((p,qty,ls,lt,total))
            receipt='RCT-'+datetime.now().strftime('%Y%m%d%H%M%S')+'-'+secrets.token_hex(2).upper()
            cur=con.execute('INSERT INTO bills(receipt_no,cashier_id,subtotal,tax_total,total) VALUES(?,?,?,?,?)',(receipt,session['user_id'],round(subtotal,2),round(tax_total,2),round(subtotal+tax_total,2))); bid=cur.lastrowid
            for p,qty,ls,lt,total in calculated:
                con.execute('INSERT INTO bill_items(bill_id,product_id,product_name,quantity,unit_price,tax_rate,line_subtotal,line_tax,line_total) VALUES(?,?,?,?,?,?,?,?,?)',(bid,p['id'],p['name'],qty,p['price'],p['tax_rate'],ls,lt,total)); con.execute('UPDATE products SET quantity=quantity-? WHERE id=?',(qty,p['id']))
            bill=dict(con.execute('SELECT * FROM bills WHERE id=?',(bid,)).fetchone())
        return jsonify(bill),201
    except RuntimeError as e: return jsonify(error=str(e)),409
    except (ValueError,TypeError,KeyError): return jsonify(error='Invalid bill items'),400

@app.route('/api/reports/sales', methods=['GET'])
@roles_required('admin')
def api_sales_report():
    period=request.args.get('period','daily')
    filters={'daily':"date(created_at)=date('now','localtime')",'weekly':"date(created_at)>=date('now','-6 days','localtime')",'monthly':"strftime('%Y-%m',created_at)=strftime('%Y-%m','now','localtime')"}
    if period not in filters: return jsonify(error='period must be daily, weekly, or monthly'),400
    with db() as con: result=con.execute(f"SELECT COUNT(*) bills,COALESCE(SUM(subtotal),0) subtotal,COALESCE(SUM(tax_total),0) tax,COALESCE(SUM(total),0) total FROM bills WHERE {filters[period]}").fetchone()
    return jsonify(period=period, **dict(result)),200

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'): return jsonify(error='Endpoint not found'),404
    return render_template('404.html'),404

init_db()
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='127.0.0.1', port=int(os.environ.get('PORT','5000')))

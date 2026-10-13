import json
import pytest
import app as shop

@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_db = tmp_path / 'test_shopstock.db'
    monkeypatch.setattr(shop, 'DB_PATH', str(test_db))
    shop.init_db()
    shop.app.config.update(TESTING=True, SECRET_KEY='test-secret')
    with shop.app.test_client() as client:
        yield client


def login(client, username='admin', password='Admin@123'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_login_and_dashboard(client):
    response = login(client)
    assert response.status_code == 200
    assert b'Good day' in response.data


def test_get_products_requires_auth(client):
    response = client.get('/api/products')
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Authentication required'


def test_product_crud_api(client):
    login(client)
    created = client.post('/api/products', json={'sku':'TEST-1','name':'Test Item','price':12.5,'quantity':10,'tax_rate':5,'low_stock_threshold':2})
    assert created.status_code == 201
    product = created.get_json()
    assert product['name'] == 'Test Item'
    pid = product['id']
    fetched = client.get(f'/api/products/{pid}')
    assert fetched.status_code == 200
    updated = client.put(f'/api/products/{pid}', json={'name':'Updated Item','price':15,'quantity':8,'tax_rate':5,'low_stock_threshold':2})
    assert updated.status_code == 200
    assert updated.get_json()['name'] == 'Updated Item'
    deleted = client.delete(f'/api/products/{pid}')
    assert deleted.status_code == 204
    missing = client.get(f'/api/products/{pid}')
    assert missing.status_code == 404


def test_duplicate_sku_rejected(client):
    login(client)
    body = {'sku':'DUP-1','name':'Duplicate One','price':5,'quantity':3}
    assert client.post('/api/products', json=body).status_code == 201
    body['name'] = 'Duplicate Two'
    assert client.post('/api/products', json=body).status_code == 409


def test_cashier_cannot_create_product_or_view_reports(client):
    login(client, 'cashier', 'Cashier@123')
    assert client.post('/api/products', json={'sku':'X','name':'X','price':1,'quantity':1}).status_code == 403
    assert client.get('/api/reports/sales').status_code == 403


def test_bill_updates_stock_and_calculates_tax(client):
    login(client)
    with shop.db() as con:
        product = con.execute("SELECT * FROM products WHERE sku='SKU-1003'").fetchone()
        pid, before, price, tax = product['id'], product['quantity'], product['price'], product['tax_rate']
    response = client.post('/api/bills', json={'items':[{'product_id':pid,'quantity':2}]})
    assert response.status_code == 201
    bill = response.get_json()
    assert round(bill['subtotal'], 2) == round(price * 2, 2)
    assert round(bill['tax_total'], 2) == round(price * 2 * tax / 100, 2)
    with shop.db() as con:
        after = con.execute('SELECT quantity FROM products WHERE id=?',(pid,)).fetchone()['quantity']
    assert after == before - 2


def test_insufficient_stock_does_not_create_bill_or_reduce_stock(client):
    login(client)
    with shop.db() as con:
        p=con.execute("SELECT * FROM products WHERE sku='SKU-1002'").fetchone(); pid=p['id']; before=p['quantity']
        bills_before=con.execute('SELECT COUNT(*) FROM bills').fetchone()[0]
    response=client.post('/api/bills',json={'items':[{'product_id':pid,'quantity':before+1}]})
    assert response.status_code == 409
    with shop.db() as con:
        after=con.execute('SELECT quantity FROM products WHERE id=?',(pid,)).fetchone()['quantity']
        bills_after=con.execute('SELECT COUNT(*) FROM bills').fetchone()[0]
    assert after == before
    assert bills_after == bills_before


def test_invalid_report_period(client):
    login(client)
    assert client.get('/api/reports/sales?period=yearly').status_code == 400

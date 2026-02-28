from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import matplotlib
matplotlib.use('Agg') # Server side plotting ke liye zaroori hai
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "vu_finance_pro_secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance_v3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))

# --- Routes ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_pass = request.form.get('confirm_password')

        if password != confirm_pass:
            return "Passwords do not match!"

        if User.query.filter_by(email=email).first():
            return redirect(url_for('login'))

        new_user = User(full_name=full_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    expenses = Expense.query.filter_by(user_id=session['user_id']).all()
    
    # Visualization
    cat_data = {}
    for ex in expenses:
        cat_data[ex.category] = cat_data.get(ex.category, 0) + ex.amount

    chart_url = None
    if cat_data:
        plt.figure(figsize=(5, 4))
        plt.pie(cat_data.values(), labels=cat_data.keys(), autopct='%1.1f%%', colors=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e'])
        plt.title('Spending Distribution')
        
        if not os.path.exists('static'):
            os.makedirs('static')
        
        plt.savefig('static/chart.png', bbox_inches='tight')
        plt.close()
        chart_url = 'chart.png'

    return render_template('dashboard.html', expenses=expenses, name=session['user_name'], chart=chart_url)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        new_ex = Expense(
            user_id=session['user_id'],
            date=request.form.get('date'),
            amount=float(request.form.get('amount')),
            category=request.form.get('category'),
            description=request.form.get('description')
        )
        db.session.add(new_ex)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
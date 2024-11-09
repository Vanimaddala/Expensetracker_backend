from flask import Flask, request, jsonify, send_file
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import io

app = Flask(__name__)

# Path to your SQLite database file
DATABASE = 'expenses.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To get rows as dictionaries
    return conn

# Create the expenses table (if not already created)
def init_db():
    conn = get_db()
    with conn:
        conn.execute(''' 
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL
            );
        ''')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.get_json()
    date = data['date']
    category = data['category']
    description = data['description']
    amount = data['amount']

    conn = get_db()
    with conn:
        conn.execute('''
            INSERT INTO expenses (date, category, description, amount)
            VALUES (?, ?, ?, ?)
        ''', (date, category, description, amount))

    return jsonify({"message": "Expense added successfully"}), 201

@app.route('/get_total_today', methods=['GET'])
def get_total_today():
    today = datetime.today().strftime('%Y-%m-%d')

    conn = get_db()
    total_expenses = conn.execute('''
        SELECT SUM(amount) FROM expenses WHERE date = ?
    ''', (today,)).fetchone()

    total_expenses = total_expenses[0] if total_expenses[0] is not None else 0.0

    return jsonify({"total_today": total_expenses})

@app.route('/get_week_analysis', methods=['GET'])
def get_week_analysis():
    today = datetime.today()
    week_start_date = today - timedelta(days=7)
    today_str = today.strftime('%Y-%m-%d')
    week_start_str = week_start_date.strftime('%Y-%m-%d')

    conn = get_db()
    expenses = conn.execute('''
        SELECT date, SUM(amount) AS total_spent
        FROM expenses
        WHERE date BETWEEN ? AND ?
        GROUP BY date
    ''', (week_start_str, today_str)).fetchall()

    if expenses:
        highest_spent_day = max(expenses, key=lambda x: x['total_spent'])
        return jsonify({
            'highest_spent_day': highest_spent_day['date'],
            'total_spent': highest_spent_day['total_spent']
        })
    else:
        return jsonify({'message': 'No expenses found for the past week'}), 404

@app.route('/visualize_weekly_expenses', methods=['GET'])
def visualize_weekly_expenses():
    today = datetime.today()
    week_start_date = today - timedelta(days=7)
    today_str = today.strftime('%Y-%m-%d')
    week_start_str = week_start_date.strftime('%Y-%m-%d')

    conn = get_db()
    expenses = conn.execute('''
        SELECT date, SUM(amount) AS total_spent
        FROM expenses
        WHERE date BETWEEN ? AND ?
        GROUP BY date
    ''', (week_start_str, today_str)).fetchall()

    if expenses:
        # Convert to DataFrame for visualization
        df = pd.DataFrame(expenses)
        plt.figure(figsize=(8, 6))
        plt.bar(df['date'], df['total_spent'], color='skyblue')
        plt.title('Weekly Expenses')
        plt.xlabel('Date')
        plt.ylabel('Total Spent')

        # Save to a BytesIO object to send as response
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        return send_file(img, mimetype='image/png')
    else:
        return jsonify({'message': 'No expenses found for the past week'}), 404

@app.route('/visualize_today_expenses_by_category', methods=['GET'])
def visualize_today_expenses_by_category():
    today = datetime.today().strftime('%Y-%m-%d')

    conn = get_db()
    expenses = conn.execute('''
        SELECT category, SUM(amount) AS total_spent
        FROM expenses
        WHERE date = ?
        GROUP BY category
    ''', (today,)).fetchall()

    if expenses:
        # Convert to DataFrame for visualization
        df = pd.DataFrame(expenses)
        plt.figure(figsize=(8, 6))
        plt.pie(df['total_spent'], labels=df['category'], autopct='%1.1f%%', colors=['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0'])
        plt.title('Today\'s Expenses by Category')

        # Save to a BytesIO object to send as response
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        return send_file(img, mimetype='image/png')
    else:
        return jsonify({'message': 'No expenses found for today'}), 404

if __name__ == '__main__':
    init_db()  # Ensure the database and table are created
    app.run(host='0.0.0.0', port=5000)  # Make sure to use 0.0.0.0 if running in a container

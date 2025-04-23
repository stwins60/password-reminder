from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import hashlib
import requests
import os
from dotenv import load_dotenv
import re
from flask_migrate import Migrate

# Load environment variables
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def evaluate_password_strength(password):
    length = len(password) >= 8
    upper = re.search(r'[A-Z]', password)
    lower = re.search(r'[a-z]', password)
    digit = re.search(r'[0-9]', password)
    special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    if all([length, upper, lower, digit, special]):
        return 'Strong'
    elif length and (upper or lower) and (digit or special):
        return 'Medium'
    else:
        return 'Weak'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    last_password_update = db.Column(db.DateTime, default=datetime.utcnow)
    slack_webhook = db.Column(db.String(255), nullable=True)
    passwords = db.relationship('PasswordHistory', backref='user', lazy=True)

    def check_password_health(self):
        age = (datetime.utcnow() - self.last_password_update).days
        return age < 90

class PasswordHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        flash("User not found. Please log in again.")
        return redirect(url_for('login'))

    password_healthy = user.check_password_health()
    password_history = PasswordHistory.query.filter_by(user_id=user.id).order_by(PasswordHistory.created_at.desc()).all()
    return render_template('dashboard.html', user=user, password_healthy=password_healthy, password_history=password_history, current_time=datetime.utcnow())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        strength = evaluate_password_strength(password)

        if strength == 'Weak':
            flash("Password is too weak. Please include at least 8 characters, upper and lower case letters, a number, and a special character.")
            return redirect(url_for('register'))

        hash_pw = hashlib.sha256(password.encode()).hexdigest()
        new_user = User(username=username, password_hash=hash_pw)
        db.session.add(new_user)
        db.session.commit()
        flash(f"User registered successfully. Password strength: {strength}")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_pw = hashlib.sha256(password.encode()).hexdigest()
        user = User.query.filter_by(username=username, password_hash=hash_pw).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/update-password', methods=['GET', 'POST'])
def update_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        new_password = request.form['new_password']
        hash_pw = hashlib.sha256(new_password.encode()).hexdigest()
        user.password_hash = hash_pw
        user.last_password_update = datetime.utcnow()
        new_history = PasswordHistory(user_id=user.id, password_hash=hash_pw)
        db.session.add(new_history)
        db.session.commit()
        flash("Password updated.")
        return redirect(url_for('home'))
    return render_template('update_password.html')

@app.route('/set-webhook', methods=['GET', 'POST'])
def set_webhook():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        webhook = request.form['webhook']
        user.slack_webhook = webhook
        db.session.commit()
        flash("Slack webhook URL updated.")
        return redirect(url_for('home'))
    return render_template('set_webhook.html', user=user)

@app.route('/notify-slack')
def notify_slack():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        webhook = user.slack_webhook or os.getenv("SLACK_WEBHOOK_URL")
        message = f"Reminder: {user.username}, please update your password."
        if webhook:
            requests.post(webhook, json={"text": message})
            flash("Notification sent to Slack.")
        else:
            flash("Slack webhook URL not set.")
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)


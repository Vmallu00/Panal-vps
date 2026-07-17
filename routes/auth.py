from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('vps.dashboard'))
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

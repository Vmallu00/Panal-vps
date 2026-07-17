#!/usr/bin/env python3
import os, secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps

from db import get_db, close_db

# ---- Import Blueprints ----
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.nodes import nodes_bp
from routes.vps import vps_bp

app = Flask(__name__)
app.secret_key = "CHANGE_ME"
app.teardown_appcontext(close_db)

# ---- Register Blueprints ----
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(nodes_bp)
app.register_blueprint(vps_bp)

# ---- Database initialization ----
def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            max_ram INTEGER DEFAULT 0,
            max_cpu INTEGER DEFAULT 0,
            max_disk INTEGER DEFAULT 0,
            status TEXT DEFAULT 'offline',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS vps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            cpu REAL NOT NULL,
            ram INTEGER NOT NULL,
            disk INTEGER NOT NULL,
            ssh_port INTEGER NOT NULL,
            private_ip TEXT,
            node_id INTEGER DEFAULT 1,
            container_id TEXT DEFAULT '',
            status TEXT DEFAULT 'stopped',
            expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(node_id) REFERENCES nodes(id)
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS redeem_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            cpu REAL, ram INTEGER, disk INTEGER, duration INTEGER,
            used_by INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Default admin
        cur.execute("SELECT * FROM users WHERE username='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO users (username, password, is_admin) VALUES (?,?,?)",
                        ('admin', 'admin123', 1))
        # Default local node
        cur.execute("SELECT * FROM nodes")
        if not cur.fetchone():
            cur.execute("INSERT INTO nodes (name, api_url, api_key) VALUES (?,?,?)",
                        ('LocalHost', 'http://127.0.0.1:9000', 'dummy-key'))
        db.commit()

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)

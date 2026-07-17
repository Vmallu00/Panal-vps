from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from db import get_db
from node_manager import get_least_loaded_node, get_node, NodeClient
from utils import login_required

vps_bp = Blueprint('vps', __name__, url_prefix='/vps')

@vps_bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cur = db.cursor()
    if session.get('is_admin'):
        cur.execute("SELECT * FROM vps ORDER BY id DESC")
    else:
        cur.execute("SELECT * FROM vps WHERE user_id=? ORDER BY id DESC", (session['user_id'],))
    return render_template('dashboard.html', vps_list=cur.fetchall())

# ... rest of the create and action routes (already provided)

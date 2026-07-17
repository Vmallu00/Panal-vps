from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from node_manager import get_db, get_least_loaded_node, get_node, NodeClient
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

@vps_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        cpu = float(request.form['cpu'])
        ram = int(request.form['ram'])
        disk = int(request.form['disk'])
        duration = int(request.form['duration'])

        node_id = get_least_loaded_node(cpu, ram, disk)
        if not node_id:
            flash("No node with resources", "danger")
            return redirect(url_for('vps.dashboard'))

        node = get_node(node_id)
        client = NodeClient(node['api_url'], node['api_key'])

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT ssh_port FROM vps ORDER BY ssh_port DESC")
        used = [r[0] for r in cur.fetchall()]
        port = 22000
        while port in used: port += 1
        if port > 25000:
            flash("No free SSH ports", "danger")
            return redirect(url_for('vps.dashboard'))

        result = client.create_container(name, cpu, ram, disk, port)
        if 'error' in result:
            flash(f"Node error: {result['error']}", "danger")
            return redirect(url_for('vps.dashboard'))

        expiry = datetime.now() + timedelta(days=duration)
        cur.execute("""
            INSERT INTO vps (user_id, name, cpu, ram, disk, ssh_port, private_ip, node_id, container_id, expiry, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (session['user_id'], name, cpu, ram, disk, port, result['private_ip'], node_id, result['container_id'], expiry, 'running'))
        db.commit()
        flash("VPS created!", "success")
        return redirect(url_for('vps.dashboard'))
    return render_template('vps_create.html')

@vps_bp.route('/<int:vid>/<action>')
@login_required
def action(vid, action):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT node_id, container_id FROM vps WHERE id=?", (vid,))
    row = cur.fetchone()
    if not row:
        flash("VPS not found", "danger")
        return redirect(url_for('vps.dashboard'))

    node = get_node(row['node_id'])
    client = NodeClient(node['api_url'], node['api_key'])
    cid = row['container_id']

    if action == 'start':   client.start(cid)
    elif action == 'stop':  client.stop(cid)
    elif action == 'restart': client.restart(cid)
    elif action == 'delete':
        client.delete(cid)
        cur.execute("DELETE FROM vps WHERE id=?", (vid,))
        db.commit()
        flash("Deleted", "success")
        return redirect(url_for('vps.dashboard'))
    else:
        flash("Unknown action", "danger")
        return redirect(url_for('vps.dashboard'))

    if action != 'delete':
        cur.execute("UPDATE vps SET status=? WHERE id=?", (action, vid))
        db.commit()
    flash(f"{action} successful", "success")
    return redirect(url_for('vps.dashboard'))

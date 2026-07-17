from flask import Blueprint, request, render_template, redirect, url_for, flash
from node_manager import get_db, update_node_status, NodeClient

nodes_bp = Blueprint('nodes', __name__, url_prefix='/admin/nodes')

@nodes_bp.route('/')
def list_nodes():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM nodes")
    nodes = cur.fetchall()
    for n in nodes:
        update_node_status(n['id'])
    cur.execute("SELECT * FROM nodes")
    return render_template('admin_nodes.html', nodes=cur.fetchall())

@nodes_bp.route('/add', methods=['GET', 'POST'])
def add_node():
    if request.method == 'POST':
        name = request.form['name']
        api_url = request.form['api_url']
        api_key = request.form['api_key']
        max_ram = int(request.form.get('max_ram', 0))
        max_cpu = int(request.form.get('max_cpu', 0))
        max_disk = int(request.form.get('max_disk', 0))
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO nodes (name, api_url, api_key, max_ram, max_cpu, max_disk) VALUES (?,?,?,?,?,?)",
                    (name, api_url, api_key, max_ram, max_cpu, max_disk))
        db.commit()
        flash("Node added", "success")
        return redirect(url_for('nodes.list_nodes'))
    return render_template('admin_node_form.html')

@nodes_bp.route('/delete/<int:nid>', methods=['POST'])
def delete_node(nid):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM vps WHERE node_id=?", (nid,))
    if cur.fetchone()[0] > 0:
        flash("Node has active VPS", "danger")
    else:
        cur.execute("DELETE FROM nodes WHERE id=?", (nid,))
        db.commit()
        flash("Deleted", "success")
    return redirect(url_for('nodes.list_nodes'))

#!/usr/bin/env python3
import sqlite3
from flask import g
from node_client import NodeClient

DATABASE = "/opt/lvm-panel-pro/lvm_panel.db"   # <-- Change to your actual DB path

def get_db():
    """Get database connection (works inside Flask app context)."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_all_nodes():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM nodes ORDER BY id")
    return cur.fetchall()

def get_node(node_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    return cur.fetchone()

def get_node_client(node_id):
    node = get_node(node_id)
    if not node:
        return None
    return NodeClient(node["api_url"], node["api_key"])

def update_node_status(node_id):
    """Ping the node and update its status in the DB."""
    node = get_node(node_id)
    if not node:
        return
    client = NodeClient(node["api_url"], node["api_key"])
    resp = client.health()
    status = "online" if resp.get("status") == "ok" else "offline"
    cur = get_db().cursor()
    cur.execute("UPDATE nodes SET status = ? WHERE id = ?", (status, node_id))
    get_db().commit()
    return status

def get_least_loaded_node(cpu_req, ram_req, disk_req):
    """
    Pick the node with the most free RAM %.
    Returns node_id, or None if no suitable node.
    """
    nodes = get_all_nodes()
    best_node = None
    best_score = -1

    for n in nodes:
        if n["status"] != "online":
            continue

        client = NodeClient(n["api_url"], n["api_key"])
        stats = client.stats()

        if "error" in stats:
            continue

        # Avoid nodes with high CPU load
        if stats.get("cpu_percent", 100) > 80:
            continue

        # Check if node has enough free RAM (with 20% buffer)
        free_ram_mb = stats.get("ram_free", 0)  # already in MB from agent
        if free_ram_mb < ram_req * 1.2:
            continue

        # Score = free RAM percentage (higher is better)
        score = 100 - stats.get("ram_percent", 100)
        if score > best_score:
            best_score = score
            best_node = n["id"]

    # Fallback to node 1 (assumes it exists)
    return best_node if best_node is not None else 1

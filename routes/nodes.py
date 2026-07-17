from flask import Blueprint, request, render_template, redirect, url_for, flash
from db import get_db
from node_manager import update_node_status, NodeClient

nodes_bp = Blueprint('nodes', __name__, url_prefix='/admin/nodes')

# ... same as before, just import get_db from db

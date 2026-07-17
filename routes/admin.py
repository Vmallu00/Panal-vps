from flask import Blueprint, render_template
from utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin.html')  # You can create a simple admin page

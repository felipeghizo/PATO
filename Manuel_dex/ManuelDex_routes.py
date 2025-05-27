from flask import Blueprint, render_template

manueldex_bp = Blueprint('manueldex', __name__,
                         template_folder='templates',
                         static_folder='static')

@manueldex_bp.route('/')
def manueldex_home():
    return render_template('manueldex/manueldex.html')

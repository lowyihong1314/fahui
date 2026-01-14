from flask import Blueprint,render_template,request
import json
from flask_login import login_required, current_user
from datetime import date
from function.config import verification_required
template_bp = Blueprint('template', __name__)

@template_bp.route('/home')
def home():
    return render_template('home.html')

@template_bp.route('/fahui_data')
@login_required
def fahui_data():
    return render_template('fahui_data.html')

@template_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@template_bp.route('/show_order_detail/<int:order_id>')
@verification_required(order_id_arg_name='order_id')
def show_order_detail(order_id):
    return render_template('show_order_detail.html', order_id=order_id)

@template_bp.route('/fahui_input/<int:order_id>')
@verification_required(order_id_arg_name='order_id')
def fahui_input(order_id):
    return render_template('fahui_input.html', order_id=order_id)

@template_bp.route('/pay_order/<int:order_id>')
@verification_required(order_id_arg_name='order_id')
def pay_order(order_id):
    return render_template('pay_order.html', order_id=order_id)

@template_bp.route('/accounting')
@login_required
def accounting():
    return render_template('accounting.html')

@template_bp.route('/user_control')
@login_required
def user_control():
    return render_template('user_control.html')

@template_bp.route('/scan_barcode')
@login_required
def scan_barcode():
    return render_template('scan_barcode.html')

@template_bp.route('/view_pdf')
def view_pdf():
    return render_template('view_pdf.html')
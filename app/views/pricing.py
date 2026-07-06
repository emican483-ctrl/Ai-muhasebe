from flask import Blueprint, render_template, session, redirect, url_for, flash
import sqlite3

pricing_bp = Blueprint('pricing', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@pricing_bp.route('/pricing')
def index():
    return render_template('dashboard/pricing.html')

@pricing_bp.route('/checkout/<int:package_id>')
def checkout(package_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Paket satın alabilmek için lütfen önce üye olun veya giriş yapın!', 'warning')
        return redirect(url_for('auth.login'))
        
    # TEST MODU: Ödeme başarılı olmuş gibi veritabanında kullanıcının paketini güncelliyoruz
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_premium = ? WHERE id = ?', (package_id, user_id))
    conn.commit()
    conn.close()
    
    flash('Ödemeniz başarıyla alındı! Hesabınız yükseltildi.', 'success')
    return redirect(url_for('dashboard.index'))

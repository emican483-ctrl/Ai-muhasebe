import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.models import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Şifreyi güvenli hale getiren fonksiyon (SHA256 kullanarak)
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        db = get_db()
        error = None

        if not username:
            error = 'Kullanıcı adı gerekli.'
        elif not password:
            error = 'Şifre gerekli.'

        if error is None:
            try:
                hashed_pw = hash_password(password)
                db.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)',
                    (username, hashed_pw)
                )
                db.commit()
                return redirect(url_for('auth.login'))
            except db.IntegrityError:
                error = f"'{username}' kullanıcı adı zaten alınmış."

        flash(error)
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        db = get_db()
        error = None
        
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user is None:
            error = 'Hatalı kullanıcı adı.'
        elif user['password'] != hash_password(password):
            error = 'Hatalı şifre.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard.index'))

        flash(error)
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import uuid
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@dashboard_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'guest_id' not in session:
        session['guest_id'] = str(uuid.uuid4())

    conn = get_db_connection()
    user_id = session.get('user_id')
    
    # Kullanıcı durumunu ve paketini kontrol et
    user_plan = 0  # 0: Misafir/Ücretsiz, 1: 7$ Planı, 2: 15$ Premium Plus
    if user_id:
        user = conn.execute('SELECT is_premium FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            user_plan = user['is_premium']

    if request.method == 'POST':
        # MİSAFİR KONTROLÜ (Maksimum 1 Fiş)
        if user_plan == 0:
            guest = conn.execute('SELECT usage_count FROM guest_usage WHERE session_id = ?', (session['guest_id'],)).fetchone()
            if guest and guest['usage_count'] >= 1:
                flash('Ücretsiz 1 deneme hakkınız bitmiştir. Devam etmek için lütfen üye olun veya paket satın alın!', 'danger')
                return redirect(url_for('pricing.index'))
            
            if not guest:
                conn.execute('INSERT INTO guest_usage (session_id, usage_count) VALUES (?, 1)', (session['guest_id'],))
            else:
                conn.execute('UPDATE guest_usage SET usage_count = usage_count + 1 WHERE session_id = ?', (session['guest_id'],))
            conn.commit()

        # 7$ BAŞLANGIÇ PLANI KONTROLÜ (Toplam Maksimum 100 Fiş)
        elif user_plan == 1:
            doc_count = conn.execute('SELECT COUNT(*) as total FROM documents WHERE user_id = ?', (user_id,)).fetchone()
            if doc_count and doc_count['total'] >= 100:
                flash('Başlangıç planı aylık 100 adetlik limitinize ulaştınız. Premium Plus planına geçebilirsiniz!', 'warning')
                return redirect(url_for('pricing.index'))

        # 15$ PREMIUM PLUS KONTROLÜ (Günlük Adil Kullanım Kotası - 100 Fiş/Gün)
        elif user_plan == 2:
            today = datetime.now().strftime('%Y-%m-%d')
            daily_count = conn.execute("SELECT COUNT(*) as total FROM documents WHERE user_id = ? AND date(created_at) = ?", (user_id, today)).fetchone()
            if daily_count and daily_count['total'] >= 100:
                flash('Premium Plus günlük adil kullanım kotasına (100 adet) ulaştınız. Lütfen yarın tekrar deneyin.', 'warning')
                return redirect(url_for('dashboard.index'))

        # [Burada Fatura Yükleme ve Gemini API Analiz İşlemleri tıkır tıkır çalışacak]
        flash('Belge başarıyla analiz edildi!', 'success')

    # Kullanıcının geçmiş belgelerini listele
    documents = []
    if user_id:
        documents = conn.execute('SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
        
    conn.close()
    return render_template('dashboard/index.html', documents=documents, user_plan=user_plan, user_id=user_id)

from flask import Blueprint, render_request, render_template, request, redirect, url_for, flash, session
import sqlite3
import uuid

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@dashboard_bp.route('/', methods=['GET', 'POST'])
def index():
    # Tarayıcıda session yoksa misafir için benzersiz bir ID oluştur
    if 'guest_id' not in session:
        session['guest_id'] = str(uuid.uuid4())

    conn = get_db_connection()
    
    # Kullanıcı giriş yapmış mı?
    user_id = session.get('user_id')
    is_premium = False
    
    if user_id:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user and user['is_premium'] == 1:
            is_premium = True

    if request.method == 'POST':
        # EĞER GİRİŞ YAPMAMIŞSA deneme hakkını kontrol et
        if not user_id:
            guest = conn.execute('SELECT * FROM guest_usage WHERE session_id = ?', (session['guest_id'],)).fetchone()
            if guest and guest['usage_count'] >= 1:
                flash('Ücretsiz 1 deneme hakkınız bitmiştir. Lütfen devam etmek için üye olun veya Premium plana geçin!', 'danger')
                return redirect(url_for('dashboard.index'))
            
            # Hakkı yoksa tabloya ekle veya artır
            if not guest:
                conn.execute('INSERT INTO guest_usage (session_id, usage_count) VALUES (?, 1)', (session['guest_id'],))
            else:
                conn.execute('UPDATE guest_usage SET usage_count = usage_count + 1 WHERE session_id = ?', (session['guest_id'],))
            conn.commit()

        # Fatura Yükleme ve Gemini Analiz İşlemleri Buraya Gelecek
        # (Yüklenen dosya kaydedilir, Gemini API'ye gönderilir ve veritabanına yazılır)
        
        flash('Belge başarıyla analiz edildi!', 'success')
        
    # Geçmiş belgeleri listele (Giriş yaptıysa kendi belgeleri, yapmadıysa boş)
    documents = []
    if user_id:
        documents = conn.execute('SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
        
    conn.close()
    return render_template('dashboard/index.html', documents=documents, user_id=user_id, is_premium=is_premium)

import os
import json
import re
import pandas as pd
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, g, flash, current_app, send_file
from werkzeug.utils import secure_filename
from app.models import get_db
from google import genai
from google.genai import types

bp = Blueprint('dashboard', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_invoice_with_gemini(file_path, api_key):
    try:
        client = genai.Client(api_key=api_key)
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
            
        prompt = """Bu bir fatura veya fiş görselidir. Lütfen bu belgedeki bilgileri analiz et ve bana SADECE şu bilgileri içeren temiz, geçerli bir JSON objesi döndür:
        {
          "firma_adi": "...",
          "tarih": "...",
          "toplam_tutar": ...,
          "kdv_tutari": ...,
          "kdv_orani": "..."
        }
        Değerler mevcut değilse boş bırakın. Toplam tutar ve KDV tutarı sadece sayı olmalı (örneğin 150.50).
        JSON dışında hiçbir metin, açıklama veya kod bloğu işareti (```json gibi) ekleme."""

        response = client.models.generate_content(
            model='gemini-2.0-flash', # En hızlı model
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                prompt
            ]
        )
        
        # Temiz JSON ayıklama
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        else:
            return response.text # Hata durumunda ham metni döndür
            
    except Exception as e:
        return json.dumps({"hata": f"Yapay zeka analizi sırasında bir hata oluştu: {str(e)}"})

@bp.route('/', methods=('GET', 'POST'))
def index():
    if g.user is None:
        return redirect(url_for('auth.login'))
    
    db = get_db()

    if request.method == 'POST':
        if 'api_key' in request.form:
            api_key = request.form['api_key'].strip()
            if api_key:
                existing = db.execute('SELECT id FROM settings WHERE user_id = ?', (g.user['id'],)).fetchone()
                if existing:
                    db.execute('UPDATE settings SET api_key = ? WHERE user_id = ?', (api_key, g.user['id']))
                else:
                    db.execute('INSERT INTO settings (user_id, api_key) VALUES (?, ?)', (g.user['id'], api_key))
                db.commit()
                flash('Gemini API Anahtarı başarıyla kaydedildi!')
            return redirect(url_for('dashboard.index'))

        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                saved_filename = f"user_{g.user['id']}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
                file.save(file_path)
                
                settings = db.execute('SELECT api_key FROM settings WHERE user_id = ?', (g.user['id'],)).fetchone()
                
                if settings:
                    analysis_result = analyze_invoice_with_gemini(file_path, settings['api_key'])
                    status = 'Tamamlandı'
                else:
                    analysis_result = json.dumps({"hata": "API Anahtarı bulunamadı."})
                    status = 'API Eksik'

                db.execute(
                    'INSERT INTO documents (user_id, file_name, file_path, status, analysis_result) VALUES (?, ?, ?, ?, ?)',
                    (g.user['id'], filename, file_path, status, analysis_result)
                )
                db.commit()
                flash('Belge başarıyla işlendi!')
                return redirect(url_for('dashboard.index'))

    raw_documents = db.execute('SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC', (g.user['id'],)).fetchall()
    
    # Belgeleri HTML'de düzgün göstermek için işlemden geçiriyoruz
    documents = []
    for doc in raw_documents:
        doc_dict = dict(doc)
        if doc['analysis_result'] and doc['status'] == 'Tamamlandı':
            try:
                # JSON metnini Python sözlüğüne çevir
                data = json.loads(doc['analysis_result'])
                formatted_result = (
                    f"Firma Adı: {data.get('firma_adi', 'N/A')}\n"
                    f"Tarih: {data.get('tarih', 'N/A')}\n"
                    f"Toplam Tutar: {data.get('toplam_tutar', 'N/A')}\n"
                    f"KDV Tutarı: {data.get('kdv_tutari', 'N/A')}\n"
                    f"KDV Oranı: {data.get('kdv_orani', 'N/A')}"
                )
                doc_dict['formatted_result'] = formatted_result
                doc_dict['data'] = data
            except json.JSONDecodeError:
                doc_dict['formatted_result'] = "JSON Çözümleme Hatası: " + doc['analysis_result']
        elif doc['status'] == 'API Eksik':
            doc_dict['formatted_result'] = "Lütfen önce API anahtarını tanımlayın."
        else:
            doc_dict['formatted_result'] = doc['analysis_result']
            
        documents.append(doc_dict)
        
    settings = db.execute('SELECT api_key FROM settings WHERE user_id = ?', (g.user['id'],)).fetchone()
    api_key_exists = True if settings else False

    return render_template('dashboard/index.html', documents=documents, api_key_exists=api_key_exists)

@bp.route('/download-excel/<int:doc_id>')
def download_excel(doc_id):
    if g.user is None:
        return redirect(url_for('auth.login'))
        
    db = get_db()
    doc = db.execute('SELECT * FROM documents WHERE id = ? AND user_id = ?', (doc_id, g.user['id'])).fetchone()
    
    if not doc or not doc['analysis_result'] or doc['status'] != 'Tamamlandı':
        flash('Belge bulunamadı veya henüz işlenmedi.')
        return redirect(url_for('dashboard.index'))
        
    try:
        data = json.loads(doc['analysis_result'])
        # Excel için veriyi hazırla
        excel_data = {
            'Belge Adı': [doc['file_name']],
            'Firma Adı': [data.get('firma_adi', 'N/A')],
            'Tarih': [data.get('tarih', 'N/A')],
            'Toplam Tutar': [data.get('toplam_tutar', 'N/A')],
            'KDV Tutarı': [data.get('kdv_tutari', 'N/A')],
            'KDV Oranı': [data.get('kdv_orani', 'N/A')],
            'Yükleme Tarihi': [doc['created_at']]
        }
        
        df = pd.DataFrame(excel_data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Fatura Verisi')
        
        output.seek(0)
        
        excel_filename = f"{os.path.splitext(doc['file_name'])[0]}.xlsx"
        
        return send_file(output, as_attachment=True, download_filename=excel_filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except (json.JSONDecodeError, Exception) as e:
        flash(f'Excel oluşturma hatası: {str(e)}')
        return redirect(url_for('dashboard.index'))

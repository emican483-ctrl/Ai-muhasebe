import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Kullanıcılar Tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    is_premium INTEGER DEFAULT 0
)
''')

# Belgeler Tablosu (Eksik kolon hatası çözülmüş hali)
cursor.execute('''
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_name TEXT,
    analysis_result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# Misafir Kullanıcılar Takip Tablosu (1 Fiş Deneme Hakkı İçin)
cursor.execute('''
CREATE TABLE IF NOT EXISTS guest_usage (
    session_id TEXT PRIMARY KEY,
    usage_count INTEGER DEFAULT 0
)
''')

conn.commit()
conn.close()
print("Veritabanı tabloları profesyonel SaaS modeline uygun olarak başarıyla oluşturuldu!")

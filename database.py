import sqlite3
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, db_file="avtomoyka.db"):
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_file)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Фойдаланувчилар жадвали
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                car_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Навбатлар жадвали
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS navbatlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sana TEXT,
                vaqt TEXT,
                xizmat_turi TEXT,
                status TEXT DEFAULT 'kutilyapti',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Банд вақтлар жадвали
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS band_vaqtlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sana TEXT,
                vaqt TEXT,
                band BOOLEAN DEFAULT 1,
                UNIQUE(sana, vaqt)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, full_name, phone, car_number):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, full_name, phone, car_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, full_name, phone, car_number))
            conn.commit()
            return True
        except Exception as e:
            print(f"Xato: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def add_navbat(self, user_id, sana, vaqt, xizmat_turi):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO navbatlar (user_id, sana, vaqt, xizmat_turi)
                VALUES (?, ?, ?, ?)
            ''', (user_id, sana, vaqt, xizmat_turi))
            
            # Вақтни банд қилиш
            cursor.execute('''
                INSERT OR REPLACE INTO band_vaqtlar (sana, vaqt, band)
                VALUES (?, ?, 1)
            ''', (sana, vaqt))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Xato: {e}")
            return False
        finally:
            conn.close()
    
    def get_mavjud_vaqtlar(self, sana):
        """Берилган кун учун мавжуд вақтларни олиш"""
        from config import ISH_VAQTI
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Банд вақтларни олиш
        cursor.execute("SELECT vaqt FROM band_vaqtlar WHERE sana = ? AND band = 1", (sana,))
        band_vaqtlar = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Барча иш вақтларини яратиш (30 дақиқа интервал)
        mavjud_vaqtlar = []
        start = datetime.strptime(ISH_VAQTI["boshlanish"], "%H:%M")
        end = datetime.strptime(ISH_VAQTI["tugash"], "%H:%M")
        
        current = start
        while current < end:
            vaqt_str = current.strftime("%H:%M")
            
            # Тушлик вақтини текшириш
            tanaffus_bosh = datetime.strptime(ISH_VAQTI["tanaffus"][0], "%H:%M")
            tanaffus_tugash = datetime.strptime(ISH_VAQTI["tanaffus"][1], "%H:%M")
            
            if not (tanaffus_bosh <= current < tanaffus_tugash):
                if vaqt_str not in band_vaqtlar:
                    mavjud_vaqtlar.append(vaqt_str)
            
            current += timedelta(minutes=30)
        
        return mavjud_vaqtlar
    
    def get_user_navbatlari(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM navbatlar 
            WHERE user_id = ? AND sana >= date('now')
            ORDER BY sana, vaqt
        ''', (user_id,))
        result = cursor.fetchall()
        conn.close()
        return result
    
    def cancel_navbat(self, navbat_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Навбат маълумотларини олиш
        cursor.execute("SELECT sana, vaqt FROM navbatlar WHERE id = ? AND user_id = ?", 
                      (navbat_id, user_id))
        navbat = cursor.fetchone()
        
        if navbat:
            sana, vaqt = navbat
            # Навбатни ўчириш
            cursor.execute("DELETE FROM navbatlar WHERE id = ?", (navbat_id,))
            # Вақтни бўшатиш
            cursor.execute("DELETE FROM band_vaqtlar WHERE sana = ? AND vaqt = ?", (sana, vaqt))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def get_all_navbatlar(self, sana=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if sana:
            cursor.execute('''
                SELECT n.*, u.full_name, u.phone, u.car_number 
                FROM navbatlar n
                JOIN users u ON n.user_id = u.user_id
                WHERE n.sana = ?
                ORDER BY n.vaqt
            ''', (sana,))
        else:
            cursor.execute('''
                SELECT n.*, u.full_name, u.phone, u.car_number 
                FROM navbatlar n
                JOIN users u ON n.user_id = u.user_id
                WHERE n.sana >= date('now')
                ORDER BY n.sana, n.vaqt
            ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_statistika(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Бугунги навбатлар
        cursor.execute("SELECT COUNT(*) FROM navbatlar WHERE sana = date('now')")
        bugun = cursor.fetchone()[0]
        
        # Жами фойдаланувчилар
        cursor.execute("SELECT COUNT(*) FROM users")
        jami_users = cursor.fetchone()[0]
        
        # Жами навбатлар
        cursor.execute("SELECT COUNT(*) FROM navbatlar")
        jami_navbat = cursor.fetchone()[0]
        
        # Даромад (бугун)
        cursor.execute('''
            SELECT SUM(CASE 
                WHEN xizmat_turi = 'oddiy' THEN 50000
                WHEN xizmat_turi = 'kompleks' THEN 80000
                WHEN xizmat_turi = 'detailing' THEN 150000
                ELSE 0
            END) FROM navbatlar WHERE sana = date('now')
        ''')
        daromad = cursor.fetchone()[0] or 0
        
        conn.close()
        return {
            "bugun": bugun,
            "jami_users": jami_users,
            "jami_navbat": jami_navbat,
            "daromad": daromad
        }

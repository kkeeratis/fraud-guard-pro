import sqlite3

# 1. สร้าง/เชื่อมต่อกับไฟล์ฐานข้อมูลชื่อ fraud_data.db
conn = sqlite3.connect('fraud_data.db')
cursor = conn.cursor()

# 2. เขียนคำสั่ง SQL เพื่อสร้างตาราง (Table) เก็บข้อมูล
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        amount REAL,
        merchant TEXT,
        is_fraud TEXT
    )
''')

# 3. ใส่ข้อมูลจำลองตั้งต้น (Dummy Data) ลงไปนิดหน่อย
cursor.execute('''
    INSERT INTO transactions (customer_name, amount, merchant, is_fraud)
    VALUES 
    ('สมชาย', 1500.00, 'ร้านสะดวกซื้อ', 'No'),
    ('สมศรี', 45000.00, 'ร้านทอง', 'Yes')
''')

# 4. บันทึกและปิดการเชื่อมต่อ
conn.commit()
conn.close()

print("สร้างฐานข้อมูลและตาราง SQL สำเร็จแล้ว!")
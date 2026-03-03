import sqlite3
import random
from datetime import datetime, timedelta

# 1. เชื่อมต่อฐานข้อมูล
db_path = 'fraud_data_v2.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# รายชื่อร้านค้าและชื่อลูกค้าจำลอง
merchants = ['BigC', 'Lotus', 'Apple Store', '7-Eleven', 'Shell Station', 'Lazada', 'Shopee', 'Amazon Cafe', 'GrabFood']
customers = ['Somsak', 'Wichai', 'Ananda', 'Preecha', 'Siriwan', 'Malee', 'Kanya', 'Jittra', 'Natapong']

print("กำลังเริ่มปั๊มข้อมูลจำลอง 50 รายการ...")

# 2. วนลูปสร้างข้อมูล 50 ครั้ง
for i in range(50):
    cust_name = random.choice(customers)
    merch = random.choice(merchants)
    
    # สุ่มยอดเงิน (ระหว่าง 100 ถึง 50,000 บาท)
    amt = round(random.uniform(100.0, 50000.0), 2)
    
    # สุ่มสถานะทุจริต (ให้มีโอกาสทุจริตประมาณ 20% เพื่อความสมจริง)
    is_fraud = 'Yes' if random.random() < 0.2 else 'No'
    
    # สุ่มวันที่ย้อนหลัง (ภายใน 30 วันที่ผ่านมา)
    random_days = random.randint(0, 30)
    timestamp = datetime.now() - timedelta(days=random_days)

    # 3. ใช้คำสั่ง SQL INSERT เพื่อเพิ่มข้อมูล
    cursor.execute('''
        INSERT INTO transactions (customer_name, amount, merchant, is_fraud, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (cust_name, amt, merch, is_fraud, timestamp))

# 4. บันทึกและปิดการเชื่อมต่อ
conn.commit()
conn.close()

print("✅ ปั๊มข้อมูลจำลองสำเร็จ! ตอนนี้ฐานข้อมูลของคุณมีข้อมูลเพิ่มขึ้นอีก 50 รายการแล้ว")
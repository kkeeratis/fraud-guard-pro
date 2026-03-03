from database_manager import Session, Transaction, add_user
import random
from datetime import datetime, timedelta

def seed_transactions():
    session = Session()
    # ตรวจสอบก่อนว่ามีข้อมูลอยู่แล้วหรือยัง เพื่อไม่ให้สร้างซ้ำ
    if session.query(Transaction).count() > 0:
        print("Database already has data. Skipping seeding.")
        session.close()
        return

    customers = ["Somsak", "Wichai", "Keerati", "Anong", "Preecha", "Aekkachai"]
    merchants = ["Apple Store", "7-Eleven", "Gold Shop", "Starbucks", "Casino", "BigC"]
    
    # สร้างข้อมูลจำลอง 20 รายการ
    for i in range(20):
        name = random.choice(customers)
        merch = random.choice(merchants)
        amt = random.uniform(500, 60000)
        
        # กฎจำลอง: ถ้าซื้อที่ Casino หรือยอด > 45000 ให้เป็น Fraud (ตาม Rule-based ของเรา)
        is_fraud = "Yes" if (amt > 45000 or merch in ["Casino", "Gold Shop"]) else "No"
        
        new_tx = Transaction(
            customer_name=name,
            amount=round(amt, 2),
            merchant=merch,
            is_fraud=is_fraud,
            timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        session.add(new_tx)
    
    session.commit()
    session.close()
    print("Seeding completed!")

if __name__ == "__main__":
    seed_transactions()
    # สร้าง user admin เริ่มต้นด้วย
    add_user("admin", "1234", "admin")
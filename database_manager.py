import os
import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

# --- 1. การเชื่อมต่อฐานข้อมูล (ดึงจาก Neon PostgreSQL) ---
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    # ระบบสำรองเผื่อหาไฟล์ secrets.toml ไม่เจอ
    DATABASE_URL = "sqlite:///fraud_guard_pro_final.db"

# pool_pre_ping ช่วยรักษาการเชื่อมต่อไม่ให้หลุดเวลาทิ้งแอปไว้นานๆ
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- 2. โครงสร้างตาราง (Models) ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String, nullable=False)
    
    # มิติข้อมูลสำหรับนำไปวิเคราะห์ใน Power BI
    gender = Column(String, nullable=True)
    city = Column(String, nullable=True)
    job = Column(String, nullable=True)
    category = Column(String, nullable=True)
    
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    is_fraud = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

# --- 3. ระบบอัปโหลดข้อมูล (Bulk Insert เร็วปรื๊ด!) ---
def seed_initial_data(session):
    if session.query(Transaction).count() > 0:
        return

    csv_path = "fraudTrain.csv"
    
    if not os.path.exists(csv_path):
        st.error(f"🚨 ไม่พบไฟล์ '{csv_path}' กรุณานำไฟล์มาวางในโฟลเดอร์เดียวกัน")
        return
        
    st.info("⏳ กำลังเตรียมข้อมูล 1,000 รายการ และส่งขึ้น Cloud (Bulk Insert)...")
    
    try:
        df = pd.read_csv(csv_path).sample(n=1000, random_state=42)
        bulk_data = [] # กล่องเก็บข้อมูลเตรียมส่งรอบเดียว
        
        for index, row in df.iterrows():
            fname = str(row.get('first', 'Unknown'))
            lname = str(row.get('last', ''))
            customer = f"{fname} {lname}".strip()
            
            gender = str(row.get('gender', 'U'))
            city = str(row.get('city', 'Unknown'))
            job = str(row.get('job', 'Unknown'))
            category = str(row.get('category', 'Unknown'))
            
            merchant = str(row.get('merchant', 'Unknown')).replace("fraud_", "")
            amount = float(row.get('amt', 0.0))
            is_fraud = "Yes" if int(row.get('is_fraud', 0)) == 1 else "No"
            
            tx_time_str = str(row.get('trans_date_trans_time', ''))
            try:
                tx_time = datetime.strptime(tx_time_str, '%Y-%m-%d %H:%M:%S')
            except:
                tx_time = datetime.now()
            
            # สร้าง Object ยัดลงกล่อง
            tx = Transaction(
                customer_name=customer, gender=gender, city=city,
                job=job, category=category, amount=amount,
                merchant=merchant, is_fraud=is_fraud, timestamp=tx_time
            )
            bulk_data.append(tx)
            
        # ส่งข้อมูลทั้งกล่องขึ้น Database ในคำสั่งเดียว (เร็วมาก)
        session.bulk_save_objects(bulk_data)
        session.commit()
        st.success("✅ อัปโหลด 1,000 รายการเสร็จสิ้น! พร้อมเชื่อมต่อ Power BI")
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
        session.rollback()

def init_db():
    Base.metadata.create_all(engine)
    with Session() as session:
        if not session.query(User).filter_by(username="admin").first():
            hashed_pw = generate_password_hash("1234")
            session.add(User(username="admin", password_hash=hashed_pw))
        seed_initial_data(session)
        session.commit()

# --- 4. ฟังก์ชันจัดการข้อมูล (CRUD) ---
def get_user(username):
    with Session() as session:
        return session.query(User).filter_by(username=username).first()

def get_transactions():
    with Session() as session:
        return session.query(Transaction).order_by(Transaction.timestamp.desc()).all()

def add_transaction(name, amount, merchant, category, is_fraud):
    with Session() as session:
        new_tx = Transaction(
            customer_name=name, amount=amount, merchant=merchant, 
            category=category, gender="Manual Entry", city="Manual Entry", 
            job="Manual Entry", is_fraud=is_fraud
        )
        session.add(new_tx)
        session.commit()
        return True

def update_transaction(tx_id, name, amount, merchant, category, is_fraud):
    with Session() as session:
        tx = session.query(Transaction).filter_by(id=tx_id).first()
        if tx:
            tx.customer_name = name
            tx.amount = amount
            tx.merchant = merchant
            tx.category = category
            tx.is_fraud = is_fraud
            session.commit()
            return True
        return False

def delete_transaction(tx_id):
    with Session() as session:
        tx = session.query(Transaction).filter_by(id=tx_id).first()
        if tx:
            session.delete(tx)
            session.commit()
            return True
        return False
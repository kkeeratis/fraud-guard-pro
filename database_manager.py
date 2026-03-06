import os
import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

# --- 1. การเชื่อมต่อฐานข้อมูล (เน้น PostgreSQL สำหรับ Cloud) ---
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    # หากรันในเครื่องแล้วไม่มี link จะใช้ SQLite แทนชั่วคราว
    DATABASE_URL = "sqlite:///fraud_guard_pro_final.db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- 2. โครงสร้างตาราง (เพิ่มฟิลด์ city_pop เพื่อรองรับ AI) ---
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
    gender = Column(String, nullable=True)
    city = Column(String, nullable=True)
    job = Column(String, nullable=True)
    category = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    city_pop = Column(Integer, nullable=True) # ฟิลด์ใหม่สำหรับ AI
    is_fraud = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

# --- 3. ระบบอัปโหลดข้อมูล (Bulk Insert พร้อมโหลด city_pop) ---
def seed_initial_data(session):
    if session.query(Transaction).count() > 0:
        return

    csv_path = "fraudTrain.csv"
    if not os.path.exists(csv_path):
        st.warning(f"⚠️ ไม่พบไฟล์ '{csv_path}' ระบบจะข้ามการโหลดข้อมูลเริ่มต้น")
        return
        
    st.info("⏳ กำลังเตรียมข้อมูล 1,000 รายการพร้อมข้อมูลประชากร (city_pop) ส่งขึ้น Cloud...")
    
    try:
        df = pd.read_csv(csv_path).sample(n=1000, random_state=42)
        bulk_data = [] 
        
        for index, row in df.iterrows():
            fname = str(row.get('first', 'Unknown'))
            lname = str(row.get('last', ''))
            customer = f"{fname} {lname}".strip()
            
            # รวบรวมข้อมูลทุกฟิลด์ที่โมเดล AI ต้องใช้
            tx = Transaction(
                customer_name=customer,
                gender=str(row.get('gender', 'U')),
                city=str(row.get('city', 'Unknown')),
                job=str(row.get('job', 'Unknown')),
                category=str(row.get('category', 'Unknown')),
                amount=float(row.get('amt', 0.0)),
                merchant=str(row.get('merchant', 'Unknown')).replace("fraud_", ""),
                city_pop=int(row.get('city_pop', 0)), # ดึงค่าประชากรมาเก็บไว้
                is_fraud="Yes" if int(row.get('is_fraud', 0)) == 1 else "No",
                timestamp=datetime.now() # หรือจะใช้เวลาจาก CSV ตามโค้ดเดิมของคุณก็ได้
            )
            bulk_data.append(tx)
            
        session.bulk_save_objects(bulk_data)
        session.commit()
        st.success("✅ อัปโหลดข้อมูลเริ่มต้นพร้อมข้อมูล AI เรียบร้อย!")
        
    except Exception as e:
        st.error(f"❌ Error during seeding: {e}")
        session.rollback()

def init_db():
    Base.metadata.create_all(engine)
    with Session() as session:
        if not session.query(User).filter_by(username="admin").first():
            hashed_pw = generate_password_hash("1234")
            session.add(User(username="admin", password_hash=hashed_pw))
        seed_initial_data(session)
        session.commit()

# --- 4. ฟังก์ชัน CRUD (ปรับใหม่ให้รับ city_pop) ---
def get_user(username):
    with Session() as session:
        return session.query(User).filter_by(username=username).first()

def get_transactions():
    with Session() as session:
        return session.query(Transaction).order_by(Transaction.timestamp.desc()).all()

def add_transaction(name, amount, merchant, category, is_fraud, gender, city, job, city_pop):
    with Session() as session:
        new_tx = Transaction(
            customer_name=name, amount=amount, merchant=merchant, 
            category=category, gender=gender, city=city, 
            job=job, city_pop=city_pop, is_fraud=is_fraud
        )
        session.add(new_tx)
        session.commit()
        return True

def update_transaction(tx_id, name, amount, merchant, category, is_fraud, gender, city, job, city_pop):
    with Session() as session:
        tx = session.query(Transaction).filter_by(id=tx_id).first()
        if tx:
            tx.customer_name = name
            tx.amount = amount
            tx.merchant = merchant
            tx.category = category
            tx.is_fraud = is_fraud
            tx.gender = gender
            tx.city = city
            tx.job = job
            tx.city_pop = city_pop
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

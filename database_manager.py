import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 1. ดึง URL จาก secrets
try:
    DATABASE_URL = st.secrets["SUPABASE_DB_URL"]
except Exception as e:
    st.error("⚠️ ไม่พบ DATABASE_URL ในไฟล์ secrets.toml")
    DATABASE_URL = "sqlite:///fallback.db"

# 2. สร้าง Engine เพียงครั้งเดียวพร้อมตั้งค่า SSL ให้รองรับ Cloud
# การเพิ่ม sslmode=require สำคัญมากสำหรับ Supabase
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True  # ช่วยเช็กการเชื่อมต่อก่อนดึงข้อมูล ป้องกันปัญหาเน็ตหลุด
)

Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- 3. โครงสร้างตาราง ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='admin')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    is_fraud = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

# 4. สร้างตารางบน Cloud อัตโนมัติ (ขยับมาไว้ตรงนี้เพื่อให้ใช้ engine ที่มี SSL)
try:
    Base.metadata.create_all(engine)
except Exception as e:
    st.warning(f"⚠️ ระบบสร้างตารางอัตโนมัติพบปัญหา (อาจมีตารางอยู่แล้ว): {e}")

# --- 5. ฟังก์ชันจัดการข้อมูล (เหมือนเดิม) ---
def add_transaction(customer_name, amount, merchant, is_fraud):
    with Session() as session:
        new_tx = Transaction(
            customer_name=customer_name,
            amount=amount,
            merchant=merchant,
            is_fraud=is_fraud
        )
        session.add(new_tx)
        session.commit()
        return True

def get_transactions():
    with Session() as session:
        return session.query(Transaction).order_by(Transaction.id.desc()).all()

def delete_transaction(tx_id):
    with Session() as session:
        tx = session.query(Transaction).filter_by(id=tx_id).first()
        if tx:
            session.delete(tx)
            session.commit()
            return True
        return False

def get_user(username):
    with Session() as session:
        return session.query(User).filter_by(username=username).first()

def add_user(username, password, role="admin"):
    with Session() as session:
        if session.query(User).filter_by(username=username).first():
            return False
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw, role=role)
        session.add(new_user)
        session.commit()
        return True

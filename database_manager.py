from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker # อัปเดต Path นำเข้าสำหรับ SQLAlchemy 2.0
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash # เพิ่มระบบรักษาความปลอดภัยรหัสผ่าน

# --- 1. กำหนดโครงสร้างฐานข้อมูล (Database Schema) ---
Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    merchant = Column(String, nullable=False)
    is_fraud = Column(String, nullable=False)
    # อัปเดตการใช้เวลาให้รองรับ Python เวอร์ชันใหม่ (Timezone-aware)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False) # Username ไม่ควรซ้ำกัน
    password_hash = Column(String, nullable=False) # เปลี่ยนจาก password เป็น password_hash
    role = Column(String, default="user")

    # ฟังก์ชันช่วยตรวจสอบรหัสผ่าน
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- 2. เชื่อมต่อฐานข้อมูล (Database Connection) ---
db_url = 'sqlite:///fraud_data_v2.db'
# แนะนำให้เพิ่ม check_same_thread=False สำหรับ SQLite กรณีรันบน Streamlit
engine = create_engine(db_url, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- 3. สร้างฟังก์ชันสำหรับจัดการข้อมูล (Data Manipulation Functions) ---

def add_transaction(customer_name, amount, merchant, is_fraud):
    with Session() as session:
        try:
            transaction = Transaction(
                customer_name=customer_name, 
                amount=amount, 
                merchant=merchant, 
                is_fraud=is_fraud
            )
            session.add(transaction)
            session.commit()
            return True
        except Exception as e:
            session.rollback() # ยกเลิกการบันทึกหากเกิดข้อผิดพลาด
            print(f"Error adding transaction: {e}")
            return False

def get_transactions():
    with Session() as session:
        return session.query(Transaction).all()

def get_user(username):
    with Session() as session:
        return session.query(User).filter(User.username == username).first()

def add_user(username, password, role="user"):
    with Session() as session:
        try:
            # ตรวจสอบก่อนว่ามี User นี้อยู่แล้วหรือไม่
            existing_user = session.query(User).filter(User.username == username).first()
            if existing_user:
                return False # ไม่สร้างซ้ำ

            # เข้ารหัสผ่านก่อนบันทึก
            hashed_pw = generate_password_hash(password)
            user = User(username=username, password_hash=hashed_pw, role=role)
            
            session.add(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding user: {e}")
            return False

def delete_transaction(tx_id):
    with Session() as session:
        try:
            tx_to_delete = session.query(Transaction).filter(Transaction.id == tx_id).first()
            if tx_to_delete:
                session.delete(tx_to_delete)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error deleting transaction: {e}")
            return False

# --- Initial Setup (สำหรับสร้าง Admin เบื้องต้น) ---
# คุณสามารถเอาคอมเมนต์ออกเพื่อรันสร้าง Admin User ครั้งแรกได้
# if not get_user("admin"):
#     add_user("admin", "1234", "admin")
import streamlit as st
import pandas as pd
from database_manager import get_transactions, add_transaction, delete_transaction
from seed_data import seed_transactions

# --- 0. การเตรียมข้อมูล (Seed Data) ---
# เรียกใช้ทันทีที่รันแอป เพื่อให้มั่นใจว่าบน Cloud จะมีข้อมูลโชว์เสมอ
try:
    seed_transactions()
except Exception as e:
    pass # ข้ามหากมีปัญหาเพื่อไม่ให้แอปหยุดทำงาน

# --- 1. การตั้งค่าหน้าเว็บและดีไซน์ (Modern UI) ---
st.set_page_config(page_title="Fraud Guard Pro v2.0", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; transition: 0.3s; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบจัดการสถานะการเข้าสู่ระบบ ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 3. หน้าจอ Login ---
if not st.session_state['logged_in']:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.write("") 
        st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=80)
        st.title("Fraud Guard Pro")
        st.info("กรุณาเข้าสู่ระบบเพื่อจัดการข้อมูลธุรกรรม")
        
        with st.container(border=True):
            user = st.text_input("Username", placeholder="admin")
            pw = st.text_input("Password", type="password", placeholder="••••")
            
            if st.button("Sign In", type="primary"):
                if user == "admin" and pw == "1234":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("❌ Username หรือ Password ไม่ถูกต้อง")

# --- 4. หน้าจอหลัก (เมื่อ Login สำเร็จ) ---
else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=70)
        st.subheader("Admin Control")
        st.success("สถานะ: เชื่อมต่อฐานข้อมูลแล้ว")
        st.divider()
        if st.button("🚪 Log Out", type="secondary"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.title("💳 Credit Card Fraud Analytics & Management")
    st.write("Dashboard สำหรับตรวจสอบและจัดการรายการทุจริตแบบ End-to-End")

    # --- ดึงข้อมูลจากฐานข้อมูล ---
    try:
        transactions = get_transactions()
        df = pd.DataFrame([
            {"ID": t.id, "Customer": t.customer_name, "Amount": t.amount, 
             "Merchant": t.merchant, "Fraud": t.is_fraud, 
             "Time": t.timestamp.strftime('%Y-%m-%d %H:%M')} 
            for t in transactions
        ]) if transactions else pd.DataFrame()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        df = pd.DataFrame()

    # --- ส่วนที่ 1: Metric Cards ---
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Transactions", f"{len(df):,} รายการ")
        c2.metric("Total Volume", f"฿{df['Amount'].sum():,.2f}")
        
        if 'Fraud' in df.columns:
            fraud_count = len(df[df['Fraud'] == 'Yes'])
            fraud_pct = (fraud_count / len(df) * 100) if len(df) > 0 else 0
            c3.metric("Fraud Detected", f"{fraud_count:,} รายการ", delta=f"{fraud_pct:.1f}%", delta_color="inverse")
        
        c4.metric("Avg. Transaction", f"฿{df['Amount'].mean():,.0f}")
    else:
        st.info("💡 ระบบกำลังเตรียมข้อมูลเริ่มต้น...")
        
    st.divider()

    # --- ส่วนที่ 2: Tabs ฟังก์ชันการทำงาน ---
    tab_log, tab_add, tab_manage = st.tabs(["📋 Transaction Log", "➕ New Entry", "⚙️ Data Management"])

    with tab_log:
        st.subheader("Data Explorer")
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_add:
        st.subheader("Add New Transaction")
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("ชื่อลูกค้า")
                amt = st.number_input("ยอดเงิน (บาท)", min_value=0.0, step=100.0)
            with col_b:
                merch = st.text_input("ชื่อร้านค้า")
            
            risk_suggested = "No"
            risk_label = "✅ ปกติ"
            if amt > 45000:
                risk_suggested = "Yes"
                risk_label = "🚨 เสี่ยง: ยอดเงินสูงผิดปกติ"
            elif merch.lower().strip() in ['apple store', 'gold shop', 'casino', 'jewelry']:
                risk_suggested = "Yes"
                risk_label = "🚨 เสี่ยง: ร้านค้าความเสี่ยงสูง"
            
            st.markdown(f"**การวิเคราะห์ระบบ:** <span style='color:{'red' if risk_suggested == 'Yes' else 'green'}'>{risk_label}</span>", unsafe_allow_html=True)
            fraud_final = st.selectbox("ยืนยันสถานะ", ["No", "Yes"], index=(0 if risk_suggested == "No" else 1))

            if st.button("💾 บันทึกลงฐานข้อมูล", type="primary"):
                if name.strip() and merch.strip() and amt > 0:
                    try:
                        add_transaction(name, amt, merch, fraud_final)
                        st.toast("บันทึกข้อมูลสำเร็จ!", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"บันทึกข้อมูลล้มเหลว: {e}")
                else:
                    st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

    with tab_manage:
        st.subheader("Danger Zone")
        st.write("ลบข้อมูลออกจากฐานข้อมูล")
        col_id, col_btn = st.columns([1, 2])
        with col_id:
            del_id = st.number_input("ใส่ ID ที่ต้องการลบ", min_value=1, step=1)
        with col_btn:
            st.write("") 
            st.write("")
            if st.button("🗑️ ยืนยันการลบ", type="primary"):
                if not df.empty and del_id in df['ID'].values:
                    try:
                        delete_transaction(del_id)
                        st.toast(f"ลบข้อมูล ID {del_id} สำเร็จ!", icon="🗑️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"ลบข้อมูลล้มเหลว: {e}")
                else:
                    st.error(f"ไม่พบข้อมูล ID {del_id}")
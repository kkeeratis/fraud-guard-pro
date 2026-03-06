import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
from database_manager import (init_db, get_user, get_transactions, 
                              add_transaction, update_transaction, delete_transaction, engine)

# --- 1. ตั้งค่าหน้าจอและ CSS ---
st.set_page_config(page_title="Fraud Guard AI Enterprise", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-left: 5px solid #0052cc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        padding: 15px;
        border-radius: 10px;
    }
    .main-title { color: #1e3a8a; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# เริ่มการทำงาน Database
init_db()

# --- 2. โหลด AI Model & Encoders (แคชไว้เพื่อความเร็ว) ---
@st.cache_resource
def load_ai_assets():
    try:
        model = joblib.load('fraud_model_v2.pkl')
        le_cat = joblib.load('le_category.pkl')
        le_gen = joblib.load('le_gender.pkl')
        le_job = joblib.load('le_job.pkl')
        return model, le_cat, le_gen, le_job
    except Exception as e:
        st.error(f"Error loading AI models: {e}")
        return None, None, None, None

model, le_cat, le_gen, le_job = load_ai_assets()

# --- 3. ระบบ Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.write("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🛡️ Fraud Guard Login</h2>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Access System", use_container_width=True, type="primary"):
                user = get_user(u)
                if user and user.check_password(p):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
else:
    # --- 4. Sidebar Navigation ---
    with st.sidebar:
        st.markdown("<h2 class='main-title'>🛡️ FRAUD GUARD AI</h2>", unsafe_allow_html=True)
        st.caption("Predictive Risk Intelligence v2.0")
        st.divider()
        menu = st.radio("Navigation", ["📊 Executive Dashboard", "🛡️ AI Risk Screening", "⚙️ Manage Records"])
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ดึงข้อมูลจาก Database
    raw_data = get_transactions()
    df = pd.DataFrame([{
        "ID": t.id, 
        "Timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M") if t.timestamp else "", 
        "Customer": t.customer_name, 
        "Amount": t.amount,
        "Category": t.category,
        "Fraud Flag": t.is_fraud,
        "Gender": t.gender,
        "City Pop": t.city_pop,
        "Job": t.job
    } for t in raw_data]) if raw_data else pd.DataFrame()

    # --- เมนู 1: Executive Dashboard ---
    if menu == "📊 Executive Dashboard":
        st.title("Strategic Overview")
        if not df.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Transactions", f"{len(df):,}")
            m2.metric("Detected Fraud", f"{len(df[df['Fraud Flag'] == 'Yes']):,}")
            m3.metric("Total Volume", f"฿{df['Amount'].sum():,.0f}")
            m4.metric("Avg. Risk Score", f"{df['Amount'].mean():,.0f}")
            
            st.subheader("Recent Activity")
            st.dataframe(df.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No data available. Please add transactions in Risk Screening.")

    # --- เมนู 2: AI Risk Screening ---
    elif menu == "🛡️ AI Risk Screening":
        st.title("AI-Powered Risk Analysis")
        st.markdown("ระบบวิเคราะห์ความเสี่ยงด้วยโมเดล **Random Forest (Recall: 0.94)**")
        
        col_form, col_res = st.columns([1.5, 1], gap="large")
        
        with col_form:
            with st.container(border=True):
                st.subheader("Transaction Details")
                c_name = st.text_input("Customer Name")
                c_amt = st.number_input("Transaction Amount (THB)", min_value=0.0, step=100.0)
                
                # ฟิลด์ที่ AI ต้องการ
                f1, f2 = st.columns(2)
                c_cat = f1.selectbox("Category", le_cat.classes_)
                c_gen = f2.selectbox("Gender", le_gen.classes_)
                
                f3, f4 = st.columns(2)
                c_pop = f3.number_input("City Population", min_value=0, value=15000)
                c_job = f4.selectbox("Job Title", le_job.classes_)
                
                c_merch = st.text_input("Merchant Name")

        with col_res:
            st.subheader("AI Prediction")
            if c_amt > 0 and model:
                # แปลงข้อมูลเป็นเลข (Encoding)
                input_df = pd.DataFrame([[
                    le_cat.transform([c_cat])[0],
                    c_amt,
                    le_gen.transform([c_gen])[0],
                    c_pop,
                    le_job.transform([c_job])[0]
                ]], columns=['category', 'amt', 'gender', 'city_pop', 'job'])
                
                # ทำนาย
                prob = model.predict_proba(input_df)[0][1]
                
                st.metric("Fraud Probability", f"{prob*100:.2f}%")
                st.progress(prob)
                
                if prob > 0.5:
                    st.error("🚨 HIGH RISK DETECTED")
                    status = "Yes"
                else:
                    st.success("✅ LOW RISK TRANSACTION")
                    status = "No"
                
                if st.button("Confirm & Save to Cloud", type="primary", use_container_width=True):
                    if c_name:
                        # บันทึกลง PostgreSQL (เพิ่มฟิลด์ city_pop ในฟังก์ชัน add_transaction ด้วย)
                        add_transaction(c_name, c_amt, c_merch, c_cat, status, c_gen, "N/A", c_job, c_pop)
                        st.success("Record secured in PostgreSQL!")
                        st.rerun()
            else:
                st.info("Waiting for transaction details...")

    # --- เมนู 3: Manage Records ---
    elif menu == "⚙️ Manage Records":
        st.title("System Records Management")
        if not df.empty:
            target_id = st.selectbox("Select ID to Delete", df['ID'].tolist())
            if st.button("Permanently Delete Record", type="primary"):
                delete_transaction(target_id)
                st.warning(f"Record {target_id} deleted.")
                st.rerun()
        else:
            st.info("Database is empty.")

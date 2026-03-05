import streamlit as st
import pandas as pd
from database_manager import (init_db, get_user, get_transactions, 
                              add_transaction, update_transaction, delete_transaction)

# --- 1. ตั้งค่าหน้าจอและ CSS (Enterprise Look) ---
st.set_page_config(page_title="Fraud Guard Enterprise", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 5% 5% 5% 10%;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0052cc;
    }
    .stApp { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

# เริ่มการทำงาน Database
init_db()

# --- 2. ระบบประเมินความเสี่ยง (Risk Engine) ---
def calculate_risk(amount, category):
    score = 0
    reasons = []
    
    if amount > 45000:
        score += 50
        reasons.append("ยอดเงินสูงผิดปกติ (>฿45,000)")
    elif amount > 15000:
        score += 20
        reasons.append("ยอดเงินค่อนข้างสูง (>฿15,000)")
        
    high_risk_categories = ['misc_net', 'shopping_net', 'grocery_pos']
    if category in high_risk_categories:
        score += 30
        reasons.append("หมวดหมู่การใช้จ่ายมีความเสี่ยงสูงทางสถิติ")
        
    score = min(score, 100)
    if score >= 70: return score, "High", reasons, "🔴"
    elif score >= 40: return score, "Medium", reasons, "🟡"
    return score, "Low", ["พฤติกรรมการใช้จ่ายปกติ"], "🟢"

# --- 3. ระบบ Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.write("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ Fraud Guard Pro</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748b;'>Enter credentials to access the system</p>", unsafe_allow_html=True)
            
            u = st.text_input("Username", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="1234")
            if st.button("Authenticate", use_container_width=True, type="primary"):
                user = get_user(u)
                if user and user.check_password(p):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
else:
    # --- 4. Main Dashboard ---
    raw_data = get_transactions()
    
    # แปลงข้อมูลเป็น DataFrame สำหรับแสดงผล
    df = pd.DataFrame([{
        "ID": t.id, 
        "Timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M") if t.timestamp else "", 
        "Customer": t.customer_name, 
        "Gender": t.gender,
        "City": t.city,
        "Job": t.job,
        "Category": t.category,
        "Merchant": t.merchant, 
        "Amount (THB)": t.amount, 
        "Fraud Flag": t.is_fraud
    } for t in raw_data]) if raw_data else pd.DataFrame()

    with st.sidebar:
        st.markdown("### 🏢 Core Modules")
        menu = st.radio("Navigation", ["📊 Data Overview", "🛡️ Risk Screening", "⚙️ Manage Records"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- เมนู 1: ดูข้อมูลทั้งหมด ---
    if menu == "📊 Data Overview":
        st.title("Data Overview & Analytics")
        st.markdown("ฐานข้อมูลธุรกรรมระดับ Enterprise เตรียมพร้อมสำหรับการเชื่อมต่อ Power BI")
        
        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Records", f"{len(df):,}")
            c2.metric("Flagged Fraud", f"{len(df[df['Fraud Flag'] == 'Yes']):,}")
            c3.metric("Total Volume", f"฿ {df['Amount (THB)'].sum():,.0f}")
            c4.metric("Avg. Ticket Size", f"฿ {df['Amount (THB)'].mean():,.0f}")
            
            st.write("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.dataframe(df, use_container_width=True, hide_index=True, height=500)
        else:
            st.info("No transaction records found.")

    # --- เมนู 2: เพิ่มข้อมูลและประเมินความเสี่ยง ---
    elif menu == "🛡️ Risk Screening":
        st.title("Live Risk Screening Entry")
        st.markdown("เพิ่มรายการธุรกรรมใหม่ ระบบจะประเมินความเสี่ยงให้ทันที")
        
        col_form, col_risk = st.columns([1.5, 1], gap="large")
        with col_form:
            with st.container(border=True):
                new_name = st.text_input("Customer Name")
                new_amt = st.number_input("Transaction Amount (THB)", min_value=0.0, step=1000.0)
                categories = ['misc_net', 'grocery_pos', 'entertainment', 'gas_transport', 'shopping_pos', 'grocery_net', 'shopping_net', 'misc_pos', 'travel']
                new_cat = st.selectbox("Category Classification", categories)
                new_merch = st.text_input("Merchant Name", placeholder="e.g. Apple Store")
                new_status = st.selectbox("Final System Flag", ["No", "Yes"])
                
                if st.button("Save Transaction", type="primary", use_container_width=True):
                    if new_name and new_amt > 0 and new_merch:
                        add_transaction(new_name, new_amt, new_merch, new_cat, new_status)
                        st.success("Transaction recorded successfully!")
                        st.rerun()
                    else:
                        st.error("Please complete all required fields.")

        with col_risk:
            with st.container(border=True):
                st.markdown("#### 📡 Live Risk Engine")
                if new_amt > 0:
                    score, level, reasons, icon = calculate_risk(new_amt, new_cat)
                    st.markdown(f"**Risk Score:** {score}/100")
                    st.progress(score / 100)
                    st.markdown(f"**Risk Level:** {icon} {level}")
                    for r in reasons:
                        st.markdown(f"- <span style='color: #555;'>{r}</span>", unsafe_allow_html=True)
                else:
                    st.info("Waiting for inputs...")

    # --- เมนู 3: แก้ไขและลบข้อมูล ---
    elif menu == "⚙️ Manage Records":
        st.title("Record Management")
        
        if not df.empty:
            with st.container(border=True):
                target_id = st.selectbox("Select Transaction ID to Modify", df['ID'].tolist())
                
                if target_id:
                    tx_data = df[df['ID'] == target_id].iloc[0]
                    st.markdown("---")
                    
                    c1, c2 = st.columns(2)
                    upd_name = c1.text_input("Customer Name", value=tx_data['Customer'])
                    upd_amt = c2.number_input("Amount (THB)", value=float(tx_data['Amount (THB)']))
                    upd_merch = c1.text_input("Merchant", value=tx_data['Merchant'])
                    upd_cat = c2.text_input("Category", value=tx_data['Category'])
                    upd_status = c1.selectbox("Fraud Flag", ["No", "Yes"], index=0 if tx_data['Fraud Flag'] == "No" else 1)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    btn_upd, btn_del, _ = st.columns([1, 1, 2])
                    
                    if btn_upd.button("Update Record", type="primary", use_container_width=True):
                        update_transaction(target_id, upd_name, upd_amt, upd_merch, upd_cat, upd_status)
                        st.success(f"Record updated!")
                        st.rerun()
                        
                    if btn_del.button("Delete Record", use_container_width=True):
                        delete_transaction(target_id)
                        st.warning(f"Record deleted!")
                        st.rerun()
        else:
            st.info("Database is empty.")
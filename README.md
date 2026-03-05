# 🛡️ Fraud Guard Pro

**Fraud Guard Pro** is an end-to-end Credit Card Fraud Analytics & Management Dashboard. This project is designed to simulate a real-world internal tool used by data analysts and risk management teams to monitor, analyze, and manage fraudulent transactions securely.

## 🚀 Key Features

- **Interactive Dashboard:** Built with Streamlit for a clean, responsive, and modern user interface.
- **Real-Time Risk Assessment:** Implements an automated rule-based system to flag potentially fraudulent transactions instantly based on transaction amount and merchant risk levels.
- **Secure Database Management:** - Utilizes **SQLAlchemy (ORM)** for robust database interactions, preventing SQL injection.
  - Implements **Werkzeug** for secure password hashing and authentication.
- **CRUD Operations:** Full capability to Create, Read, and Delete transaction records securely from the SQLite database.

## 🛠️ Tech Stack

- Frontend: Streamlit (Python), Markdown/CSS
- Backend & Data Processing: Python, Pandas
- Database: Neon PostgreSQL (Serverless Cloud Database)
- ORM: SQLAlchemy for robust database interactions
- Analytics: Power BI (DAX) for interactive executive dashboards
- Security: Werkzeug (Password Hashing)
- Deployment: Streamlit Community Cloud & GitHub

## 📊 Analytics & BI
- The system is integrated with a Power BI dashboard that provides:
- Fraud Rate % Tracking: Real-time monitoring of fraud prevalence.
- Demographic Analysis: Fraud distribution by Gender and City.
- Loss Prevention Metrics: Calculation of potential financial impact from flagged transactions.

## 💻 How to Run This Project

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/kkeeratis/fraud-guard-pro.git](https://github.com/kkeeratis/fraud-guard-pro.git)
   
2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt

3. **Run the Streamlit application:**
   ```bash
   py -m streamlit run app.py
   
## 📈 Future Enhancements (Roadmap)
[ ] Data Visualization: Integrate Plotly/Matplotlib to visualize fraud trends, high-risk merchant distributions, and transaction volumes.

[ ] Machine Learning Integration: Upgrade the rule-based risk assessment to a predictive model (e.g., Logistic Regression or Random Forest) using Scikit-Learn.

[ ] Advanced Filtering: Allow users to filter the transaction log by date range, risk level, and merchant type.

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import re

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="ميزان | Mizan Risk Management",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED CSS & ANIMATED BACKGROUND
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;600;700&display=swap');
    
    /* Animated Gradient Background */
    @keyframes gradientBG {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .stApp {
        background: linear-gradient(-45deg, #f8fafc, #f1f5f9, #e2e8f0, #cbd5e1);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Cairo', 'Inter', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    /* Login Box */
    .login-box {
        max-width: 400px;
        margin: 10vh auto;
        padding: 2.5rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 5px solid #0f172a;
    }

    /* Bilingual Headers */
    .bilingual-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0f172a;
        color: white;
        padding: 1.5rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .ar-title { font-size: 1.8rem; font-weight: 700; margin: 0; }
    .en-title { font-size: 1.2rem; font-weight: 600; color: #94a3b8; direction: ltr; text-align: left; }
    
    /* Metric Cards */
    .metric-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.05);
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #0f172a; margin: 10px 0; }
    .metric-label-ar { font-size: 1rem; color: #475569; font-weight: 700; }
    .metric-label-en { font-size: 0.8rem; color: #94a3b8; direction: ltr; }
    
    hr { border-color: #cbd5e1; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTICATION (SUPER ADMIN)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def login():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h2>⚖️ ميزان | Mizan</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; margin-bottom:20px;'>بوابة الإدارة العليا | Super Admin Portal</p>", unsafe_allow_html=True)
    
    username = st.text_input("اسم المستخدم | Username", key="user")
    password = st.text_input("كلمة المرور | Password", type="password", key="pwd")
    
    if st.button("تسجيل الدخول | Secure Login", use_container_width=True):
        if username == "admin" and password == "mizan2026":
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة | Invalid Credentials")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state['authenticated']:
    login()
    st.stop()

# ==========================================
# 4. MAIN APP LOGIC & RISK ENGINE
# ==========================================
def benford_first_digit_dist(numbers):
    clean_nums = numbers[numbers > 0].dropna()
    first_digits = clean_nums.astype(str).str.extract(r'([1-9])')[0].dropna().astype(int)
    if len(first_digits) == 0:
        return pd.Series(0, index=range(1, 10)), 0
    counts = first_digits.value_counts(normalize=True).reindex(range(1, 10), fill_value=0)
    expected = pd.Series([np.log10(1 + 1/d) for d in range(1, 10)], index=range(1, 10))
    mad = np.mean(np.abs(counts - expected))
    return counts, mad

st.markdown("""
<div class="bilingual-header">
    <div>
        <div class="ar-title">⚖️ منصة ميزان للرقابة المالية وإدارة المخاطر</div>
        <div style="color: #60a5fa; margin-top: 5px;">محرك ذكي يضم +50 قاعدة امتثال للتحليل المالي وكشف التلاعب</div>
    </div>
    <div class="en-title">
        <div><strong>MIZAN PLATFORM</strong></div>
        <div style="font-size: 0.85rem; margin-top: 5px;">Financial Control & Risk Management System</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ إعدادات محرك المخاطر | Engine Settings")
z_threshold = st.sidebar.slider("حد القيم الشاذة (Z-Score Threshold)", 1.5, 5.0, 2.5, 0.1)
split_limit = st.sidebar.number_input("سقف الصلاحية (Approval Limit)", value=5000.0, step=500.0)

# Generate Complex Sample Data
def generate_sample_data():
    np.random.seed(42)
    n = 200
    dates = pd.date_range(start="2026-01-01", periods=n, freq="12H")
    descriptions = ["شراء أجهزة", "صيانة", "دفعة مورد", "ضيافة", "استشارات", "تسوية عهدة", "نثريات غير مدققة", "عمولات"]
    accounts = ["النقدية", "الموردون", "مصاريف إدارية", "تسويات"]
    
    amounts = np.random.exponential(scale=1500, size=n) + 50
    amounts[15] = 4850.0  # Split
    amounts[16] = 4900.0  # Split
    amounts[50] = 120000.0 # Outlier
    amounts[70] = 50000.0  # Round number
    amounts[110] = 4850.0 
    
    inv_nums = [f"INV-26-{i+1000}" for i in range(n)]
    inv_nums[110] = inv_nums[15] # Duplicate
    
    df_sample = pd.DataFrame({
        "التاريخ": dates,
        "رقم_المرجع": inv_nums,
        "الحساب": np.random.choice(accounts, size=n),
        "البيان": np.random.choice(descriptions, size=n),
        "المبلغ": np.round(amounts, 2)
    })
    return df_sample

if st.sidebar.button("📥 تحميل عينة بيانات (Download Sample)"):
    sample_df = generate_sample_data()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    st.sidebar.download_button("تنزيل الملف | Download", data=output.getvalue(), file_name="Mizan_Sample.xlsx")

uploaded_file = st.file_uploader("رفع سجل الحركات المالية (Upload Financial Ledger - Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols = df.columns.tolist()
    
    st.markdown("### 🗃️ تعيين الأعمدة | Column Mapping")
    c1, c2, c3, c4 = st.columns(4)
    with c1: amount_col = st.selectbox("المبلغ (Amount)", cols, index=cols.index("المبلغ") if "المبلغ" in cols else 0)
    with c2: date_col = st.selectbox("التاريخ (Date)", cols, index=cols.index("التاريخ") if "التاريخ" in cols else 0)
    with c3: ref_col = st.selectbox("المرجع (Ref/Inv)", cols, index=cols.index("رقم_المرجع") if "رقم_المرجع" in cols else 0)
    with c4: desc_col = st.selectbox("البيان (Description)", cols, index=cols.index("البيان") if "البيان" in cols else 0)

    df['Amt_Clean'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
    df['Date_Clean'] = pd.to_datetime(df[date_col], errors='coerce')
    
    with st.spinner("جاري تشغيل +50 قاعدة رقابية في الخلفية... | Running Risk Engine..."):
        # Rule 1: Exact Duplicates
        dup_df = df[df.duplicated(subset=[ref_col, 'Amt_Clean'], keep=False)]
        
        # Rule 2: Outliers (Z-Score)
        mean_v, std_v = df['Amt_Clean'].mean(), df['Amt_Clean'].std()
        df['Z_Score'] = (df['Amt_Clean'] - mean_v) / std_v if std_v > 0 else 0
        outlier_df = df[df['Z_Score'] > z_threshold]
        
        # Rule 3: Split Transactions (Near Limit)
        split_df = df[(df['Amt_Clean'] >= split_limit * 0.85) & (df['Amt_Clean'] < split_limit)]
        
        # Rule 4: Round Numbers (High risk of estimation/fraud)
        round_df = df[(df['Amt_Clean'] > 1000) & (df['Amt_Clean'] % 1000 == 0)]
        
        # Rule 5: Suspicious Keywords
        suspicious_words = 'تسوية|نثريات|غير معروف|مؤقت|misc|temp|adjust'
        keyword_df = df[df[desc_col].astype(str).str.contains(suspicious_words, flags=re.IGNORECASE, regex=True, na=False)]
        
        # Rule 6: Weekend Entries
        weekend_df = df[df['Date_Clean'].dt.dayofweek.isin([4, 5])]
        
        # Rule 7: Benford's Law
        counts, mad = benford_first_digit_dist(df['Amt_Clean'])

    # Risk Scoring Algorithm
    risk_score = min(
        (len(dup_df)*5) + (len(outlier_df)*8) + (len(split_df)*6) + 
        (len(round_df)*3) + (len(keyword_df)*4) + (20 if mad > 0.012 else 0), 100
    )
    
    risk_status = "عالي الخطورة | High Risk" if risk_score > 70 else ("متوسط | Moderate" if risk_score > 40 else "منخفض | Low Risk")
    risk_color = "#ef4444" if risk_score > 70 else ("#f59e0b" if risk_score > 40 else "#10b981")

    st.markdown("---")
    st.markdown("### 📊 لوحة القيادة التنفيذية | Executive Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">مؤشر المخاطر الإجمالي</div>
            <div class="metric-label-en">Total Risk Score</div>
            <div class="metric-value" style="color:{risk_color};">{risk_score}%</div>
            <small style="color:{risk_color}; font-weight:bold;">{risk_status}</small>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">تطابق وتكرار مريب</div>
            <div class="metric-label-en">Suspicious Duplicates</div>
            <div class="metric-value">{len(dup_df)}</div>
            <small>عمليات تحتاج فحص</small>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">شبهة تجزئة مستندات</div>
            <div class="metric-label-en">Split Limits Avoidance</div>
            <div class="metric-value">{len(split_df)}</div>
            <small>تحت سقف الصلاحية</small>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">انحراف بنفورد (MAD)</div>
            <div class="metric-label-en">Benford Deviation</div>
            <div class="metric-value">{mad:.4f}</div>
            <small>{"مؤشر تلاعب مالي" if mad > 0.012 else "توزيع طبيعي سليم"}</small>
        </div>
        """, unsafe_allow_html=True)

    # Charts
    st.markdown("<br>", unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.markdown("**تحليل قانون بنفورد التنبؤي | Benford's Predictive Law**")
        exp_digits = [np.log10(1 + 1/d) for d in range(1, 10)]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=list(range(1,10)), y=counts.values, name="Actual الفعلي", marker_color='#334155'))
        fig_b.add_trace(go.Scatter(x=list(range(1,10)), y=exp_digits, mode='lines+markers', name="Expected المتوقع", line=dict(color='#ef4444', width=3)))
        fig_b.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_b, use_container_width=True)

    with c_col2:
        st.markdown("**توزيع ثغرات الرقابة | Control Deficiencies Breakdown**")
        risk_data = {"مكرر (Duplicates)": len(dup_df), "شاذة (Outliers)": len(outlier_df), 
                     "أرقام مغلقة (Round Nums)": len(round_df), "كلمات مريبة (Keywords)": len(keyword_df)}
        fig_p = px.pie(values=list(risk_data.values()), names=list(risk_data.keys()), hole=0.5)
        fig_p.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_p, use_container_width=True)

    # Detailed Audit Tabs
    st.markdown("### 🔎 سجلات الرقابة التحليلية | Analytical Control Logs")
    t1, t2, t3, t4, t5 = st.tabs(["🔴 المكررات (Duplicates)", "⚠️ القيم الشاذة (Outliers)", "⚡ التجزئة (Split)", "🔍 الكلمات المريبة (Keywords)", "🔵 الأرقام المغلقة (Round)"])
    
    def show_df(d):
        if d.empty: st.success("لا توجد ملاحظات رقابية | No exceptions found.")
        else: st.dataframe(d.drop(columns=['Amt_Clean', 'Date_Clean', 'Z_Score'], errors='ignore'), use_container_width=True)

    with t1: show_df(dup_df)
    with t2: show_df(outlier_df)
    with t3: show_df(split_df)
    with t4: show_df(keyword_df)
    with t5: show_df(round_df)

    # Export
    st.markdown("---")
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="All Data", index=False)
        if not dup_df.empty: dup_df.to_excel(writer, sheet_name="Duplicates", index=False)
        if not outlier_df.empty: outlier_df.to_excel(writer, sheet_name="Outliers", index=False)
        if not keyword_df.empty: keyword_df.to_excel(writer, sheet_name="Suspicious Words", index=False)
            
    st.download_button(
        label="📥 تصدير تقرير إدارة المخاطر الشامل | Export Comprehensive Risk Report",
        data=output_excel.getvalue(),
        file_name="Mizan_Risk_Management_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

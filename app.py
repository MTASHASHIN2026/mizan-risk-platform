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
    page_title="منصة ميزان | Mizan Risk Management",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CLEAN & PROFESSIONAL STYLING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Inter', sans-serif;
        direction: rtl;
    }
    
    .stApp {
        background-color: #f8fafc;
    }

    /* Bilingual Header */
    .bilingual-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0f172a;
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .ar-title { font-size: 1.6rem; font-weight: 700; margin: 0; }
    .en-title { font-size: 1rem; font-weight: 600; color: #94a3b8; direction: ltr; text-align: left; }
    
    /* Metric Cards */
    .metric-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #0f172a; margin: 5px 0; }
    .metric-label-ar { font-size: 0.95rem; color: #334155; font-weight: 700; }
    .metric-label-en { font-size: 0.8rem; color: #64748b; direction: ltr; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. AUTHENTICATION (SUPER ADMIN)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, col_login, c2 = st.columns([1, 1.5, 1])
    
    with col_login:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 14px; border-top: 5px solid #0f172a; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); text-align: center;">
            <h2 style="margin-bottom: 5px;">⚖️ منصة ميزان | Mizan Platform</h2>
            <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 25px;">منظومة الرقابة المالية وإدارة المخاطر (Super Admin Portal)</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم | Username")
            password = st.text_input("كلمة المرور | Password", type="password")
            submit = st.form_submit_button("تسجيل الدخول | Secure Login", use_container_width=True)
            
            if submit:
                if username == "admin" and password == "mizan2026":
                    st.session_state['authenticated'] = True
                    st.success("تم تسجيل الدخول بنجاح")
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة | Invalid Credentials")
    st.stop()

# ==========================================
# 4. MAIN DASHBOARD & RISK ENGINE
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
        <div style="color: #60a5fa; margin-top: 4px; font-size: 0.9rem;">محرك ذكي مدمج لتقييم الامتثال وكشف مؤشرات المخاطر المالية</div>
    </div>
    <div class="en-title">
        <div><strong>MIZAN PLATFORM</strong></div>
        <div style="font-size: 0.8rem; color: #cbd5e1;">Financial Control & Enterprise Risk Analytics</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ إعدادات محرك المخاطر | Control Settings")
z_threshold = st.sidebar.slider("حد القيم الشاذة (Z-Score Threshold)", 1.5, 5.0, 2.5, 0.1)
split_limit = st.sidebar.number_input("سقف الصلاحية المعتمد (Authorization Limit)", value=5000.0, step=500.0)

# Sample Data Generator
def generate_sample_data():
    np.random.seed(42)
    n = 180
    dates = pd.date_range(start="2026-01-01", periods=n, freq="D")
    descriptions = ["شراء مستلزمات", "صيانة تشغيلية", "دفعة مورد", "ضيافة رسمية", "استشارات قانونية", "نثريات وتسويات"]
    accounts = ["101 - النقدية", "201 - الموردون", "501 - مصروفات عامة"]
    
    amounts = np.random.exponential(scale=1800, size=n) + 100
    amounts[10] = 4850.0 
    amounts[11] = 4900.0 
    amounts[30] = 115000.0 
    amounts[50] = 30000.0 
    amounts[70] = 4850.0  
    
    inv_nums = [f"INV-26-{i+1000}" for i in range(n)]
    inv_nums[70] = inv_nums[10] 
    
    return pd.DataFrame({
        "التاريخ": dates,
        "رقم_المرجع": inv_nums,
        "الحساب": np.random.choice(accounts, size=n),
        "البيان": np.random.choice(descriptions, size=n),
        "المبلغ": np.round(amounts, 2)
    })

st.sidebar.markdown("---")
if st.sidebar.button("📥 تحميل نموذج Excel تجريبي"):
    sample_df = generate_sample_data()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    st.sidebar.download_button("تنزيل الملف النموذج", data=output.getvalue(), file_name="Mizan_Risk_Sample.xlsx")

uploaded_file = st.file_uploader("قم برفع كشف الحركات المالية (Excel File)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols = df.columns.tolist()
    
    st.markdown("### 🗃️ تعيين الأعمدة | Column Mapping")
    c1, c2, c3, c4 = st.columns(4)
    with c1: amount_col = st.selectbox("المبلغ (Amount):", cols, index=cols.index("المبلغ") if "المبلغ" in cols else 0)
    with c2: date_col = st.selectbox("التاريخ (Date):", cols, index=cols.index("التاريخ") if "التاريخ" in cols else 0)
    with c3: ref_col = st.selectbox("المرجع (Reference):", cols, index=cols.index("رقم_المرجع") if "رقم_المرجع" in cols else 0)
    with c4: desc_col = st.selectbox("البيان (Description):", cols, index=cols.index("البيان") if "البيان" in cols else 0)

    df['Amt_Clean'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
    df['Date_Clean'] = pd.to_datetime(df[date_col], errors='coerce')
    
    # RISK CALCULATIONS
    dup_df = df[df.duplicated(subset=[ref_col, 'Amt_Clean'], keep=False)]
    
    mean_v, std_v = df['Amt_Clean'].mean(), df['Amt_Clean'].std()
    df['Z_Score'] = (df['Amt_Clean'] - mean_v) / std_v if std_v > 0 else 0
    outlier_df = df[df['Z_Score'] > z_threshold]
    
    split_df = df[(df['Amt_Clean'] >= split_limit * 0.85) & (df['Amt_Clean'] < split_limit)]
    round_df = df[(df['Amt_Clean'] > 1000) & (df['Amt_Clean'] % 1000 == 0)]
    
    suspicious_words = 'تسوية|نثريات|مؤقت|misc|temp|adjust'
    keyword_df = df[df[desc_col].astype(str).str.contains(suspicious_words, flags=re.IGNORECASE, regex=True, na=False)]
    
    counts, mad = benford_first_digit_dist(df['Amt_Clean'])

    # RISK SCORE COMPUTATION
    risk_score = min(
        (len(dup_df)*5) + (len(outlier_df)*8) + (len(split_df)*6) + 
        (len(round_df)*3) + (len(keyword_df)*4) + (20 if mad > 0.012 else 0), 100
    )
    
    risk_status = "عالي الخطورة | High Risk" if risk_score > 70 else ("متوسط | Moderate" if risk_score > 40 else "منخفض | Low Risk")
    risk_color = "#ef4444" if risk_score > 70 else ("#f59e0b" if risk_score > 40 else "#10b981")

    st.markdown("---")
    st.markdown("### 📊 لوحة المؤشرات التنفيذية | Executive Risk Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">درجة المخاطر الإجمالية</div>
            <div class="metric-label-en">Overall Risk Score</div>
            <div class="metric-value" style="color:{risk_color};">{risk_score}%</div>
            <small style="color:{risk_color}; font-weight:bold;">{risk_status}</small>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">قيود مكررة مريبة</div>
            <div class="metric-label-en">Duplicates Flagged</div>
            <div class="metric-value">{len(dup_df)}</div>
            <small>تكرار المبلغ والمرجع</small>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">شبهة تجزئة مبالغ</div>
            <div class="metric-label-en">Authorization Splitting</div>
            <div class="metric-value">{len(split_df)}</div>
            <small>قريبة من سقف الصلاحية</small>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">انحراف قانون بنفورد</div>
            <div class="metric-label-en">Benford Deviation (MAD)</div>
            <div class="metric-value">{mad:.4f}</div>
            <small>{"مؤشر تلاعب" if mad > 0.012 else "توزيع طبيعي"}</small>
        </div>
        """, unsafe_allow_html=True)

    # VISUALIZATIONS
    st.markdown("<br>", unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.markdown("#### 1. تحليل قانون بنفورد | Benford's Law Chart")
        exp_digits = [np.log10(1 + 1/d) for d in range(1, 10)]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=list(range(1,10)), y=counts.values, name="الفعلي (Actual)", marker_color='#2563eb'))
        fig_b.add_trace(go.Scatter(x=list(range(1,10)), y=exp_digits, mode='lines+markers', name="المتوقع (Expected)", line=dict(color='#dc2626', width=3)))
        fig_b.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_b, use_container_width=True)

    with c_col2:
        st.markdown("#### 2. توزيع الملاحظات الرقابية | Risk Breakdown")
        risk_data = {
            "قيود مكررة": len(dup_df), 
            "قيم استثنائية": len(outlier_df), 
            "أرقام مدورة": len(round_df), 
            "كلمات مريبة": len(keyword_df)
        }
        fig_p = px.pie(values=list(risk_data.values()), names=list(risk_data.keys()), hole=0.45)
        fig_p.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_p, use_container_width=True)

    # TABS FOR DETAILED AUDIT LOGS
    st.markdown("### 🔎 سجل التفاصيل والقيود الشاخصة | Risk Audit Logs")
    t1, t2, t3, t4, t5 = st.tabs(["🔴 القيود المكررة", "⚠️ القيم الشاذة", "⚡ شبهة التجزئة", "🔍 الكلمات المريبة", "🔵 الأرقام المغلقة"])
    
    def render_tab_df(data_frame):
        if data_frame.empty:
            st.success("لا توجد ملاحظات رقابية في هذا القسم | No risks detected.")
        else:
            st.dataframe(data_frame.drop(columns=['Amt_Clean', 'Date_Clean', 'Z_Score'], errors='ignore'), use_container_width=True)

    with t1: render_tab_df(dup_df)
    with t2: render_tab_df(outlier_df)
    with t3: render_tab_df(split_df)
    with t4: render_tab_df(keyword_df)
    with t5: render_tab_df(round_df)

    # EXPORT REPORT
    st.markdown("---")
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="الكشف الكامل", index=False)
        if not dup_df.empty: dup_df.to_excel(writer, sheet_name="القيود المكررة", index=False)
        if not outlier_df.empty: outlier_df.to_excel(writer, sheet_name="القيم الشاخصة", index=False)
            
    st.download_button(
        label="📥 تصدير التقرير الرقابي الشامل (Excel Report)",
        data=output_excel.getvalue(),
        file_name="Mizan_Risk_Audit_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

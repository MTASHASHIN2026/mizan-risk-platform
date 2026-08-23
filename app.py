import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import re

# ==========================================
# 1. إعدادات الصفحة والتصميم الأساسي
# ==========================================
st.set_page_config(
    page_title="منصة ميزان | Mizan Risk Management",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', 'Inter', sans-serif; direction: rtl; }
    .stApp { background-color: #f8fafc; }
    
    .bilingual-header {
        display: flex; justify-content: space-between; align-items: center;
        background: #0f172a; color: white; padding: 1.5rem 2rem;
        border-radius: 12px; margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background-color: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 1.2rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #0f172a; margin: 5px 0; }
    .metric-label-ar { font-size: 1rem; color: #334155; font-weight: 700; }
    .metric-label-en { font-size: 0.8rem; color: #64748b; direction: ltr; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. نظام تسجيل الدخول الآمن (Super Admin)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, col_login, c2 = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown("""
        <div style="background: white; padding: 2.5rem; border-radius: 14px; border-top: 5px solid #0f172a; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;">
            <h2 style="margin-bottom: 5px; color: #0f172a;">⚖️ منصة ميزان | Mizan</h2>
            <p style="color: #64748b; font-size: 0.95rem; margin-bottom: 25px;">بوابة الإدارة العليا للرقابة المالية وإدارة المخاطر</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم | Username")
            password = st.text_input("كلمة المرور | Password", type="password")
            if st.form_submit_button("تسجيل الدخول الآمن | Secure Login", use_container_width=True):
                if username == "admin" and password == "mizan2026":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة | Invalid Credentials")
    st.stop()

# ==========================================
# 3. دوال التحليل والتعرف الذكي
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

def auto_detect_column(columns, keywords):
    for col in columns:
        col_str = str(col).lower()
        if any(kw in col_str for kw in keywords):
            return col
    return columns[0] if len(columns) > 0 else None

# ==========================================
# 4. الواجهة الرئيسية ومحرك المخاطر
# ==========================================
st.markdown("""
<div class="bilingual-header">
    <div>
        <div style="font-size: 1.6rem; font-weight: 700;">⚖️ منصة ميزان للرقابة المالية وإدارة المخاطر</div>
        <div style="color: #60a5fa; margin-top: 4px; font-size: 0.95rem;">محرك الرقابة الذكي وقواعد كشف الاحتيال المحاسبي</div>
    </div>
    <div style="font-size: 1rem; font-weight: 600; color: #94a3b8; direction: ltr; text-align: left;">
        <div><strong>MIZAN PLATFORM</strong></div>
        <div style="font-size: 0.8rem; color: #cbd5e1;">Financial Control & Enterprise Risk Analytics</div>
    </div>
</div>
""", unsafe_allow_html=True)

# شريط الإعدادات الجانبي
st.sidebar.header("⚙️ إعدادات محرك المخاطر | Control Settings")
z_threshold = st.sidebar.slider("حد القيم الشاذة المعياري (Z-Score)", 1.5, 5.0, 3.0, 0.1)
split_limit = st.sidebar.number_input("سقف الصلاحية المعتمد (Authorization Limit)", value=5000.0, step=500.0)

uploaded_file = st.file_uploader("قم برفع كشف الحركات المالية (ملف Excel)", type=["xlsx", "xls"])

if uploaded_file:
    # قراءة وتنظيف هيكل الملف
    raw_df = pd.read_excel(uploaded_file)
    df = raw_df.dropna(how='all').dropna(how='all', axis=1)
    cols = [str(c).strip() for c in df.columns]
    df.columns = cols

    # التعرف الذكي على الأعمدة
    default_amt = auto_detect_column(cols, ['مبلغ', 'المبلغ', 'مدين', 'دائن', 'amount', 'debit', 'val'])
    default_date = auto_detect_column(cols, ['تاريخ', 'التاريخ', 'date', 'time', 'dt'])
    default_ref = auto_detect_column(cols, ['مرجع', 'سند', 'فاتورة', 'رقم', 'ref', 'inv', 'doc', 'id'])
    default_desc = auto_detect_column(cols, ['بيان', 'البيان', 'شرح', 'تفاصيل', 'desc', 'narration', 'details'])

    st.markdown("### 🗃️ تعيين وقراءة الأعمدة | Smart Column Mapping")
    c1, c2, c3, c4 = st.columns(4)
    with c1: amount_col = st.selectbox("المبلغ (Amount):", cols, index=cols.index(default_amt))
    with c2: date_col = st.selectbox("التاريخ (Date):", cols, index=cols.index(default_date))
    with c3: ref_col = st.selectbox("المرجع/رقم السند (Ref):", cols, index=cols.index(default_ref))
    with c4: desc_col = st.selectbox("البيان (Description):", cols, index=cols.index(default_desc))

    # تعقيم وتجهيز البيانات
    df['Amt_Clean'] = pd.to_numeric(df[amount_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df['Date_Clean'] = pd.to_datetime(df[date_col], errors='coerce')
    df['Ref_Clean'] = df[ref_col].astype(str).str.strip()
    valid_df = df[df['Amt_Clean'] > 0].copy()

    # تشغيل قواعد الرقابة
    dup_df = valid_df[valid_df.duplicated(subset=['Ref_Clean', 'Amt_Clean'], keep=False)]
    
    mean_v, std_v = valid_df['Amt_Clean'].mean(), valid_df['Amt_Clean'].std()
    valid_df['Z_Score'] = (valid_df['Amt_Clean'] - mean_v) / std_v if std_v > 0 else 0
    outlier_df = valid_df[valid_df['Z_Score'] > z_threshold]
    
    split_df = valid_df[(valid_df['Amt_Clean'] >= split_limit * 0.85) & (valid_df['Amt_Clean'] < split_limit)]
    round_df = valid_df[(valid_df['Amt_Clean'] > 1000) & (valid_df['Amt_Clean'] % 1000 == 0)]
    
    suspicious_words = 'تسوية|نثريات|مؤقت|misc|temp|adjust|عهدة'
    keyword_df = valid_df[valid_df[desc_col].astype(str).str.contains(suspicious_words, flags=re.IGNORECASE, regex=True, na=False)]
    
    counts, mad = benford_first_digit_dist(valid_df['Amt_Clean'])

    # حساب مؤشر المخاطر الإجمالي
    dup_p = min(len(dup_df) * 2, 25)
    outlier_p = min(len(outlier_df) * 5, 25)
    split_p = min(len(split_df) * 4, 20)
    round_p = min(len(round_df) * 2, 10)
    benford_p = 20 if mad > 0.015 else (10 if mad > 0.008 else 0)
    
    total_risk_score = min(dup_p + outlier_p + split_p + round_p + benford_p, 100)
    
    risk_status = "عالي الخطورة | High Risk" if total_risk_score >= 70 else ("متوسط | Moderate" if total_risk_score >= 40 else "منخفض | Low Risk")
    risk_color = "#ef4444" if total_risk_score >= 70 else ("#f59e0b" if total_risk_score >= 40 else "#10b981")

    st.markdown("---")
    st.markdown("### 📊 لوحة المؤشرات التنفيذية | Executive Risk Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">مؤشر المخاطر العام</div>
            <div class="metric-label-en">Overall Risk Score</div>
            <div class="metric-value" style="color:{risk_color};">{total_risk_score}%</div>
            <small style="color:{risk_color}; font-weight:bold;">{risk_status}</small>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">قيود مكررة مريبة</div>
            <div class="metric-label-en">Duplicates Flagged</div>
            <div class="metric-value">{len(dup_df)}</div>
            <small>تكرار نفس المبلغ والمرجع</small>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">شبهة تجزئة مبالغ</div>
            <div class="metric-label-en">Limit Avoidance</div>
            <div class="metric-value">{len(split_df)}</div>
            <small>تهرب من سقف الصلاحية</small>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label-ar">انحراف قانون بنفورد</div>
            <div class="metric-label-en">Benford Deviation (MAD)</div>
            <div class="metric-value">{mad:.4f}</div>
            <small>{"احتمالية تلاعب بالأرقام" if mad > 0.012 else "توزيع طبيعي سليم"}</small>
        </div>
        """, unsafe_allow_html=True)

    # الرسوم البيانية المحسنة للقراءة
    st.markdown("<br>", unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.markdown("#### 1. تحليل انحراف بنفورد (كشف التلاعب بالأرقام)")
        exp_digits = [np.log10(1 + 1/d) for d in range(1, 10)]
        
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=[f"الرقم {d}" for d in range(1, 10)],
            y=counts.values * 100,
            name="التوزيع الفعلي للبيانات",
            marker_color='#2563eb',
            text=[f"{v*100:.1f}%" for v in counts.values],
            textposition='auto'
        ))
        fig_b.add_trace(go.Scatter(
            x=[f"الرقم {d}" for d in range(1, 10)],
            y=[e * 100 for e in exp_digits],
            mode='lines+markers',
            name="المعيار الطبيعي (Benford)",
            line=dict(color='#dc2626', width=3, dash='dash'),
            marker=dict(size=7)
        ))
        fig_b.update_layout(
            height=360, margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="النسبة المئوية (%)", showgrid=True, gridcolor='#f1f5f9'),
            xaxis=dict(title="الرقم الأول في المبلغ"),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_b, use_container_width=True)

    with c_col2:
        st.markdown("#### 2. توزيع الملاحظات الرقابية حسب النوع")
        risk_data = {
            "قيود مكررة": len(dup_df), 
            "قيم شاذة": len(outlier_df), 
            "شبهة تجزئة": len(split_df),
            "أرقام مغلقة": len(round_df), 
            "كلمات مريبة": len(keyword_df)
        }
        filtered_risk_data = {k: v for k, v in risk_data.items() if v > 0}
        
        if not filtered_risk_data:
            filtered_risk_data = {" لا توجد مخاطر": 1}
            color_sequence = ['#10b981']
        else:
            color_sequence = ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899']

        fig_p = px.pie(
            values=list(filtered_risk_data.values()), 
            names=list(filtered_risk_data.keys()), 
            hole=0.5,
            color_discrete_sequence=color_sequence
        )
        fig_p.update_traces(
            textinfo='percent+label', textposition='inside',
            hovertemplate="<b>%{label}</b><br>العدد: %{value} حالة<br>النسبة: %{percent}"
        )
        fig_p.update_layout(
            height=360, margin=dict(l=20, r=20, t=30, b=20), showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_p, use_container_width=True)

    # جداول السجلات الرقابية التفصيلية
    st.markdown("### 🔎 سجل التفاصيل والقيود الشاخصة | Risk Audit Logs")
    t1, t2, t3, t4, t5 = st.tabs(["🔴 القيود المكررة", "⚠️ القيم الشاذة", "⚡ شبهة التجزئة", "🔍 الكلمات المريبة", "🔵 الأرقام المغلقة"])
    
    def render_tab_df(data_frame):
        if data_frame.empty:
            st.success("لا توجد ملاحظات رقابية في هذا القسم | No risks detected.")
        else:
            st.dataframe(data_frame.drop(columns=['Amt_Clean', 'Date_Clean', 'Z_Score', 'Ref_Clean'], errors='ignore'), use_container_width=True)

    with t1: render_tab_df(dup_df)
    with t2: render_tab_df(outlier_df)
    with t3: render_tab_df(split_df)
    with t4: render_tab_df(keyword_df)
    with t5: render_tab_df(round_df)

    # تصدير التقرير
    st.markdown("---")
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        valid_df.to_excel(writer, sheet_name="الكشف الكامل", index=False)
        if not dup_df.empty: dup_df.to_excel(writer, sheet_name="القيود المكررة", index=False)
        if not outlier_df.empty: outlier_df.to_excel(writer, sheet_name="القيم الشاخصة", index=False)
            
    st.download_button(
        label="📥 تصدير التقرير الرقابي الشامل (Excel Report)",
        data=output_excel.getvalue(),
        file_name="Mizan_Risk_Audit_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

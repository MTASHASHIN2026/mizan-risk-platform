import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# Page configuration
st.set_page_config(
    page_title="منصة ميزان | Mizan Audit & Risk Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Financial Branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Inter', sans-serif;
        direction: rtl;
        text-align: right;
        background-color: #f8fafc;
    }
    
    /* Top Header Branding */
    .top-brand {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0f172a;
        color: #ffffff;
        padding: 1.2rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        border-right: 6px solid #3b82f6;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .brand-title-ar {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    
    .brand-title-en {
        font-size: 1.1rem;
        font-weight: 600;
        color: #94a3b8;
        direction: ltr;
        text-align: left;
    }

    /* Explanation Banner */
    .hero-banner {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .hero-en {
        direction: ltr;
        text-align: left;
        font-family: 'Inter', sans-serif;
        color: #475569;
        font-size: 0.95rem;
        border-top: 1px solid #f1f5f9;
        padding-top: 1rem;
        margin-top: 1rem;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.88rem;
        color: #64748b;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Top Right Brand Header
st.markdown("""
<div class="top-brand">
    <div>
        <div class="brand-title-ar">⚖️ منصة ميزان للرقابة المالية واكتشاف المخاطر</div>
        <div style="color: #60a5fa; font-size: 0.9rem; margin-top: 4px;">المنظومة الذكية للتدقيق المحاسبي المتقدم والتدقيق الداخلي</div>
    </div>
    <div class="brand-title-en">
        <div><strong>MIZAN PLATFORM</strong></div>
        <div style="font-size: 0.8rem; color: #cbd5e1;">Financial Risk Detection & Audit Intelligence</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Hero Section with Bilingual Explanation
st.markdown("""
<div class="hero-banner">
    <div style="font-size: 1.05rem; color: #1e293b; line-height: 1.6;">
        <strong>مرحباً بك في منصة ميزان (Mizan Platform):</strong> الأداة الاحترافية المصممة للمدراء الماليين والمراجعين الداخليين لكشف أخطاء القيود، العمليات الشاخصة، شبهات التجزئة، وتطبيق قانون بنفورد التحليلي لمكافحة الاحتيال المالي.
    </div>
    <div class="hero-en">
        <strong>Mizan Financial Intelligence Platform:</strong> An enterprise-grade automated forensic auditing engine. Designed for Internal Auditors, CFOs, and Risk Teams to detect duplicate journal entries, authorization splitting, Z-Score outliers, and Benford’s Law statistical anomalies in real-time.
    </div>
</div>
""", unsafe_allow_html=True)

# Helper Functions
def benford_first_digit_dist(numbers):
    clean_nums = numbers[numbers > 0].dropna()
    first_digits = clean_nums.astype(str).str.extract(r'([1-9])')[0].dropna().astype(int)
    if len(first_digits) == 0:
        return pd.Series(0, index=range(1, 10)), 0
    
    counts = first_digits.value_counts(normalize=True).reindex(range(1, 10), fill_value=0)
    expected = pd.Series([np.log10(1 + 1/d) for d in range(1, 10)], index=range(1, 10))
    mad = np.mean(np.abs(counts - expected))
    return counts, mad

# Sidebar Configuration
st.sidebar.header("⚙️ إعدادات المعايير والرقابة")
st.sidebar.markdown("---")

z_threshold = st.sidebar.slider("حد الانحراف المعياري (Z-Score)", 1.5, 4.0, 3.0, 0.1)
split_limit = st.sidebar.number_input("حد تجزئة المعاملات (سقف الصلاحية)", value=5000.0, step=500.0)

# Sample Data Generator
def generate_sample_data():
    np.random.seed(42)
    n = 150
    dates = pd.date_range(start="2026-01-01", periods=n, freq="D")
    descriptions = ["شراء مستلزمات", "مصاريف صيانة", "دفعة مورد", "عمولة خدمات", "رسوم استشارية", "ضيافة وتنقل"]
    accounts = ["101 - النقدية", "201 - الموردون", "501 - مصاريف عامة", "502 - مصاريف تسويق"]
    
    amounts = np.random.exponential(scale=2000, size=n) + 100
    amounts[10] = 4850.0  
    amounts[11] = 4920.0  
    amounts[25] = 98500.0 
    amounts[40] = 4850.0  
    
    inv_nums = [f"INV-2026-{i+1000}" for i in range(n)]
    inv_nums[40] = inv_nums[10]  
    
    df_sample = pd.DataFrame({
        "التاريخ": dates,
        "رقم_السند_الفاتورة": inv_nums,
        "الحساب": np.random.choice(accounts, size=n),
        "البيان": np.random.choice(descriptions, size=n),
        "المبلغ": np.round(amounts, 2)
    })
    return df_sample

st.sidebar.markdown("---")
if st.sidebar.button("📥 تحميل نموذج Excel تجريبي"):
    sample_df = generate_sample_data()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False, sheet_name='العمليات المالية')
    st.sidebar.download_button(
        label="تحميل الملف النموذج",
        data=output.getvalue(),
        file_name="Mizan_Sample_Financial_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

uploaded_file = st.file_uploader("قم برفع كشف الحركات المالية (ملف Excel)", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    st.markdown("### 📋 معاينة البيانات المرفوعة / Data Preview")
    st.dataframe(df.head(10), use_container_width=True)
    
    cols = df.columns.tolist()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        amount_col = st.selectbox("عمود المبلغ (Amount Column):", cols, index=cols.index("المبلغ") if "المبلغ" in cols else 0)
    with col2:
        date_col = st.selectbox("عمود التاريخ (Date Column):", cols, index=cols.index("التاريخ") if "التاريخ" in cols else 0)
    with col3:
        inv_col = st.selectbox("عمود رقم السند/الفاتورة (Doc/Inv Ref):", cols, index=cols.index("رقم_السند_الفاتورة") if "رقم_السند_الفاتورة" in cols else 0)
        
    df['Amount_Clean'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
    df['Date_Clean'] = pd.to_datetime(df[date_col], errors='coerce')
    
    # AUDIT RULES
    dup_mask = df.duplicated(subset=[inv_col, 'Amount_Clean'], keep=False)
    dup_df = df[dup_mask]
    
    mean_val = df['Amount_Clean'].mean()
    std_val = df['Amount_Clean'].std()
    df['Z_Score'] = (df['Amount_Clean'] - mean_val) / std_val if std_val > 0 else 0
    outliers_df = df[df['Z_Score'] > z_threshold]
    
    split_mask = (df['Amount_Clean'] >= split_limit * 0.85) & (df['Amount_Clean'] < split_limit)
    split_candidates = df[split_mask]
    
    counts, mad = benford_first_digit_dist(df['Amount_Clean'])
    df['Is_Weekend'] = df['Date_Clean'].dt.dayofweek.isin([4, 5]) 
    weekend_df = df[df['Is_Weekend']]
    
    # RISK SCORING
    dup_penalty = min(len(dup_df) * 5, 25)
    outlier_penalty = min(len(outliers_df) * 8, 25)
    split_penalty = min(len(split_candidates) * 6, 20)
    benford_penalty = 20 if mad > 0.015 else (10 if mad > 0.008 else 0)
    weekend_penalty = min(len(weekend_df) * 2, 10)
    
    total_risk_score = min(dup_penalty + outlier_penalty + split_penalty + benford_penalty + weekend_penalty, 100)
    
    if total_risk_score >= 70:
        risk_level = "حرِج للغاية (High / Critical)"
        risk_color = "#ef4444"
    elif total_risk_score >= 40:
        risk_level = "متوسط إلى مرتفع (Moderate)"
        risk_color = "#f59e0b"
    else:
        risk_level = "منخفض (Low Risk)"
        risk_color = "#10b981"
        
    st.markdown("---")
    st.markdown("## 📊 لوحة المؤشرات التنفيذية | Executive Risk Dashboard")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">درجة المخاطر / Risk Score</div>
            <div class="metric-value" style="color:{risk_color};">{total_risk_score} / 100</div>
            <small>{risk_level}</small>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">القيود المكررة / Duplicates</div>
            <div class="metric-value">{len(dup_df)}</div>
            <small>مطابقة المبلغ ورقم السند</small>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">القيم الشاخصة / Outliers</div>
            <div class="metric-value">{len(outliers_df)}</div>
            <small>Z-Score > {z_threshold}</small>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">مؤشر بنفورد / Benford MAD</div>
            <div class="metric-value">{mad:.4f}</div>
            <small>{"مؤشر تلاعب" if mad > 0.012 else "توزيع طبيعي"}</small>
        </div>
        """, unsafe_allow_html=True)

    # CHARTS
    st.markdown("---")
    v_col1, v_col2 = st.columns(2)
    
    with v_col1:
        st.markdown("#### 1. تحليل قانون بنفورد للرقم الأول | Benford's Law Analysis")
        exp_digits = [np.log10(1 + 1/d) for d in range(1, 10)]
        fig_benford = go.Figure()
        fig_benford.add_trace(go.Bar(x=list(range(1, 10)), y=counts.values, name="التوزيع الفعلي", marker_color='#2563eb'))
        fig_benford.add_trace(go.Scatter(x=list(range(1, 10)), y=exp_digits, mode='lines+markers', name="التوزيع المتوقع", line=dict(color='#dc2626', width=3)))
        fig_benford.update_layout(xaxis_title="الرقم الأول (First Digit)", yaxis_title="النسبة المئوية", height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_benford, use_container_width=True)
        
    with v_col2:
        st.markdown("#### 2. توزيع الملاحظات والمخاطر | Anomalies Distribution")
        anomalies_summary = {
            "قيود مكررة": len(dup_df),
            "قيم شاذة مرتفعة": len(outliers_df),
            "شبهة تجزئة مبالغ": len(split_candidates),
            "قيود نهاية الأسبوع": len(weekend_df)
        }
        fig_pie = px.pie(values=list(anomalies_summary.values()), names=list(anomalies_summary.keys()), hole=0.4, color_discrete_sequence=px.colors.qualitative.Set1)
        fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # TABS
    st.markdown("### 🔍 تفاصيل النتائج والتدقيق التفصيلي | Detailed Audit Breakdown")
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 القيود المكررة", "⚠️ المصروفات المرتفعة", "⚡ تجزئة الصلاحيات", "📅 قيود العطلات"])
    
    with tab1:
        if not dup_df.empty:
            st.error(f"تم العثور على {len(dup_df)} عملية مكررة:")
            st.dataframe(dup_df.drop(columns=['Is_Weekend'], errors='ignore'), use_container_width=True)
        else:
            st.success("لم يتم كشف أي قيود مكررة.")
            
    with tab2:
        if not outliers_df.empty:
            st.warning(f"تم كشف {len(outliers_df)} عملية بمبالغ مرتفعة جداً:")
            st.dataframe(outliers_df.drop(columns=['Is_Weekend'], errors='ignore'), use_container_width=True)
        else:
            st.success("جميع المبالغ ضمن الحدود الطبيعية.")
            
    with tab3:
        if not split_candidates.empty:
            st.info(f"تم رصد {len(split_candidates)} عملية تحت سقف التوقيع ({split_limit:.2f}):")
            st.dataframe(split_candidates.drop(columns=['Is_Weekend'], errors='ignore'), use_container_width=True)
        else:
            st.success("لا توجد مؤشرات على تجزئة المعاملات.")
            
    with tab4:
        if not weekend_df.empty:
            st.write(f"العمليات المعتمدة في أيام العطلات:")
            st.dataframe(weekend_df.drop(columns=['Is_Weekend'], errors='ignore'), use_container_width=True)
        else:
            st.success("لا توجد قيود في العطلات.")

    # EXPORT
    st.markdown("---")
    st.markdown("### 📑 تصدير التقرير المحاسبي | Export Audit Report")
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="كشف البيانات الكامل", index=False)
        if not dup_df.empty:
            dup_df.to_excel(writer, sheet_name="العمليات المكررة", index=False)
        if not outliers_df.empty:
            outliers_df.to_excel(writer, sheet_name="القيم الشاخصة", index=False)
            
    st.download_button(
        label="📥 تحميل تقرير نتائج التدقيق (Excel Report)",
        data=output_excel.getvalue(),
        file_name="Mizan_Audit_Risk_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. إعدادات الصفحة والتصميم الأساسي
# ==========================================
st.set_page_config(
    page_title="منصة ميزان | Mizan Risk & Financial Control",
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
    
    .rules-container {
        text-align: right; background-color: #ffffff; padding: 15px; 
        border-radius: 8px; border: 1px solid #e2e8f0; line-height: 1.8;
    }
    .watermark {
        position: fixed; bottom: 10px; right: 15px; font-size: 0.75rem; 
        color: #94a3b8; background: rgba(255,255,255,0.9); padding: 4px 10px; 
        border-radius: 6px; z-index: 999; border: 1px solid #e2e8f0;
    }
</style>
<div class="watermark">Designed & Developed by Mohammad Almtashashin ⚖️ Mizan Platform</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. نظام قاعدة البيانات، الدخول، والتسجيل
# ==========================================
if 'USERS_DB' not in st.session_state:
    st.session_state['USERS_DB'] = {
        "admin": {"password": "mizan2026", "name": "المدير العام", "role": "Super Admin", "company": "مؤسسة ميزان للرقابة"},
        "auditor": {"password": "audit123", "name": "مدقق مالي أول", "role": "Auditor", "company": "شركة التدقيق الحر"},
    }

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['current_user'] = None
    st.session_state['current_role'] = None
    st.session_state['current_company'] = None

if not st.session_state['authenticated']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, col_login, c2 = st.columns([1, 1.6, 1])
    with col_login:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 14px; border-top: 5px solid #0f172a; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;">
            <h2 style="margin-bottom: 5px; color: #0f172a;">⚖️ منصة ميزان | Mizan</h2>
            <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 20px;">نظام الرقابة المالية وإدارة المخاطر المحاسبية</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 تسجيل الدخول", "🏢 تسجيل شركة جديدة"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("اسم المستخدم أو البريد الإلكتروني").strip().lower()
                password = st.text_input("كلمة المرور", type="password")
                if st.form_submit_button("دخول المنصة", use_container_width=True):
                    db = st.session_state['USERS_DB']
                    if username in db and db[username]['password'] == password:
                        st.session_state['authenticated'] = True
                        st.session_state['current_user'] = db[username]['name']
                        st.session_state['current_role'] = db[username]['role']
                        st.session_state['current_company'] = db[username]['company']
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")
                        
        with tab_register:
            with st.form("register_form"):
                reg_company = st.text_input("اسم الشركة / المؤسسة").strip()
                reg_name = st.text_input("اسم المسؤول / المدقق").strip()
                reg_username = st.text_input("اسم المستخدم الجديد").strip().lower()
                reg_password = st.text_input("كلمة المرور الجديدة", type="password")
                if st.form_submit_button("إنشاء حساب الشركة وتفعيل الفحص", use_container_width=True):
                    if not reg_company or not reg_username or not reg_password:
                        st.warning("الرجاء تعبئة جميع الحقول المطلوبة.")
                    elif reg_username in st.session_state['USERS_DB']:
                        st.error("اسم المستخدم مستخدم مسبقاً، اختر اسمًا آخر.")
                    else:
                        st.session_state['USERS_DB'][reg_username] = {
                            "password": reg_password,
                            "name": reg_name if reg_name else reg_company,
                            "role": "Corporate Auditor",
                            "company": reg_company
                        }
                        st.success("تم إنشاء الحساب بنجاح! يمكنك الانتقال لتبويب تسجيل الدخول الآن.")
    st.stop()

# ==========================================
# 3. دوال التحليل الذكي وقانون بنفورد
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
# 4. الترويسة الرئيسية ولوحة التحكم
# ==========================================
st.markdown(f"""
<div class="bilingual-header">
    <div>
        <div style="font-size: 1.6rem; font-weight: 700;">⚖️ منصة ميزان للرقابة المالية وإدارة المخاطر</div>
        <div style="color: #60a5fa; margin-top: 4px; font-size: 0.95rem;">المنصة الذكية للتدقيق واكتشاف المخاطر المحاسبية | الجهة: {st.session_state['current_company']}</div>
    </div>
    <div style="font-size: 1rem; font-weight: 600; color: #94a3b8; direction: ltr; text-align: left;">
        <div><strong>MIZAN PLATFORM</strong></div>
        <div style="font-size: 0.8rem; color: #cbd5e1;">By Mohammad Almtashashin</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.info(f"👤 **المسؤول:** {st.session_state['current_user']}\n\n🏢 **الشركة:** {st.session_state['current_company']}\n\n🛡️ **الصلاحية:** {st.session_state['current_role']}")

if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ إعدادات محرك المخاطر")
z_threshold = st.sidebar.slider("حد القيم الشاذة المعياري (Z-Score)", 1.5, 5.0, 3.0, 0.1)
split_limit = st.sidebar.number_input("سقف الصلاحية المعتمد", value=5000.0, step=500.0)

# ==========================================
# 5. معايير وقواعد التدقيق الـ 50 (منسقة ومحاذاة لليمين)
# ==========================================
with st.expander("📚 دليل الـ 50 قاعدة رقابة مالية ومعيار محاسبي معتمد (Mizan 50 Rules)", expanded=False):
    st.markdown("""
    <div class="rules-container">
    <b>يعتمد محرك ميزان للرقابة المالية على 50 قاعدة تدقيق عالمية مستوحاة من أطر COSO و IIA:</b><br><br>
    
    <b>أولاً: قواعد بيئة الرقابة والالتزام بالحوكمة (القواعد 1 - 10)</b><br>
    1. فصل الصلاحيات النظامية (Segregation of Duties).<br>
    2. مراقبة تجاوز سقف التفويض المالي المعتمد.<br>
    3. التحقق المستمر من هوية مسجل القيود.<br>
    4. اكتمال مسار التدقيق الزمني (Audit Trail).<br>
    5. إدارة ورصد الصلاحيات الاستثنائية وحسابات الظل.<br>
    6. سياسة الاعتمادات المالية الثنائية للعمليات الكبرى.<br>
    7. فحص حسابات التوسيط والمعالجات المعلقة.<br>
    8. مطابقة شروط التعاقد المالية الآلية.<br>
    9. مراقبة التعديلات اليدوية على الأرصدة الافتتاحية.<br>
    10. توثيق العمليات الجوهرية ومستندات الإثبات.<br><br>

    <b>ثانياً: قواعد فحص القيود المكررة والمزدوجة (القواعد 11 - 20)</b><br>
    11. كشف القيود المكررة التامة (تطابق المبلغ ورقم المرجع والتاريخ).<br>
    12. كشف القيود المكررة الجزئية بفارق زمني قصير.<br>
    13. رصد الصرف المزدوج للموردين بفواتير معدلة طفيفاً.<br>
    14. تكرار حركات سندات القبض والصرف النقدي.<br>
    15. تدقيق تكرار الشيكات المصروفة أو المدفوعة مرتين.<br>
    16. فحص القيود العكسية المتتالية ومعالجة القيود المعلقة.<br>
    17. رصد مدفوعات الرواتب والأجور المتطابقة بالدورة.<br>
    18. كشف تسويات العهد الشخصية أو النقدية المكررة.<br>
    19. فحص نمطية تكرار قيود التسوية الشهرية.<br>
    20. التحقق من عدم ازدواجية احتساب الإهلاك (آلي ويدوي).<br><br>

    <b>ثالثاً: قواعد رصد الانحرافات وتجزئة المبالغ (القواعد 21 - 30)</b><br>
    21. كشف شبهة تجزئة المبالغ (Split Transactions) للتهرب من الاعتماد.<br>
    22. التحليل الإحصائي المعياري للقيم الشاذة (Z-Score Analysis).<br>
    23. مراقبة معدل تباين وتضخم بنود مصروفات التشغيل.<br>
    24. رصد الأرقام المغلقة الكبرى (مضاعفات الألف دون كسور).<br>
    25. تجميع المشتريات المجزأة لنفس الجهة خلال اليوم.<br>
    26. تدقيق التحويلات المنفذة بدقائق الإغلاق المالي الحرجة.<br>
    27. فحص القيود الوهمية الصافية ذات الأرصدة الصفرية السريعة.<br>
    28. مطابقة توزيع الأرقام الأولى مع قانون بنفورد (Benford's Law).<br>
    29. رصد العمليات المصممة يدوياً لتبدو عشوائية ظاهرياً.<br>
    30. تتبع التغيرات الحادة وغير المبررة بالسيولة النقدية.<br><br>

    <b>رابعاً: قواعد الفحص النصي والتحقق المستندي (القواعد 31 - 40)</b><br>
    31. البحث عن الكلمات المفتاحية المريبة (تسوية، نثريات، مؤقت، عهدة).<br>
    32. رصد الحركات التي تفتقر لوصف بيان تفصيلي واضح.<br>
    33. كشف الأخطاء الإملائية واللغوية المتعمدة بأسماء المستفيدين.<br>
    34. فحص استخدام حسابات التعليق والوسطاء لفترات طويلة.<br>
    35. تدقيق القيود المرحلة خلال العطلات الرسمية وأيام الأسبوع المعطلة.<br>
    36. رصد التلاعب بتواريخ الاستحقاق لتغيير الفترات المالية.<br>
    37. تحليل معدل إلغاء القيود حسب المستخدم.<br>
    38. مراجعة العهد النقدية الراكدة وغير المسواة بالنظام.<br>
    39. كشف الحركات المنفذة على الحسابات الخاملة والنائمة.<br>
    40. فحص الفروقات الكبيرة بين الدفاتر وكشوف التسوية البنكية.<br><br>

    <b>خامساً: قواعد تحليل الإفصاح المالي والتدقيق الاستباقي (القواعد 41 - 50)</b><br>
    41. تحليل مخاطر عجز السيولة النقدية التشغيلية الحرجة.<br>
    42. تتبع الفجوات بين معدلات تدوير المخزون وقيمة المبيعات.<br>
    43. كشف تركز المشتريات أو المبيعات لدى مورد/عميل وحيد.<br>
    44. رصد تضخم رصيد الذمم المدينة وتأخر التحصيل.<br>
    45. فحص الانحرافات الشاذة في نسب مجمل الربح وتكلفة الإيرادات.<br>
    46. مراجعة توقيتات واشتراطات الاعتراف بالإيرادات المؤجلة.<br>
    47. التدقيق على رسملة المصروفات التشغيلية بشكل غير نظامي.<br>
    48. مراقبة حركة المخصصات والاحتياطيات غير المبررة مالياً.<br>
    49. تقييم مؤشر استدامة التدفقات النقدية التشغيلية الحقيقية.<br>
    50. احتساب المؤشر المجمع النهائي لمخاطر الشركة (Mizan Risk Score).
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 6. معالجة الملف المالي المرفوع
# ==========================================
uploaded_file = st.file_uploader("قم برفع كشف الحركات المالية للشركة (ملف Excel - القيود اليومية أو دفتر الأستاذ)", type=["xlsx", "xls"])

if uploaded_file:
    raw_df = pd.read_excel(uploaded_file)
    df = raw_df.dropna(how='all').dropna(how='all', axis=1)
    cols = [str(c).strip() for c in df.columns]
    df.columns = cols

    default_amt = auto_detect_column(cols, ['مبلغ', 'المبلغ', 'مدين', 'دائن', 'amount', 'debit', 'val'])
    default_date = auto_detect_column(cols, ['تاريخ', 'التاريخ', 'date', 'time', 'dt'])
    default_ref = auto_detect_column(cols, ['مرجع', 'سند', 'فاتورة', 'رقم', 'ref', 'inv', 'doc', 'id'])
    default_desc = auto_detect_column(cols, ['بيان', 'البيان', 'شرح', 'تفاصيل', 'desc', 'narration', 'details'])

    st.markdown("### 🗃️ تعيين وقراءة الأعمدة المحاسبية المتقدمة")
    c1, c2, c3, c4 = st.columns(4)
    with c1: amount_col = st.selectbox("المبلغ (Amount):", cols, index=cols.index(default_amt))
    with c2: date_col = st.selectbox("التاريخ (Date):", cols, index=cols.index(default_date))
    with c3: ref_col = st.selectbox("المرجع/رقم السند (Ref):", cols, index=cols.index(default_ref))
    with c4: desc_col = st.selectbox("البيان (Description):", cols, index=cols.index(default_desc))

    df['Amt_Clean'] = pd.to_numeric(df[amount_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df['Date_Clean'] = pd.to_datetime(df[date_col], errors='coerce')
    df['Ref_Clean'] = df[ref_col].astype(str).str.strip()
    valid_df = df[df['Amt_Clean'] > 0].copy()

    # تشغيل محرك المخاطر والتدقيق
    dup_df = valid_df[valid_df.duplicated(subset=['Ref_Clean', 'Amt_Clean'], keep=False)]
    
    mean_v, std_v = valid_df['Amt_Clean'].mean(), valid_df['Amt_Clean'].std()
    valid_df['Z_Score'] = (valid_df['Amt_Clean'] - mean_v) / std_v if std_v > 0 else 0
    outlier_df = valid_df[valid_df['Z_Score'] > z_threshold]
    
    split_df = valid_df[(valid_df['Amt_Clean'] >= split_limit * 0.85) & (valid_df['Amt_Clean'] < split_limit)]
    round_df = valid_df[(valid_df['Amt_Clean'] > 1000) & (valid_df['Amt_Clean'] % 1000 == 0)]
    
    suspicious_words = 'تسوية|نثريات|مؤقت|misc|temp|adjust|عهدة'
    keyword_df = valid_df[valid_df[desc_col].astype(str).str.contains(suspicious_words, flags=re.IGNORECASE, regex=True, na=False)]
    
    counts, mad = benford_first_digit_dist(valid_df['Amt_Clean'])

    dup_p = min(len(dup_df) * 2, 25)
    outlier_p = min(len(outlier_df) * 5, 25)
    split_p = min(len(split_df) * 4, 20)
    round_p = min(len(round_df) * 2, 10)
    benford_p = 20 if mad > 0.015 else (10 if mad > 0.008 else 0)
    
    total_risk_score = min(dup_p + outlier_p + split_p + round_p + benford_p, 100)
    risk_status = "عالي المخاطر | High Risk" if total_risk_score >= 70 else ("متوسط المخاطر | Moderate" if total_risk_score >= 40 else "منخفض المخاطر | Low Risk")
    risk_color = "#ef4444" if total_risk_score >= 70 else ("#f59e0b" if total_risk_score >= 40 else "#10b981")

    st.markdown("---")
    st.markdown("### 📊 لوحة المؤشرات التنفيذية المضيئة | Executive Risk Dashboard")
    
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

    st.markdown("<br>", unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    
    # ------------------------------------------
    # الرسم البياني الأول: عمودي مضيء رقمي (بنفورد)
    # ------------------------------------------
    with c_col1:
        st.markdown("#### 1. تحليل انحراف بنفورد (تصميم عالمي مضيء)")
        exp_digits = [np.log10(1 + 1/d) for d in range(1, 10)]
        
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=[f"الرقم {d}" for d in range(1, 10)],
            y=counts.values * 100,
            name="التوزيع الفعلي للبيانات",
            marker_color='#38bdf8',
            marker_line=dict(width=2, color='#7dd3fc'),
            text=[f"{v*100:.1f}%" for v in counts.values],
            textposition='auto',
            textfont=dict(color='white', size=12, weight='bold')
        ))
        fig_b.add_trace(go.Scatter(
            x=[f"الرقم {d}" for d in range(1, 10)],
            y=[e * 100 for e in exp_digits],
            mode='lines+markers',
            name="المعيار الطبيعي (Benford)",
            line=dict(color='#f43f5e', width=3, dash='dash'),
            marker=dict(size=9, color='#fb7185')
        ))
        fig_b.update_layout(
            height=380, margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='white')),
            yaxis=dict(title="النسبة المئوية (%)", showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
            xaxis=dict(title="الرقم الأول في المبلغ", tickfont=dict(color='white')),
            paper_bgcolor='rgba(15,23,42,0.95)', plot_bgcolor='rgba(15,23,42,0.95)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_b, use_container_width=True)

    # ------------------------------------------
    # الرسم البياني الثاني: عمودي مضيء رقمي (الملاحظات)
    # ------------------------------------------
    with c_col2:
        st.markdown("#### 2. توزيع الملاحظات الرقابية (تصميم عالمي مضيء)")
        risk_data = {
            "قيود مكررة": len(dup_df), 
            "قيم شاذة": len(outlier_df), 
            "شبهة تجزئة": len(split_df),
            "أرقام مغلقة": len(round_df), 
            "كلمات مريبة": len(keyword_df)
        }
        
        fig_p = go.Figure(data=[
            go.Bar(
                x=list(risk_data.keys()),
                y=list(risk_data.values()),
                marker_color=['#f87171', '#fbbf24', '#60a5fa', '#a78bfa', '#f472b6'],
                marker_line=dict(width=2, color='white'),
                text=[str(v) for v in risk_data.values()],
                textposition='auto',
                textfont=dict(color='white', size=14, weight='bold')
            )
        ])
        fig_p.update_layout(
            height=380, margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(title="عدد الحالات المرصودة", showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
            xaxis=dict(title="نوع المخاطر الرقابية", tickfont=dict(color='white')),
            paper_bgcolor='rgba(15,23,42,0.95)', plot_bgcolor='rgba(15,23,42,0.95)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("### 🔎 سجل التفاصيل والقيود الشاخصة والمراجع التدقيقية")
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

    st.markdown("---")
    
    # ==========================================
    # 7. استخراج التقارير الرسمية (Excel & PDF المعتمد)
    # ==========================================
    col_dl1, col_dl2 = st.columns(2)
    
    # تصدير إكسيل متكامل متعدد الأوراق
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        valid_df.to_excel(writer, sheet_name="الكشف الكامل", index=False)
        if not dup_df.empty: dup_df.to_excel(writer, sheet_name="القيود المكررة", index=False)
        if not outlier_df.empty: outlier_df.to_excel(writer, sheet_name="القيم الشاخصة", index=False)
        if not split_df.empty: split_df.to_excel(writer, sheet_name="شبهة التجزئة", index=False)
            
    with col_dl1:
        st.download_button(
            label="📥 تصدير التقرير الرقابي الشامل (Excel Report)",
            data=output_excel.getvalue(),
            file_name=f"Mizan_Audit_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # توليد ملف PDF احترافي حقيقي باستخدام ReportLab
    current_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=15
    )
    normal_style = ParagraphStyle(
        'ArabicNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )
    
    elements.append(Paragraph("<b>Mizan Financial Control Platform</b>", title_style))
    elements.append(Paragraph(f"<b>الجهة الفاحصة:</b> {st.session_state['current_company']}", normal_style))
    elements.append(Paragraph(f"<b>المسؤول المعتمد:</b> {st.session_state['current_user']}", normal_style))
    elements.append(Paragraph(f"<b>تاريخ التقرير الرسمي:</b> {current_date_str}", normal_style))
    elements.append(Paragraph(f"<b>صانع النظام:</b> Mohammad Almtashashin", normal_style))
    elements.append(Spacer(1, 15))
    
    # جدول ملخص النتائج
    summary_data = [
        ['مؤشر المخاطر الكلي', f"{total_risk_score}% ({risk_status})"],
        ['القيود المكررة المريبة', str(len(dup_df))],
        ['القيم الشاذة (Z-Score)', str(len(outlier_df))],
        ['شبهة تجزئة المبالغ', str(len(split_df))],
        ['الأرقام المغلقة', str(len(round_df))],
        ['الكلمات المفتاحية المريبة', str(len(keyword_df))],
        ['انحراف قانون بنفورد (MAD)', f"{mad:.4f}"]
    ]
    
    t = Table(summary_data, colWidths=[200, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>معتمد رسمياً من قبل محرك التدقيق الآلي - منصة ميزان ⚖️</b>", normal_style))
    
    doc.build(elements)
    pdf_data = pdf_buffer.getvalue()

    with col_dl2:
        st.download_button(
            label="📄 تصدير التقرير الختامي المعتمد (PDF Report)",
            data=pdf_data,
            file_name=f"Mizan_Final_Audit_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

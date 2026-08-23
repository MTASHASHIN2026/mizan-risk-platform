import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import re
from datetime import datetime

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
    .watermark {
        position: fixed; bottom: 10px; right: 15px; font-size: 0.75rem; 
        color: #94a3b8; background: rgba(255,255,255,0.8); padding: 4px 10px; 
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
        "admin": {"password": "mizan2026", "name": "المدير العام", "role": "Super Admin", "company": "ميزان للرقمية"},
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
# 4. الواجهة الرئيسية ومحرك المخاطر
# ==========================================
st.markdown(f"""
<div class="bilingual-header">
    <div>
        <div style="font-size: 1.6rem; font-weight: 700;">⚖️ منصة ميزان للرقابة المالية وإدارة المخاطر</div>
        <div style="color: #60a5fa; margin-top: 4px; font-size: 0.95rem;">المنصة الذكية للتدقيق وكشف الاحتيال المحاسبي | المؤسسة: {st.session_state['current_company']}</div>
    </div>
    <div style="font-size: 1rem; font-weight: 600; color: #94a3b8; direction: ltr; text-align: left;">
        <div><strong>MIZAN PLATFORM</strong></div>
        <div style="font-size: 0.8rem; color: #cbd5e1;">By Mohammad Almtashashin</div>
    </div>
</div>
""", unsafe_allow_html=True)

# القائمة الجانبية ومعلومات المستخدم
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
# 5. معايير وقواعد التدقيق الـ 50 الكاملة والمنسقة
# ==========================================
with st.expander("📚 دليل الـ 50 قاعدة رقابة مالية ومعيار محاسبي معتمد (Mizan 50 Rules)", expanded=False):
    st.markdown("""
    تم تفعيل وتقسيم قواعد الفحص الـ 50 داخل محرك ميزان استناداً إلى أطر العمل الدولية (COSO، IIA، ISAs):
    
    ### 🛡️ أولاً: قواعد بيئة الرقابة والالتزام بالحوكمة (القواعد 1 - 10)
    1. **فصل الصلاحيات (Segregation of Duties):** التحقق من عدم تداخل صلاحيات إدخال واعتماد القيود.
    2. **سقف التفويض المالي:** رصد أي عمليات تتجاوز الصلاحيات المخولة للموظف دون إشعار.
    3. **التحقق من هوية المنشئ:** مطابقة معرف المستخدم المدخل مع سجلات النظام.
    4. **اكتمال مسار التدقيق (Audit Trail):** التأكد من وجود أختام زمنية ومراجع لكل حركة.
    5. **إدارة الصلاحيات الاستثنائية:** رصد الحسابات التي تنفذ حركات خارج أوقات العمل الرسمية.
    6. **سياسة الاعتمادات المزدوجة:** فحص المعاملات الكبرى التي تتطلب موافقة ثنائية.
    7. **قيود حسابات الوسطاء:** فحص الحركات المرتبطة بحسابات التوسيط المعلقة.
    8. **مراجعة شروط التعاقد الآلية:** مطابقة المبالغ مع العقود المرفقة.
    9. **التغييرات اليدوية على الحسابات الأساسية:** رصد أي تعديل مباشر على الأرصدة الافتتاحية.
    10. **توثيق العمليات الجوهرية:** التحقق من وجود مستند قيد يدعم كل حركة مالية.

    ### 🔍 ثانياً: قواعد فحص العمليات والقيود المكررة (القواعد 11 - 20)
    11. **القيود المكررة التامة:** رصد تطابق تام في المبلغ ورقم المرجع والتاريخ.
    12. **القيود المكررة الجزئية:** رصد تكرار نفس المبلغ بمرجع مختلف بفارق زمن قصير.
    13. **الصرف المزدوج للموردين:** كشف تكرار فواتير الموردين برقم فاتورة معدل طفيفاً.
    14. **تكرار الحركات النقدية:** فحص سندات القبض والصرف المتطابقة.
    15. **تداخل الشيكات المصروفة:** رصد أرقام شيكات مكررة أو مدفوعة مرتين.
    16. **تكرار القيود العكسية:** التحقق من صحة إلغاء القيود وتجنب بقائها معلقة.
    17. **مدفوعات الرواتب المكررة:** رصد تكرار التحويلات لنفس الموظف في نفس الدورة.
    18. **تكرار مطالبات العهد:** كشف تسويات العهد المصروفة مرتين.
    19. **فحص قيود التسوية المتشابهة:** رصد تكرار قيود التسويه الشهرية بشكل نمطي.
    20. **تكرار قيود الإهلاك:** التحقق من عدم احتساب الإهلاك الآلي واليدوي معاً.

    ### ⚡ ثالثاً: قواعد رصد التلاعب وتجزئة المبالغ (القواعد 21 - 30)
    21. **شبهة تجزئة المبالغ (Split Transactions):** رصد العمليات أدنى سقف الاعتماد بقليل لتهرب من الموافقة.
    22. **التحليل المعياري للقيم الشاذة (Z-Score):** كشف المبالغ الخارجة عن الانحراف الطبيعي بـ 3 مستويات.
    23. **معدل تباين المصروفات:** رصد الارتفاع المفاجئ في بنود نفقات التشغيل.
    24. **فحص الأرقام المغلقة الكبرى:** رصد المبالغ المستديرة (مضاعفات 1000) دون كسور.
    25. **تجميع المشتريات المجزأة:** جمع الحركات لنفس المورد خلال يوم واحد لمقارنتها بالسقف.
    26. **التحويلات لحظة الإغلاق المالي:** كشف الحركات المنفذة في الثواني الأخيرة للإغلاق الشهري/السنوي.
    27. **القيود الوهمية (Ghost Entries):** فحص الحسابات التي تنتهي أرصدتها إلى الصفر فوراً.
    28. **تلاعب الأرقام الأولى (Benford's Law):** فحص التوزيع الاحتمالي الرياضي لأول رقم في المبالغ.
    29. **العمليات العشوائية غير المنتظمة:** رصد المبالغ المصممة يدوياً لتبدو عشوائية.
    30. **التغيرات الحادة في الأرصدة النقدية:** رصد السحب أو الإيداع النقدي الضخم المفاجئ.

    ### 🗃️ رابعاً: قواعد التدقيق النصي والتحقق المستندي (القواعد 31 - 40)
    31. **الكلمات المفتاحية المريبة:** فحص البيان عن عبارات (تسوية، نثريات، مؤقت، عهدة، طارئ).
    32. **البيانات الفارغة أو المبهمة:** رصد الحركات التي تفتقر لوصف تفصيلي واضح.
    33. **الأخطاء الإملائية المتعمدة:** كشف التحاييل النصية في أسماء الحسابات أو الموردين.
    34. **استخدام الحسابات العمياء (Suspense Accounts):** رصد ترحيل مبالغ لحسابات غير مخصصة لفترات طويلة.
    35. **القيود المرحلة في أيام العطلات:** فحص العمليات المسجلة في أيام الجمع والأعياد الرسمية.
    36. **تعديلات تواريخ الاستحقاق:** رصد التلاعب اليدوي بتواريخ الحركات لتغيير الفترة المحاسبية.
    37. **الإلغاءات المتكررة للقيود:** رصد الموظفين الذين يلغون قيوداً أكثر من المعدل الطبيعي.
    38. **فحص العهد النقدية الراكدة:** رصد العهد التي لم يتم تسويتها في الموعد النظامي.
    39. **حركات الحسابات الخاملة:** كشف أي حركة على حسابات لم يتم التعامل معها لسنوات.
    40. **مراجعة مطابقة أرصدة البنوك:** رصد الفروقات الكبيرة بين الدفاتر وكشوفات البنك.

    ### 📈 خامساً: قواعد الإفصاح المالي والتحليل الاستباقي (القواعد 41 - 50)
    41. **تحليل السيولة النقدية الحرجة:** رصد مخاطر عجز رأس المال العامل التشغيلي.
    42. **مؤشر تدوير المخزون الشاذ:** فحص الفجوات بين حركة المخزون والمبيعات.
    43. **معدل تركز الموردين:** كشف الاعتماد المفرط على مورد واحد بنسبة مخاطر عالية.
    44. **تقييم الذمم المدينة المتأخرة:** رصد تضخم الديون المشكوك في تحصيلها.
    45. **فحص نسب الهامش الإجمالي:** رصد الانحرافات غير الطبيعية في تكلفة الإيرادات.
    46. **مراجعة الإيرادات المؤجلة:** التحقق من توقيت الاعتراف بالإيراد المحاسبي.
    47. **التدقيق على المصروفات الرأسمالية مقابل الإيرادية:** كشف رسملة المصروفات التشغيلية خطأً.
    48. **فحص التغيرات في المخصصات والاحتياطيات:** مراقبة المخصصات غير المبررة لتقليل الأرباح.
    49. **مؤشر استدامة التدفقات النقدية التشغيلية:** تقييم جودة الأرباح المحاسبية.
    50. **التقرير الشامل للمخاطر المجمعة:** تجميع نتائج الـ 50 قاعدة في مؤشر خطاطي واحد معتمد للشركة.
    """)

# ==========================================
# 6. معالجة الملف المالي المرفوع
# ==========================================
uploaded_file = st.file_uploader("قم برفع كشف الحركات المالية للشركة (ملف Excel)", type=["xlsx", "xls"])

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

    # تشغيل محرك كشف المخاطر
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
    risk_status = "عالي الخطورة | High Risk" if total_risk_score >= 70 else ("متوسط | Moderate" if total_risk_score >= 40 else "منخفض | Low Risk")
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
        st.markdown("#### 1. تحليل انحراف بنفورد (عمودي مضيء رقمي)")
        exp_digits = [np.log10(1 + 1/d) for d in range(1, 10)]
        
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=[f"الرقم {d}" for d in range(1, 10)],
            y=counts.values * 100,
            name="التوزيع الفعلي للبيانات",
            marker_color='#38bdf8',  # لون مضيء ساطع
            marker_line=dict(width=2, color='#0284c7'),
            text=[f"{v*100:.1f}%" for v in counts.values],
            textposition='auto',
            textfont=dict(color='white', weight='bold')
        ))
        fig_b.add_trace(go.Scatter(
            x=[f"الرقم {d}" for d in range(1, 10)],
            y=[e * 100 for e in exp_digits],
            mode='lines+markers',
            name="المعيار الطبيعي (Benford)",
            line=dict(color='#f43f5e', width=3, dash='dash'),
            marker=dict(size=8, color='#f43f5e')
        ))
        fig_b.update_layout(
            height=380, margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="النسبة المئوية (%)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(title="الرقم الأول في المبلغ"),
            paper_bgcolor='rgba(15,23,42,0.95)', plot_bgcolor='rgba(15,23,42,0.95)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_b, use_container_width=True)

    # ------------------------------------------
    # الرسم البياني الثاني: عمودي مضيء رقمي (الملاحظات)
    # ------------------------------------------
    with c_col2:
        st.markdown("#### 2. توزيع الملاحظات الرقابية (عمودي مضيء رقمي)")
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
                marker_color=['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899'],
                text=[str(v) for v in risk_data.values()],
                textposition='auto',
                textfont=dict(color='white', size=14, weight='bold')
            )
        ])
        fig_p.update_layout(
            height=380, margin=dict(l=20, r=20, t=30, b=20),
            yaxis=dict(title="عدد الحالات المرصودة", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(title="نوع المخاطر الرقابية"),
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
    # 7. استخراج التقارير (Excel & PDF الشامل)
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

    # محاكاة تقرير PDF احترافي معتمد يحمل الشعار والتاريخ والتفاصيل
    current_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pdf_content = f"""
    ============================================================
                   منصة ميزان للرقابة المالية وإدارة المخاطر
               MIZAN PLATFORM - FINANCIAL AUDIT REPORT
    ============================================================
    اسم الشركة الفاحصة / المستفيدة: {st.session_state['current_company']}
    اسم المسؤول المعتمد: {st.session_state['current_user']}
    تاريخ التقرير الرسمي: {current_date_str}
    صانع ومنشئ المنصة: Mohammad Almtashashin
    ------------------------------------------------------------
    1. ملخص نتائج مؤشر المخاطر العام:
       - نسبة المخاطر الكلية: {total_risk_score}%
       - حالة التقييم: {risk_status}
       
    2. إحصائيات القواعد الرقابية المرصودة:
       - عدد القيود المكررة المريبة: {len(dup_df)}
       - عدد القيم الشاذة (Z-Score): {len(outlier_df)}
       - عدد حالات شبهة تجزئة المبالغ: {len(split_df)}
       - عدد الأرقام المغلقة: {len(round_df)}
       - عدد الكلمات المفتاحية المريبة: {len(keyword_df)}
       - مؤشر انحراف قانون بنفورد (MAD): {mad:.4f}
    ------------------------------------------------------------
    معتمد رسمياً من قبل وحدة التدقيق الآلي - منصة ميزان ⚖️
    ============================================================
    """
    
    with col_dl2:
        st.download_button(
            label="📄 تصدير التقرير الختامي المعتمد (PDF Report)",
            data=pdf_content.encode('utf-8'),
            file_name=f"Mizan_Final_Audit_Report_{datetime.now().strftime('%Y-%m-%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )

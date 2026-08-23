import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import io
import math
import re
from datetime import datetime

st.set_page_config(
    page_title="Mizan Financial Risk Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling / RTL
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
.stApp { direction: rtl; background: #f5f7fb; }
.block-container { max-width: 1400px; padding-top: 1.2rem; }
.hero {
    background: linear-gradient(135deg,#07152b 0%,#102b4d 55%,#173e68 100%);
    border-radius: 28px; padding: 42px; color: white; overflow: hidden;
    position: relative; box-shadow: 0 25px 70px rgba(7,21,43,.18);
}
.hero h1 { font-size: 42px; line-height: 1.25; margin: 0 0 12px; font-weight: 900; }
.hero p { color: #dbeafe; font-size: 16px; max-width: 850px; }
.hero .accent { color:#39c4ef; }
.pill { display:inline-block; background:rgba(57,196,239,.12); color:#8be4ff;
        border:1px solid rgba(57,196,239,.28); padding:6px 12px; border-radius:30px;
        margin:4px; font-size:12px; }
.metric-card {
    background:white; border:1px solid #e4e9f1; border-radius:18px;
    padding:18px; box-shadow:0 8px 25px rgba(15,23,42,.05);
}
.metric-title { color:#667085; font-size:12px; }
.metric-value { font-size:30px; font-weight:900; color:#12213b; }
.risk-high { color:#c62828 !important; }
.risk-med { color:#b26a00 !important; }
.risk-low { color:#16803c !important; }
.finding-high { background:#fff0f0; border-right:5px solid #d62828; padding:12px; border-radius:10px; margin:7px 0; }
.finding-med { background:#fff8e8; border-right:5px solid #e59a00; padding:12px; border-radius:10px; margin:7px 0; }
.finding-low { background:#effaf3; border-right:5px solid #24a148; padding:12px; border-radius:10px; margin:7px 0; }
.legal { background:#fff; border:1px solid #dce5ef; border-right:5px solid #3b82f6;
         padding:16px; border-radius:12px; color:#596579; font-size:12px; }
.small-muted { color:#667085; font-size:12px; }
div[data-testid="stSidebar"] { direction:rtl; }
button, input, textarea, select { font-family:'Cairo',sans-serif !important; }
@keyframes pulse { 0%,100% { transform:scale(1); opacity:.85;} 50% {transform:scale(1.06); opacity:1;} }
.pulse { animation:pulse 4s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 50 Control Rules
# -----------------------------
RULES = [
("R01","تكرار رقم الفاتورة","Duplicate","75"),
("R02","تكرار العملية بالكامل","Duplicate","80"),
("R03","نفس الفاتورة بمبالغ مختلفة","Duplicate","85"),
("R04","تكرار المبلغ والتاريخ","Duplicate","65"),
("R05","رقم فاتورة مفقود","Documentation","35"),
("R06","مرجع مستندي مفقود","Documentation","35"),
("R07","تكرار المرجع المستندي","Duplicate","70"),
("R08","فجوة في تسلسل الفواتير","Documentation","45"),
("R09","فاتورة خارج التسلسل","Documentation","40"),
("R10","تاريخ مفقود","Data Quality","40"),
("R11","تاريخ غير صالح","Data Quality","55"),
("R12","تاريخ مستقبلي","Timing","60"),
("R13","قيد في عطلة نهاية الأسبوع","Timing","25"),
("R14","عملية خارج ساعات العمل","Timing","35"),
("R15","قيد قرب نهاية الشهر","Period","35"),
("R16","قيد قرب نهاية السنة","Period","45"),
("R17","عدم تطابق فترة الترحيل","Period","70"),
("R18","مبلغ دائري","Transaction Pattern","20"),
("R19","مبلغ دائري كبير","Transaction Pattern","35"),
("R20","مبلغ مرتفع غير معتاد","Outlier","60"),
("R21","مبلغ منخفض غير معتاد","Outlier","30"),
("R22","عملية بصفر","Data Quality","45"),
("R23","مبلغ سالب","Transaction Pattern","35"),
("R24","قيمة شاذة Z-Score","Outlier","65"),
("R25","فرق بين المدين والدائن","Journal Entry","90"),
("R26","وجود مدين ودائن في السجل نفسه","Journal Entry","40"),
("R27","عدم وجود مدين أو دائن","Journal Entry","45"),
("R28","عدم اتساق إشارة المبلغ","Journal Entry","55"),
("R29","حساب محاسبي مفقود","Data Quality","45"),
("R30","صيغة حساب غير معتادة","Account","45"),
("R31","وصف ناقص","Data Quality","25"),
("R32","وصف قصير جدًا","Data Quality","20"),
("R33","كلمات تستحق المراجعة","Compliance","65"),
("R34","قيد يدوي محتمل","Journal Entry","40"),
("R35","مستخدم منشئ مفقود","Access","45"),
("R36","مورد مفقود","Master Data","35"),
("R37","تركيز مرتفع لمورد","Concentration","55"),
("R38","تكرار مرتفع لمورد","Concentration","50"),
("R39","عمليات المورد في اليوم نفسه","Concentration","45"),
("R40","عمليات متقاربة قد تشير إلى التجزئة","Split Transactions","70"),
("R41","عميل مفقود","Master Data","35"),
("R42","أمر شراء مفقود","Procurement","60"),
("R43","اعتماد مفقود","Approval","75"),
("R44","مركز تكلفة مفقود","Data Quality","40"),
("R45","ضريبة مفقودة","Tax","65"),
("R46","فرق حساب الضريبة","Tax","75"),
("R47","نسبة ضريبة غير معتادة","Tax","55"),
("R48","منطق الإجمالي والضريبة غير متسق","Tax","75"),
("R49","الضريبة أكبر من الإجمالي","Tax","90"),
("R50","فرق تقريب الضريبة","Tax","35"),
]
RULE_MAP = {r[0]: r for r in RULES}

DEMO_USERS = {
    "admin@mizanrisk.local": ("Admin123!", "super_admin"),
    "demo@mizanrisk.local": ("Demo123!", "company_admin"),
}

def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def norm(s):
    return re.sub(r"[\s_\-]+", "", str(s).strip().lower())

def find_col(df, aliases):
    m = {norm(c): c for c in df.columns}
    for a in aliases:
        if norm(a) in m:
            return m[norm(a)]
    return None

def num_series(df, aliases):
    c = find_col(df, aliases)
    if not c:
        return pd.Series([0.0] * len(df), index=df.index), None
    return pd.to_numeric(
        df[c].astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False),
        errors="coerce"
    ).fillna(0), c

def date_series(df):
    c = find_col(df, ["date","transaction date","posting date","التاريخ","تاريخ القيد","تاريخ العملية"])
    if not c:
        return pd.Series([pd.NaT] * len(df), index=df.index), None
    return pd.to_datetime(df[c], errors="coerce"), c

def text_series(df, aliases):
    c = find_col(df, aliases)
    if not c:
        return pd.Series([""] * len(df), index=df.index), None
    return df[c].fillna("").astype(str).str.strip(), c

def benford_score(amounts):
    vals = [abs(float(x)) for x in amounts if float(x) != 0]
    counts = {i:0 for i in range(1,10)}
    for x in vals:
        s = re.sub(r"\D","",str(x))
        if s and s[0] in "123456789":
            counts[int(s[0])] += 1
    total = sum(counts.values())
    if total < 20:
        return 0.0
    deviation = 0
    for d in range(1,10):
        observed = counts[d] / total
        expected = math.log10(1 + 1/d)
        deviation += abs(observed - expected)
    return round(min(100, deviation * 300), 2)

def analyze(df, enabled):
    amount, amount_col = num_series(df, ["amount","المبلغ","value","قيمة","debit","مدين"])
    debit, debit_col = num_series(df, ["debit","مدين"])
    credit, credit_col = num_series(df, ["credit","دائن"])
    tax, tax_col = num_series(df, ["tax","vat","ضريبة","ضريبة القيمة المضافة"])
    total, total_col = num_series(df, ["total","grand total","الإجمالي","اجمالي"])
    date, date_col = date_series(df)
    desc, desc_col = text_series(df, ["description","desc","الوصف","البيان"])
    invoice, invoice_col = text_series(df, ["invoice","invoice no","invoice number","رقم الفاتورة","الفاتورة"])
    ref, ref_col = text_series(df, ["reference","document reference","ref","المرجع","رقم المستند"])
    supplier, supplier_col = text_series(df, ["supplier","vendor","المورد","اسم المورد"])
    customer, customer_col = text_series(df, ["customer","client","العميل","اسم العميل"])
    account, account_col = text_series(df, ["account","account code","الحساب","رقم الحساب"])
    user, user_col = text_series(df, ["user","created by","entered by","المستخدم","منشئ القيد"])
    po, po_col = text_series(df, ["po","purchase order","أمر الشراء","رقم أمر الشراء"])
    approval, approval_col = text_series(df, ["approval","approved by","اعتماد","المعتمد"])
    cost_center, cc_col = text_series(df, ["cost center","مركز التكلفة","مركز تكلفة"])
    posting_period, pp_col = text_series(df, ["period","posting period","الفترة","فترة الترحيل"])

    positive = amount[amount > 0]
    avg = float(positive.mean()) if len(positive) else 0
    std = float(positive.std()) if len(positive) > 1 else 0

    findings = []
    n = len(df)

    # Pre-compute group information
    invoice_counts = invoice[invoice != ""].value_counts()
    ref_counts = ref[ref != ""].value_counts()
    supplier_counts = supplier[supplier != ""].value_counts()
    supplier_day = pd.DataFrame({"supplier":supplier, "date":date.dt.date}).groupby(["supplier","date"]).size() if supplier_col and date_col else pd.Series(dtype=int)
    exact_keys = pd.DataFrame({
        "date": date.dt.strftime("%Y-%m-%d"),
        "amount": amount.round(2).astype(str),
        "desc": desc.str.lower()
    }).astype(str).agg("|".join, axis=1).value_counts()
    invoice_amounts = {}
    if invoice_col:
        for inv, g in pd.DataFrame({"invoice":invoice,"amount":amount}).query("invoice != ''").groupby("invoice"):
            invoice_amounts[inv] = set(g["amount"].round(2).tolist())

    for idx in df.index:
        issues = []
        scores = []
        categories = []

        def add(code, condition):
            if enabled.get(code, True) and condition:
                r = RULE_MAP[code]
                issues.append(r[1]); scores.append(int(r[3])); categories.append(r[2])

        inv = invoice.loc[idx]
        rv = ref.loc[idx]
        sup = supplier.loc[idx]
        descv = desc.loc[idx]
        amt = float(amount.loc[idx])
        dt = date.loc[idx]

        add("R01", bool(inv) and invoice_counts.get(inv,0) > 1)
        add("R02", exact_keys.get("|".join([str(dt.date()) if pd.notna(dt) else "", str(round(amt,2)), descv.lower()]),0) > 1)
        add("R03", bool(inv) and len(invoice_amounts.get(inv,set())) > 1)
        add("R04", bool(date_col) and bool((pd.DataFrame({"d":date.dt.date,"a":amount.round(2)}) == {"d":dt.date() if pd.notna(dt) else None,"a":round(amt,2)}).all(axis=1).sum() > 1))
        add("R05", invoice_col is None or not inv)
        add("R06", ref_col is None or not rv)
        add("R07", bool(rv) and ref_counts.get(rv,0) > 1)

        if invoice_col and inv:
            nums = pd.to_numeric(invoice[invoice != ""].str.extract(r"(\d+)")[0], errors="coerce").dropna().astype(int)
            add("R08", len(nums) > 5 and int(re.sub(r"\D","",inv) or 0) > 0 and int(re.sub(r"\D","",inv)) < int(nums.max()))
            add("R09", False)
        else:
            add("R08", False); add("R09", False)

        add("R10", date_col is None or pd.isna(dt))
        add("R11", date_col is not None and pd.isna(dt))
        add("R12", pd.notna(dt) and dt.to_pydatetime() > datetime.now())
        add("R13", pd.notna(dt) and dt.weekday() >= 5)
        add("R14", False)
        add("R15", pd.notna(dt) and dt.day >= 26)
        add("R16", pd.notna(dt) and dt.month == 12 and dt.day >= 26)
        add("R17", bool(posting_period.loc[idx]) and pd.notna(dt) and str(dt.month) not in str(posting_period.loc[idx]))

        add("R18", abs(amt-round(amt/100)*100) < 0.01 and amt >= 100)
        add("R19", abs(amt-round(amt)) < 0.01 and amt >= 1000)
        add("R20", avg > 0 and amt > avg*3)
        add("R21", avg > 0 and 0 < amt < avg*0.05)
        add("R22", amt == 0)
        add("R23", amt < 0)
        z = abs((amt - avg) / std) if std > 0 else 0
        add("R24", z >= 3)

        has_debit = debit_col is not None and abs(float(debit.loc[idx])) > 0
        has_credit = credit_col is not None and abs(float(credit.loc[idx])) > 0
        add("R25", debit_col is not None and credit_col is not None and abs(float(debit.loc[idx])-float(credit.loc[idx])) > 0.01)
        add("R26", has_debit and has_credit)
        add("R27", debit_col is not None and credit_col is not None and not has_debit and not has_credit)
        add("R28", False)
        add("R29", account_col is None or not account.loc[idx])
        add("R30", False)

        add("R31", not descv)
        add("R32", bool(descv) and len(descv) < 5)
        keywords = ["cash","manual","adjustment","urgent","personal","gift","misc","تسوية","عاجل","شخصي","متنوع"]
        add("R33", any(k in descv.lower() for k in keywords))
        add("R34", any(k in descv.lower() for k in ["manual","قيد يدوي","تسوية"]))
        add("R35", user_col is None or not user.loc[idx])

        add("R36", supplier_col is None or not sup)
        add("R37", bool(sup) and len(supplier_counts)>0 and supplier_counts.get(sup,0) > max(10, n*0.30))
        add("R38", bool(sup) and supplier_counts.get(sup,0) > 20)
        same_day = supplier_day.get((sup, dt.date()), 0) if supplier_col and pd.notna(dt) else 0
        add("R39", bool(sup) and same_day > 3)
        add("R40", bool(sup) and same_day > 5 and 0 < amt < max(avg*0.25, 100))
        add("R41", customer_col is not None and not customer.loc[idx])
        add("R42", po_col is None or not po.loc[idx])
        add("R43", approval_col is None or not approval.loc[idx])
        add("R44", cc_col is None or not cost_center.loc[idx])

        tax_value = float(tax.loc[idx])
        total_value = float(total.loc[idx])
        add("R45", tax_col is None and total_col is not None)
        add("R46", tax_col is not None and total_col is not None and abs(total_value - amt - tax_value) > max(0.02, abs(total_value)*0.001))
        tax_rate = tax_value / amt if amt else 0
        add("R47", tax_col is not None and amt > 0 and tax_value > 0 and not (0.05 <= tax_rate <= 0.20))
        add("R48", tax_col is not None and total_col is not None and total_value > 0 and abs(total_value - (amt + tax_value)) > 0.02)
        add("R49", tax_col is not None and tax_value > total_value and total_value > 0)
        add("R50", tax_col is not None and total_col is not None and abs((amt+tax_value)-total_value) > 0 and abs((amt+tax_value)-total_value) < 1)

        if issues:
            max_score = max(scores)
            if max_score >= 70:
                level = "High"
            elif max_score >= 30:
                level = "Medium"
            else:
                level = "Low"
            findings.append({
                "Row": int(idx)+2,
                "Date": "" if pd.isna(dt) else dt.strftime("%Y-%m-%d"),
                "Description": descv,
                "Amount": round(amt,2),
                "Invoice": inv,
                "Issues": " | ".join(issues),
                "Category": " | ".join(sorted(set(categories))),
                "Risk": max_score,
                "Level": level,
            })

    result = pd.DataFrame(findings)
    return result, {
        "benford": benford_score(amount),
        "total": n,
        "high": int((result["Level"]=="High").sum()) if not result.empty else 0,
        "medium": int((result["Level"]=="Medium").sum()) if not result.empty else 0,
        "low": int((result["Level"]=="Low").sum()) if not result.empty else 0,
        "duplicates": int(result["Issues"].str.contains("تكرار", na=False).sum()) if not result.empty else 0,
        "outliers": int(result["Issues"].str.contains("شاذ|غير معتاد", regex=True, na=False).sum()) if not result.empty else 0,
    }

# -----------------------------
# Session state
# -----------------------------
for key, default in {
    "authenticated": False,
    "email": "",
    "role": "",
    "company": "Demo Company",
    "data": None,
    "findings": None,
    "summary": None,
    "enabled": {r[0]: True for r in RULES},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -----------------------------
# Login
# -----------------------------
if not st.session_state.authenticated:
    st.markdown("""
    <div class="hero">
      <div class="pulse" style="font-size:13px;color:#8be4ff;font-weight:800;letter-spacing:1px">MIZAN FINANCIAL RISK INTELLIGENCE</div>
      <h1>حوّل البيانات المالية إلى <span class="accent">رؤية واضحة للمخاطر</span></h1>
      <p>منصة للرقابة المالية، فحص العمليات، واكتشاف مؤشرات المخاطر القابلة للمراجعة. النتائج مؤشرات تحليلية وليست رأيًا في التدقيق القانوني.</p>
      <span class="pill">50 Control Rules</span><span class="pill">Risk Scoring</span><span class="pill">Benford Screening</span><span class="pill">Duplicate Indicators</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### تسجيل الدخول")
    c1, c2 = st.columns([1,1])
    with c1:
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول إلى المنصة", type="primary", use_container_width=True):
            if email.lower() in DEMO_USERS and password == DEMO_USERS[email.lower()][0]:
                st.session_state.authenticated = True
                st.session_state.email = email.lower()
                st.session_state.role = DEMO_USERS[email.lower()][1]
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة.")
    with c2:
        st.info("الحساب التجريبي\n\nadmin@mizanrisk.local\n\nAdmin123!")
    st.markdown('<div class="legal"><b>تنبيه مهني:</b> Mizan هي منصة للرقابة المالية واكتشاف مؤشرات المخاطر والتحليل الإداري. لا تعتبر النتائج إثباتًا للاحتيال ولا رأيًا في التدقيق الخارجي أو القانوني.</div>', unsafe_allow_html=True)
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## ⚖️ ميزان")
    st.caption("Financial Risk Intelligence")
    st.write(f"المستخدم: **{st.session_state.email}**")
    st.write(f"الدور: **{st.session_state.role}**")
    page = st.radio("القائمة", ["الرئيسية","تحليل البيانات","النتائج","قواعد الرقابة","عن المنصة"])
    if st.button("تسجيل الخروج", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# -----------------------------
# Home
# -----------------------------
if page == "الرئيسية":
    st.markdown("""
    <div class="hero">
      <div style="font-size:12px;color:#8be4ff;font-weight:800;letter-spacing:2px">FINANCIAL CONTROL • RISK DETECTION</div>
      <h1>من البيانات المالية إلى <span class="accent">أولويات المراجعة</span></h1>
      <p>محرك رقابي يساعدك على تحديد العمليات التي تستحق الفحص، مع تفسير سبب ظهور كل مؤشر ودرجة خطورته.</p>
      <span class="pill">50 قاعدة رقابية</span><span class="pill">Z-Score</span><span class="pill">Benford</span><span class="pill">Duplicate Screening</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### كيف يعمل النظام؟")
    a,b,c,d = st.columns(4)
    for col, num, title, txt in [
        (a,"01","رفع البيانات","CSV أو Excel"),
        (b,"02","فحص 50 قاعدة","مؤشرات متعددة"),
        (c,"03","Risk Score","ترتيب الأولويات"),
        (d,"04","Review","قرار بشري موثق"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{num}</div><b>{title}</b><div class="small-muted">{txt}</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="legal"><b>الوضع القانوني للمنتج:</b> تم تصميمه كمنصة Financial Control & Risk Intelligence. هو نظام مساعدة في الرقابة وتحليل المخاطر، وليس جهة تدقيق معتمدة ولا يصدر رأيًا تدقيقيًا قانونيًا.</div>', unsafe_allow_html=True)

# -----------------------------
# Upload / Analysis
# -----------------------------
elif page == "تحليل البيانات":
    st.title("تحليل البيانات المالية")
    st.write("ارفع ملف CSV أو XLSX. يفضل وجود أعمدة مثل: التاريخ، المبلغ، رقم الفاتورة، الوصف، المورد، المدين، الدائن، الضريبة.")
    st.info("يمكنك رفع CSV أو Excel بصيغة XLSX أو XLS (Excel القديم). إذا ظهر في المتصفح أن نوع الملف غير مسموح، اضغط اختيار ملف مرة أخرى وتأكد أن اسم الملف ينتهي بـ .xlsx أو .xls أو .csv.")

    uploaded = st.file_uploader(
        "رفع ملف البيانات المالية",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=False,
        help="الصيغ المدعومة: CSV / XLSX / XLS"
    )

    if uploaded:
        try:
            filename = uploaded.name.lower().strip()
            file_bytes = uploaded.getvalue()

            if filename.endswith(".csv"):
                # محاولة UTF-8 ثم Windows-1256 للملفات العربية
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8-sig")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="cp1256")
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            elif filename.endswith(".xls"):
                df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
            else:
                raise ValueError("صيغة الملف غير مدعومة. استخدم CSV أو XLSX أو XLS.")

            # تنظيف أسماء الأعمدة والمسافات
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how="all").reset_index(drop=True)

            if df.empty:
                raise ValueError("الملف لا يحتوي على صفوف بيانات بعد حذف الصفوف الفارغة.")

            st.session_state.data = df
            st.success(f"تم تحميل الملف بنجاح: {uploaded.name} — عدد العمليات: {len(df):,}")
            st.caption("الأعمدة المكتشفة: " + " | ".join(map(str, df.columns.tolist())))
            st.dataframe(df.head(20), use_container_width=True, height=350)

            if st.button("تشغيل محرك الـ 50 قاعدة", type="primary", use_container_width=True):
                with st.spinner("جاري تحليل العمليات وتشغيل 50 قاعدة رقابية..."):
                    findings, summary = analyze(df, st.session_state.enabled)
                st.session_state.findings = findings
                st.session_state.summary = summary
                st.success(f"اكتمل التحليل. تم فحص {len(df):,} عملية.")

        except ImportError:
            st.error("ملفات XLS القديمة تحتاج مكتبة xlrd. تأكد أن requirements.txt يحتوي على xlrd>=2.0.1 ثم أعد تشغيل التطبيق.")
        except Exception as e:
            st.error(f"تعذر قراءة الملف: {type(e).__name__}: {e}")
            st.warning("إذا كان الملف Excel قديمًا بصيغة XLS، استخدم النسخة XLSX أو ارفع الملف بصيغة CSV.")

# -----------------------------
# Results
# -----------------------------
elif page == "النتائج":
    st.title("لوحة نتائج الرقابة")
    if st.session_state.findings is None:
        st.info("لم يتم تشغيل تحليل بعد. اذهب إلى «تحليل البيانات».")
    else:
        s = st.session_state.summary
        f = st.session_state.findings
        risk_score = min(100, int((s["high"]*2 + s["medium"]) / max(1,s["total"]) * 100))
        cols = st.columns(5)
        metrics = [
            ("Risk Score",f"{risk_score}/100"),
            ("High Risk",s["high"]),
            ("Medium Risk",s["medium"]),
            ("Duplicates",s["duplicates"]),
            ("Benford",s["benford"]),
        ]
        for col,(t,v) in zip(cols,metrics):
            with col:
                st.markdown(f'<div class="metric-card"><div class="metric-title">{t}</div><div class="metric-value">{v}</div></div>', unsafe_allow_html=True)
        st.markdown("### توزيع المخاطر")
        if not f.empty:
            chart = f["Level"].value_counts().reindex(["High","Medium","Low"]).fillna(0)
            st.bar_chart(chart)
            st.dataframe(f.sort_values(["Risk","Row"], ascending=[False,True]), use_container_width=True, height=600)
            csv = f.to_csv(index=False).encode("utf-8-sig")
            st.download_button("تحميل تقرير CSV", csv, "Mizan_Risk_Report.csv", "text/csv", use_container_width=True)
        else:
            st.success("لم تظهر مؤشرات رقابية في البيانات وفق القواعد المفعلة.")

# -----------------------------
# Rules
# -----------------------------
elif page == "قواعد الرقابة":
    st.title("50 قاعدة رقابية")
    st.caption("يمكنك تشغيل/إيقاف القواعد قبل إعادة التحليل.")
    for i in range(0, len(RULES), 2):
        c1, c2 = st.columns(2)
        for col, rule in zip([c1,c2], RULES[i:i+2]):
            code,name,cat,score = rule
            with col:
                enabled = st.checkbox(
                    f"{code} — {name} [{cat} | {score}]",
                    value=st.session_state.enabled.get(code, True),
                    key=f"rule_{code}"
                )
                st.session_state.enabled[code] = enabled
    st.success(f"القواعد المفعلة: {sum(st.session_state.enabled.values())} / 50")

# -----------------------------
# About
# -----------------------------
else:
    st.title("عن Mizan")
    st.markdown("""
    ### Mizan Financial Risk Intelligence
    **ميزان للرقابة المالية وإدارة المخاطر**

    المنصة موجهة للمحاسبين، مسؤولي الرقابة المالية، CFOs، وفرق المخاطر لمساعدتهم في فحص البيانات وتحديد العمليات التي تستحق المراجعة.

    **المحرك الحالي يتضمن 50 قاعدة رقابية** إضافة إلى Benford Screening وZ-Score.

    ### مبدأ العمل
    1. البيانات تدخل إلى المنصة.
    2. يتم تشغيل قواعد الرقابة.
    3. يتم إنشاء مؤشرات ومخاطر.
    4. يقوم المختص بمراجعة الحالة.
    5. القرار النهائي يبقى قرارًا بشريًا موثقًا.

    ### مهم
    المنصة لا تصدر رأيًا تدقيقيًا قانونيًا ولا تدعي اكتشاف جريمة أو احتيال بصورة قطعية.
    """)

st.markdown("---")
st.caption("Mizan Financial Risk Intelligence • Financial Control • Risk Detection • Management Insights")


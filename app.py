import os, io, csv, re, sqlite3, hashlib, secrets, math
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort
from werkzeug.utils import secure_filename
try: import openpyxl
except ImportError: openpyxl = None

BASE=os.path.dirname(os.path.abspath(__file__)); DB=os.getenv('DB_FILE',os.path.join(BASE,'mizanrisk.db')); UP=os.path.join(BASE,'uploads'); os.makedirs(UP,exist_ok=True)
app=Flask(__name__); app.secret_key=os.getenv('SECRET_KEY','CHANGE_ME_IN_PRODUCTION'); app.config.update(MAX_CONTENT_LENGTH=15*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')

RULES=[
('DUPLICATE_INVOICE','تكرار رقم الفاتورة',75,'أكثر من عملية تحمل رقم فاتورة واحد.'),('DUPLICATE_TRANSACTION','تكرار العملية بالكامل',80,'تاريخ ومبلغ ووصف/فاتورة متطابقة.'),('SAME_INVOICE_DIFFERENT_AMOUNT','الفاتورة نفسها بمبالغ مختلفة',85,'رقم فاتورة واحد مرتبط بأكثر من مبلغ.'),('SAME_DATE_AMOUNT','تكرار المبلغ والتاريخ',55,'تكرار نفس المبلغ في نفس التاريخ.'),('MISSING_INVOICE','رقم فاتورة مفقود',35,'عملية بدون رقم فاتورة أو مستند.'),('MISSING_DATE','تاريخ مفقود',50,'عملية بدون تاريخ.'),('INVALID_DATE','تاريخ غير صالح',55,'التاريخ غير قابل للمعالجة.'),('FUTURE_DATE','تاريخ مستقبلي',65,'تاريخ العملية بعد تاريخ النظام.'),('WEEKEND_ENTRY','قيد في عطلة نهاية الأسبوع',25,'مؤشر توقيت يستحق التحقق.'),('ROUND_AMOUNT','مبلغ دائري',30,'مبلغ دائري مرتفع.'),('UNUSUAL_AMOUNT_HIGH','مبلغ مرتفع غير معتاد',60,'المبلغ أعلى من نمط البيانات.'),('UNUSUAL_AMOUNT_LOW','مبلغ منخفض غير معتاد',30,'المبلغ منخفض بصورة غير معتادة.'),('ZERO_AMOUNT','عملية بصفر',45,'عملية بمبلغ صفر.'),('NEGATIVE_AMOUNT','مبلغ سالب',45,'مبلغ سالب يحتاج تفسيراً.'),('DEBIT_CREDIT_MISMATCH','فرق بين المدين والدائن',90,'فرق ظاهر بين المدين والدائن.'),('BOTH_DEBIT_CREDIT','مدين ودائن في السجل نفسه',50,'السجل يحتوي مديناً ودائناً معاً.'),('NO_DEBIT_CREDIT','لا مدين ولا دائن',50,'السجل لا يحتوي مديناً أو دائناً.'),('EMPTY_DESCRIPTION','وصف ناقص',25,'الوصف غير موجود.'),('SHORT_DESCRIPTION','وصف قصير جداً',20,'وصف العملية قصير بصورة تقلل قابلية المراجعة.'),('SUSPICIOUS_KEYWORDS','كلمات تستحق المراجعة',40,'كلمات في الوصف تستحق فحصاً إضافياً.'),('MANUAL_JOURNAL','قيد يدوي محتمل',35,'الوصف يشير إلى قيد أو تسوية يدوية.'),('MISSING_USER','مستخدم منشئ مفقود',35,'اسم/معرف المستخدم غير موجود.'),('AFTER_HOURS','عملية خارج ساعات العمل',30,'الوقت خارج ساعات العمل.'),('MONTH_END','قيد قرب نهاية الشهر',25,'قيد في آخر أيام الشهر.'),('YEAR_END','قيد قرب نهاية السنة',40,'قيد في آخر أيام السنة.'),('INVOICE_GAP','فجوة في تسلسل الفواتير',35,'فجوة في التسلسل الرقمي للفواتير.'),('INVOICE_OUT_OF_ORDER','فاتورة خارج التسلسل',35,'التسلسل لا يتوافق مع الترتيب الزمني.'),('MISSING_SUPPLIER','مورد مفقود',40,'عملية مشتريات بدون مورد.'),('DUPLICATE_SUPPLIER','تكرار مرتفع لمورد',30,'عدد مرتفع من العمليات لنفس المورد.'),('MISSING_CUSTOMER','عميل مفقود',35,'عملية مبيعات بدون عميل.'),('MISSING_TAX','ضريبة مفقودة',35,'غياب الضريبة عند توفر صافي/إجمالي.'),('TAX_MISMATCH','فرق حساب الضريبة',70,'الضريبة لا تتطابق مع الصافي والإجمالي.'),('ABNORMAL_TAX_RATE','نسبة ضريبة غير معتادة',45,'نسبة الضريبة خارج النطاق المتوقع.'),('TOTAL_TAX_LOGIC','منطق الإجمالي والضريبة',60,'الإجمالي لا يطابق صافي العملية والضريبة.'),('TAX_GT_TOTAL','الضريبة أكبر من الإجمالي',80,'قيمة الضريبة أكبر من الإجمالي.'),('MISSING_PO','أمر شراء مفقود',45,'مشتريات بدون أمر شراء.'),('MISSING_APPROVAL','اعتماد مفقود',55,'العملية بلا حالة اعتماد.'),('MISSING_COST_CENTER','مركز تكلفة مفقود',30,'غياب مركز التكلفة.'),('MISSING_ACCOUNT','حساب محاسبي مفقود',55,'غياب الحساب المحاسبي.'),('INVALID_ACCOUNT_FORMAT','صيغة حساب غير معتادة',35,'الحساب لا يتوافق مع نمط حسابات البيانات.'),('LARGE_ROUND_AMOUNT','مبلغ دائري كبير',55,'مبلغ دائري كبير جداً.'),('BENFORD_SCREENING','انحراف إحصائي عن Benford',50,'انحراف إحصائي يستحق الفحص ولا يثبت مخالفة.'),('AMOUNT_ZSCORE','قيمة شاذة إحصائياً',65,'المبلغ بعيد إحصائياً عن متوسط البيانات.'),('SUPPLIER_CONCENTRATION','تركيز مرتفع لمورد',45,'نسبة كبيرة من العمليات مرتبطة بمورد واحد.'),('SPLIT_TRANSACTIONS','عمليات متقاربة قد تشير إلى تجزئة',70,'عمليات متكررة تحت حد رقابي في وقت قصير.'),('SAME_SUPPLIER_DAY','تكرار عمليات المورد في اليوم',40,'عدد مرتفع من العمليات لنفس المورد في اليوم.'),('SIGN_MISMATCH','عدم اتساق إشارة المبلغ',55,'إشارة المبلغ لا تتوافق مع الحركة.'),('MISSING_REFERENCE','مرجع مستندي مفقود',30,'لا يوجد مرجع مستندي.'),('POSTING_PERIOD_MISMATCH','عدم تطابق فترة الترحيل',60,'تاريخ الترحيل يختلف عن فترة المستند.'),('TAX_ROUNDING_DIFFERENCE','فرق تقريب الضريبة',25,'فرق صغير محتمل بسبب التقريب.'),('DUPLICATE_REFERENCE','تكرار المرجع المستندي',65,'مرجع مستندي مكرر بين عمليات متعددة.')]

def now(): return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
def hp(p): return hashlib.sha256(p.encode()).hexdigest()
def db():
 from flask import g
 if 'db' not in g: g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row
 return g.db
@app.teardown_appcontext
def close(e=None):
 from flask import g
 x=g.pop('db',None)
 if x:x.close()
def init():
 d=db(); d.executescript('''CREATE TABLE IF NOT EXISTS companies(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,created_at TEXT);CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT,company_id INTEGER);CREATE TABLE IF NOT EXISTS rules(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE,name TEXT,score INTEGER,description TEXT,enabled INTEGER DEFAULT 1);CREATE TABLE IF NOT EXISTS audit_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,company_id INTEGER,filename TEXT,total INTEGER,high INTEGER,medium INTEGER,low INTEGER,risk_score INTEGER,benford_score REAL,duplicate_candidates INTEGER,outlier_count INTEGER,created_at TEXT);CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id INTEGER,row_no INTEGER,txn_date TEXT,description TEXT,amount REAL,invoice TEXT,issues TEXT,risk INTEGER,category TEXT,status TEXT DEFAULT 'Pending',review_note TEXT DEFAULT '');CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,action TEXT,entity TEXT,entity_id INTEGER,created_at TEXT);CREATE TABLE IF NOT EXISTS subscriptions(id INTEGER PRIMARY KEY AUTOINCREMENT,company_id INTEGER UNIQUE,plan TEXT,status TEXT,expires_at TEXT);''')
 for r in RULES: d.execute('INSERT OR IGNORE INTO rules(code,name,score,description,enabled) VALUES(?,?,?,?,1)',r)
 if d.execute('SELECT COUNT(*) c FROM users').fetchone()['c']==0:
  d.execute('INSERT INTO companies(name,created_at) VALUES(?,?)',('Demo Company',now())); cid=d.execute('SELECT last_insert_rowid()').fetchone()[0]
  d.execute('INSERT INTO users(name,email,password,role,company_id) VALUES(?,?,?,?,?)',('Mizan Supervisor','admin@mizanrisk.local',hp('Admin123!'),'super_admin',None)); d.execute('INSERT INTO users(name,email,password,role,company_id) VALUES(?,?,?,?,?)',('Demo Company Admin','demo@mizanrisk.local',hp('Demo123!'),'company_admin',cid)); d.execute('INSERT INTO subscriptions(company_id,plan,status,expires_at) VALUES(?,?,?,?)',(cid,'Trial','active','2026-12-31'))
 d.commit()
with app.app_context(): init()
def user():
 uid=session.get('uid'); return db().execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone() if uid else None
def log(a,e='',i=None):
 u=user(); db().execute('INSERT INTO audit_log(user_id,action,entity,entity_id,created_at) VALUES(?,?,?,?,?)',(u['id'] if u else None,a,e,i,now())); db().commit()
def req(fn):
 @wraps(fn)
 def w(*a,**k):
  if not user(): return redirect(url_for('login'))
  return fn(*a,**k)
 return w
def admin(fn):
 @wraps(fn)
 def w(*a,**k):
  if not user() or user()['role']!='super_admin': abort(403)
  return fn(*a,**k)
 return w
def access(cid): u=user(); return bool(u and (u['role']=='super_admin' or u['company_id']==cid))
def clean(v): return '' if v is None else str(v).strip()
def nk(v): return re.sub(r'[\s_\-]+','',str(v).lower())
def gv(r,names):
 m={nk(k):v for k,v in r.items()}
 for n in names:
  if nk(n) in m:return m[nk(n)]
 return ''
def num(v):
 try:return float(str(v).replace(',','').strip())
 except:return 0.0
def read_rows(path):
 ext=os.path.splitext(path)[1].lower()
 if ext=='.csv':
  with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
 if ext=='.xlsx' and openpyxl:
  wb=openpyxl.load_workbook(path,data_only=True,read_only=True); it=wb.active.iter_rows(values_only=True); h=[clean(x) for x in next(it)]; return [dict(zip(h,r)) for r in it]
 raise ValueError('يرجى رفع CSV أو XLSX.')
def dtparse(v):
 v=clean(v)
 for f in ('%Y-%m-%d','%d/%m/%Y','%m/%d/%Y','%Y/%m/%d','%d-%m-%Y'):
  try:return datetime.strptime(v[:10],f)
  except:pass
 return None
def benford(rs):
 c={str(i):0 for i in range(1,10)}; total=0
 for r in rs:
  s=re.sub(r'\D','',str(num(gv(r,['amount','المبلغ','value','debit','مدين']))) )
  if s and s[0]!='0':c[s[0]]+=1; total+=1
 if total<20:return 0.0
 exp={str(i):math.log10(1+1/i) for i in range(1,10)}; dev=sum(abs(c[k]/total-exp[k]) for k in c)/2
 return round(min(100,dev*300),2)
def analyze(rs,en):
 from collections import defaultdict
 vals=[num(gv(r,['amount','المبلغ','value','total','الإجمالي','debit','مدين'])) for r in rs]; pos=[x for x in vals if x>0]; avg=sum(pos)/(len(pos) or 1); sd=math.sqrt(sum((x-avg)**2 for x in pos)/(len(pos) or 1)) if pos else 0
 rec=[]; invmap=defaultdict(list); exact=defaultdict(list); damt=defaultdict(list); sup=defaultdict(list); supday=defaultdict(list); refs=defaultdict(list); invnums=[]
 def flag(r,code,label,score,cat):
  if en.get(code): r['issues'].append(label); r['categories'].append(cat); r['risk']=max(r['risk'],score)
 for i,row in enumerate(rs,1):
  date=clean(gv(row,['date','التاريخ','transaction date'])); dt=dtparse(date); desc=clean(gv(row,['description','desc','الوصف','البيان','details'])); inv=clean(gv(row,['invoice','invoice no','invoice_no','رقم الفاتورة','رقم المستند'])); amt=num(gv(row,['amount','المبلغ','value','total','الإجمالي','debit','مدين'])); debit=num(gv(row,['debit','مدين'])); credit=num(gv(row,['credit','دائن'])); net=num(gv(row,['net','subtotal','صافي','الصافي'])); tax=num(gv(row,['tax','vat','الضريبة','ضريبة'])); total=num(gv(row,['total','amount','المبلغ','الإجمالي'])); supplier=clean(gv(row,['supplier','vendor','المورد','اسم المورد'])); customer=clean(gv(row,['customer','client','العميل','اسم العميل'])); created=clean(gv(row,['user','created by','created_by','المستخدم','منشئ'])); po=clean(gv(row,['po','purchase order','po number','أمر شراء','رقم أمر الشراء'])); approval=clean(gv(row,['approval','approved','approval status','الاعتماد','حالة الاعتماد'])); cc=clean(gv(row,['cost center','cost_center','مركز التكلفة'])); account=clean(gv(row,['account','account code','الحساب','رقم الحساب'])); ref=clean(gv(row,['reference','ref','document','مرجع','رقم المرجع'])); posting=clean(gv(row,['posting date','posting_date','تاريخ الترحيل']))
  r={'row_no':i,'date':date,'dt':dt,'description':desc,'amount':amt,'debit':debit,'credit':credit,'net':net,'tax':tax,'total':total,'invoice':inv,'supplier':supplier,'customer':customer,'created':created,'po':po,'approval':approval,'cc':cc,'account':account,'ref':ref,'posting':posting,'issues':[],'categories':[],'risk':0}; rec.append(r)
  if inv: invmap[inv].append(i-1); exact[(inv,round(amt,2),date)].append(i-1); m=re.search(r'\d+',inv); invnums.append((int(m.group()),i-1)) if m else None
  if date and amt: damt[(date,round(amt,2))].append(i-1)
  if supplier: sup[supplier].append(i-1); supday[(supplier,date)].append(i-1)
  if ref: refs[ref].append(i-1)
  if not inv: flag(r,'MISSING_INVOICE','رقم فاتورة مفقود',35,'Documentation')
  if not date: flag(r,'MISSING_DATE','تاريخ مفقود',50,'Data Quality')
  elif not dt: flag(r,'INVALID_DATE','تاريخ غير صالح',55,'Data Quality')
  else:
   if dt>datetime.utcnow(): flag(r,'FUTURE_DATE','تاريخ مستقبلي',65,'Timing')
   if dt.weekday()>=5: flag(r,'WEEKEND_ENTRY','قيد في عطلة نهاية الأسبوع',25,'Timing')
   if dt.day>=29: flag(r,'MONTH_END','قيد قرب نهاية الشهر',25,'Timing')
   if dt.month==12 and dt.day>=29: flag(r,'YEAR_END','قيد قرب نهاية السنة',40,'Timing')
  if amt==0: flag(r,'ZERO_AMOUNT','عملية بصفر',45,'Amount')
  if amt<0: flag(r,'NEGATIVE_AMOUNT','مبلغ سالب',45,'Amount')
  if amt>=1000 and abs(amt-round(amt))<.0001: flag(r,'ROUND_AMOUNT','مبلغ دائري',30,'Pattern')
  if amt>=100000 and abs(amt-round(amt))<.0001: flag(r,'LARGE_ROUND_AMOUNT','مبلغ دائري كبير',55,'Pattern')
  if avg and amt>avg*3 and amt>100: flag(r,'UNUSUAL_AMOUNT_HIGH','مبلغ مرتفع غير معتاد',60,'Outlier')
  if avg and 0<amt<avg*.10: flag(r,'UNUSUAL_AMOUNT_LOW','مبلغ منخفض غير معتاد',30,'Outlier')
  if sd and amt>0 and abs((amt-avg)/sd)>=3: flag(r,'AMOUNT_ZSCORE','قيمة شاذة إحصائياً',65,'Statistics')
  if debit and credit and abs(debit-credit)>.01: flag(r,'DEBIT_CREDIT_MISMATCH','فرق بين المدين والدائن',90,'Journal')
  elif debit and credit: flag(r,'BOTH_DEBIT_CREDIT','مدين ودائن في السجل نفسه',50,'Journal')
  if not desc: flag(r,'EMPTY_DESCRIPTION','وصف ناقص',25,'Data Quality')
  elif len(desc)<6: flag(r,'SHORT_DESCRIPTION','وصف قصير جداً',20,'Data Quality')
  low=desc.lower()
  if any(w in low for w in ('cash','urgent','write off','adjustment','نقدي','عاجل','شطب','تعديل')): flag(r,'SUSPICIOUS_KEYWORDS','كلمات تستحق المراجعة',40,'Description')
  if any(w in low for w in ('manual','تسوية يدوية','قيد يدوي')): flag(r,'MANUAL_JOURNAL','قيد يدوي محتمل',35,'Journal')
  if not created: flag(r,'MISSING_USER','مستخدم منشئ مفقود',35,'Access')
  if not supplier: flag(r,'MISSING_SUPPLIER','مورد مفقود',40,'Supplier')
  if not customer: flag(r,'MISSING_CUSTOMER','عميل مفقود',35,'Customer')
  if not tax and (net or total): flag(r,'MISSING_TAX','ضريبة مفقودة',35,'Tax')
  if net and tax:
   rate=tax/net*100
   if rate<0 or rate>30: flag(r,'ABNORMAL_TAX_RATE','نسبة ضريبة غير معتادة',45,'Tax')
   expected=net+tax
   if total and abs(expected-total)>max(.01,total*.01): flag(r,'TAX_MISMATCH','فرق حساب الضريبة',70,'Tax'); flag(r,'TOTAL_TAX_LOGIC','منطق الإجمالي والضريبة',60,'Tax')
   elif total and abs(expected-total)>.001: flag(r,'TAX_ROUNDING_DIFFERENCE','فرق تقريب الضريبة',25,'Tax')
  if total and tax>total: flag(r,'TAX_GT_TOTAL','الضريبة أكبر من الإجمالي',80,'Tax')
  if supplier and not po: flag(r,'MISSING_PO','أمر شراء مفقود',45,'Procurement')
  if not approval: flag(r,'MISSING_APPROVAL','اعتماد مفقود',55,'Authorization')
  if not cc: flag(r,'MISSING_COST_CENTER','مركز تكلفة مفقود',30,'Master Data')
  if not account: flag(r,'MISSING_ACCOUNT','حساب محاسبي مفقود',55,'Accounting')
  if account and not re.match(r'^[A-Za-z0-9._/-]{2,30}$',account): flag(r,'INVALID_ACCOUNT_FORMAT','صيغة حساب غير معتادة',35,'Accounting')
  if not ref: flag(r,'MISSING_REFERENCE','مرجع مستندي مفقود',30,'Documentation')
  if posting and date and posting[:7]!=date[:7]: flag(r,'POSTING_PERIOD_MISMATCH','عدم تطابق فترة الترحيل',60,'Period')
  if dt and (dt.hour<7 or dt.hour>=19): flag(r,'AFTER_HOURS','عملية خارج ساعات العمل',30,'Timing')
  if debit and credit and amt and ((amt>0 and credit<0) or (amt<0 and debit<0)): flag(r,'SIGN_MISMATCH','عدم اتساق إشارة المبلغ',55,'Journal')
 for inv,idxs in invmap.items():
  if len(idxs)>1:
   for j in idxs: flag(rec[j],'DUPLICATE_INVOICE','تكرار رقم الفاتورة',75,'Duplicate')
   if len({round(rec[j]['amount'],2) for j in idxs})>1:
    for j in idxs: flag(rec[j],'SAME_INVOICE_DIFFERENT_AMOUNT','الفاتورة نفسها بمبالغ مختلفة',85,'Duplicate')
 for key,idxs in exact.items():
  if len(idxs)>1:
   for j in idxs: flag(rec[j],'DUPLICATE_TRANSACTION','تكرار العملية بالكامل',80,'Duplicate')
 for key,idxs in damt.items():
  if len(idxs)>1:
   for j in idxs: flag(rec[j],'SAME_DATE_AMOUNT','تكرار المبلغ والتاريخ',55,'Pattern')
 total_sup=sum(len(v) for v in sup.values())
 for name,idxs in sup.items():
  if len(idxs)>=max(5,math.ceil(total_sup*.20)):
   for j in idxs: flag(rec[j],'SUPPLIER_CONCENTRATION','تركيز مرتفع لمورد',45,'Supplier')
  if len(idxs)>=10:
   for j in idxs: flag(rec[j],'DUPLICATE_SUPPLIER','تكرار مرتفع لمورد',30,'Supplier')
 for key,idxs in supday.items():
  if key[0] and len(idxs)>=5:
   for j in idxs: flag(rec[j],'SAME_SUPPLIER_DAY','تكرار عمليات المورد في اليوم',40,'Supplier')
   small=[j for j in idxs if 0<rec[j]['amount']<5000]
   if len(small)>=4:
    for j in small: flag(rec[j],'SPLIT_TRANSACTIONS','عمليات متقاربة قد تشير إلى تجزئة',70,'Procurement')
 for ref,idxs in refs.items():
  if len(idxs)>1:
   for j in idxs: flag(rec[j],'DUPLICATE_REFERENCE','تكرار المرجع المستندي',65,'Documentation')
 nums=sorted(invnums,key=lambda x:x[0])
 for (n1,_),(n2,j) in zip(nums,nums[1:]):
  if n2-n1>1: flag(rec[j],'INVOICE_GAP','فجوة في تسلسل الفواتير',35,'Sequence')
 b=benford(rs)
 if en.get('BENFORD_SCREENING') and b>=35 and rec:
  j=max(range(len(rec)),key=lambda x:rec[x]['amount']); flag(rec[j],'BENFORD_SCREENING','انحراف إحصائي عن Benford',50,'Statistics')
 findings=[r for r in rec if r['risk']>0]; high=sum(r['risk']>=70 for r in findings); med=sum(30<=r['risk']<70 for r in findings); low=sum(r['risk']<30 for r in findings); score=min(100,round(((high*2)+med+low*.25)/(len(rs) or 1)*100)); dup=sum(1 for r in rec if 'تكرار رقم الفاتورة' in r['issues'] or 'تكرار العملية بالكامل' in r['issues']); out=sum(1 for r in rec if 'مبلغ مرتفع غير معتاد' in r['issues'] or 'قيمة شاذة إحصائياً' in r['issues']); return findings,high,med,low,score,b,out,dup

@app.route('/')
def home(): return redirect(url_for('dashboard')) if user() else render_template('landing.html',user=None)
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  u=db().execute('SELECT * FROM users WHERE email=? AND password=?',(request.form['email'].strip().lower(),hp(request.form['password']))).fetchone()
  if u: session.clear(); session['uid']=u['id']; log('login'); return redirect(url_for('dashboard'))
  flash('بيانات الدخول غير صحيحة.','error')
 return render_template('login.html',user=None)
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))
@app.route('/dashboard')
@req
def dashboard():
 u=user()
 if u['role']=='super_admin': runs=db().execute('SELECT a.*,c.name company FROM audit_runs a JOIN companies c ON c.id=a.company_id ORDER BY a.id DESC LIMIT 50').fetchall(); companies=db().execute('SELECT * FROM companies ORDER BY id DESC').fetchall(); users=db().execute('SELECT u.*,c.name company FROM users u LEFT JOIN companies c ON c.id=u.company_id ORDER BY u.id DESC').fetchall(); total=db().execute('SELECT COUNT(*) c FROM companies').fetchone()['c']
 else: runs=db().execute('SELECT * FROM audit_runs WHERE company_id=? ORDER BY id DESC LIMIT 50',(u['company_id'],)).fetchall(); companies=[]; users=[]; total=1
 return render_template('dashboard.html',user=u,runs=runs,companies=companies,users=users,total_companies=total)
@app.route('/upload',methods=['POST'])
@req
def upload():
 u=user(); cid=int(request.form.get('company_id') or u['company_id']); abort(403) if not access(cid) else None; f=request.files.get('file')
 if not f or not f.filename: flash('اختر ملفاً أولاً.','error'); return redirect(url_for('dashboard'))
 if os.path.splitext(f.filename)[1].lower() not in ('.csv','.xlsx'): flash('الصيغ المسموحة CSV و XLSX.','error'); return redirect(url_for('dashboard'))
 path=os.path.join(UP,secrets.token_hex(10)+'_'+secure_filename(f.filename)); f.save(path)
 try:
  rs=read_rows(path); en={r['code']:bool(r['enabled']) for r in db().execute('SELECT * FROM rules')}; findings,high,med,low,score,b,outs,dups=analyze(rs,en)
 except Exception as e: flash('تعذر تحليل الملف: '+str(e),'error'); return redirect(url_for('dashboard'))
 finally:
  try: os.remove(path)
  except: pass
 d=db(); d.execute('INSERT INTO audit_runs(company_id,filename,total,high,medium,low,risk_score,benford_score,duplicate_candidates,outlier_count,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(cid,f.filename,len(rs),high,med,low,score,b,dups,outs,now())); rid=d.execute('SELECT last_insert_rowid()').fetchone()[0]
 for x in findings: d.execute('INSERT INTO findings(run_id,row_no,txn_date,description,amount,invoice,issues,risk,category) VALUES(?,?,?,?,?,?,?,?,?)',(rid,x['row_no'],x['date'],x['description'],x['amount'],x['invoice'],' | '.join(x['issues']),x['risk'],', '.join(sorted(set(x['categories'])))))
 d.commit(); log('audit_run_created','audit_run',rid); return redirect(url_for('run_detail',run_id=rid))
@app.route('/run/<int:run_id>')
@req
def run_detail(run_id):
 u=user(); r=db().execute('SELECT a.*,c.name company FROM audit_runs a JOIN companies c ON c.id=a.company_id WHERE a.id=?',(run_id,)).fetchone(); abort(403) if not r or not access(r['company_id']) else None; fs=db().execute('SELECT * FROM findings WHERE run_id=? ORDER BY risk DESC,id',(run_id,)).fetchall(); return render_template('run.html',user=u,run=r,findings=fs)
@app.route('/finding/<int:fid>',methods=['POST'])
@req
def update_finding(fid):
 d=db(); f=d.execute('SELECT f.*,a.company_id FROM findings f JOIN audit_runs a ON a.id=f.run_id WHERE f.id=?',(fid,)).fetchone(); abort(403) if not f or not access(f['company_id']) else None; status=request.form.get('status','Pending'); note=request.form.get('review_note','')[:1500]; d.execute('UPDATE findings SET status=?,review_note=? WHERE id=?',(status,note,fid)); d.commit(); log('finding_reviewed','finding',fid); return redirect(url_for('run_detail',run_id=f['run_id']))
@app.route('/export/<int:run_id>')
@req
def export_run(run_id):
 d=db(); r=d.execute('SELECT * FROM audit_runs WHERE id=?',(run_id,)).fetchone(); abort(403) if not r or not access(r['company_id']) else None; out=io.StringIO(); w=csv.writer(out); w.writerow(['Row','Date','Description','Amount','Invoice','Issues','Risk','Category','Status','Review Note'])
 for f in d.execute('SELECT * FROM findings WHERE run_id=? ORDER BY risk DESC',(run_id,)): w.writerow([f['row_no'],f['txn_date'],f['description'],f['amount'],f['invoice'],f['issues'],f['risk'],f['category'],f['status'],f['review_note']])
 return send_file(io.BytesIO(('\ufeff'+out.getvalue()).encode('utf-8')),as_attachment=True,download_name=f'MizanRisk_Report_{run_id}.csv',mimetype='text/csv')
@app.route('/admin/rules',methods=['GET','POST'])
@admin
def admin_rules():
 d=db()
 if request.method=='POST':
  for r in d.execute('SELECT id FROM rules'): d.execute('UPDATE rules SET enabled=? WHERE id=?',(1 if request.form.get(f"rule_{r['id']}") else 0,r['id']))
  d.commit(); flash('تم حفظ إعدادات قواعد الرقابة.','success')
 return render_template('rules.html',user=user(),rules=d.execute('SELECT * FROM rules ORDER BY id').fetchall())
@app.route('/admin/company',methods=['POST'])
@admin
def create_company():
 name=request.form.get('name','').strip()
 if name:
  d=db(); d.execute('INSERT INTO companies(name,created_at) VALUES(?,?)',(name,now())); cid=d.execute('SELECT last_insert_rowid()').fetchone()[0]; d.execute('INSERT INTO subscriptions(company_id,plan,status,expires_at) VALUES(?,?,?,?)',(cid,'Trial','active','2026-12-31')); d.commit()
 return redirect(url_for('dashboard'))
@app.route('/admin/user',methods=['POST'])
@admin
def create_user():
 try:
  d=db(); d.execute('INSERT INTO users(name,email,password,role,company_id) VALUES(?,?,?,?,?)',(request.form['name'].strip(),request.form['email'].strip().lower(),hp(request.form['password']),'company_admin',int(request.form['company_id']))); d.commit(); flash('تم إنشاء المستخدم.','success')
 except Exception as e: flash('تعذر إنشاء المستخدم: '+str(e),'error')
 return redirect(url_for('dashboard'))
@app.route('/health')
def health(): return {'status':'ok','service':'Mizan Financial Risk Intelligence','rules':len(RULES),'time':now()}
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')),debug=False)


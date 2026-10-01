"""תבניות Jinja. כל המשתנים עוברים דרך {{ }} (escape אוטומטי) - אף פעם לא דרך f-string."""

CSRF = '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'

BASE = """<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}SH{% endblock %} · SH</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
<style>
:root{--brand:#4f46e5;--brand-d:#4338ca}
body{font-family:'Heebo',system-ui,sans-serif;background:#f4f5fb;color:#1f2430}
.card{border:0;border-radius:16px;box-shadow:0 2px 14px rgba(30,30,70,.07)}
.btn{border-radius:10px;font-weight:500}
.btn-primary{--bs-btn-bg:var(--brand);--bs-btn-border-color:var(--brand);--bs-btn-hover-bg:var(--brand-d);--bs-btn-hover-border-color:var(--brand-d);--bs-btn-active-bg:var(--brand-d);--bs-btn-active-border-color:var(--brand-d)}
.form-control,.form-select{border-radius:10px}
.topbar{background:#fff;border-bottom:1px solid #e8e9f3}
.brand-mark{width:56px;height:56px;border-radius:16px;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:22px;margin:0 auto 14px}
.brand-sm{width:34px;height:34px;font-size:14px;border-radius:10px;margin:0}
.nav-pills .nav-link{border-radius:10px;color:#555}
.nav-pills .nav-link.active{background:var(--brand)}
.ltr{direction:ltr;text-align:left}
.code{font-family:ui-monospace,Consolas,monospace;font-size:.9rem}
.step-num{width:28px;height:28px;border-radius:50%;background:#eef0ff;color:var(--brand);display:inline-flex;align-items:center;justify-content:center;font-weight:700;flex:none}
.url-chip{background:#f1f2fa;border-radius:8px;padding:2px 8px;font-size:.85rem;word-break:break-all}
</style>
</head>
<body>
{% if current_user %}
<header class="topbar mb-4"><div class="container py-2 d-flex justify-content-between align-items-center" style="max-width:1080px">
  <a href="{{ url_for('index') }}" class="d-flex align-items-center gap-2 text-decoration-none text-dark fw-bold">
    <span class="brand-mark brand-sm">SH</span>מערכת שרתים
  </a>
  <div class="d-flex align-items-center gap-3">
    <span class="text-muted small d-none d-sm-inline">{{ current_user.username }}{% if current_user.is_admin %} <span class="badge bg-primary">מנהל</span>{% endif %}</span>
    <form method="post" action="{{ url_for('logout') }}" class="m-0">__CSRF__<button class="btn btn-outline-secondary btn-sm">התנתק</button></form>
  </div>
</div></header>
{% endif %}
<main class="container pb-5" style="max-width:1080px">
{% with messages = get_flashed_messages(with_categories=true) %}{% for cat, msg in messages %}
<div class="alert alert-{{ cat }} alert-dismissible fade show" role="alert">{{ msg }}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="סגור"></button></div>
{% endfor %}{% endwith %}
{% block content %}{% endblock %}
</main>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
document.querySelectorAll('form').forEach(function(f){f.addEventListener('submit',function(){
  var b=f.querySelector('button.js-load'); if(b){b.disabled=true;b.textContent='רגע...';}
});});
</script>
{% block scripts %}{% endblock %}
</body>
</html>"""

LOGIN = """{% extends 'base.html' %}
{% block title %}כניסה{% endblock %}
{% block content %}
{% set tab = tab|default('login') %}
<div class="d-flex justify-content-center pt-4">
<div class="card p-4 p-md-5 w-100" style="max-width:460px">
  <div class="brand-mark">SH</div>
  <h3 class="text-center mb-1">ברוכים הבאים</h3>
  <p class="text-center text-muted mb-4">מדביקים קוד, ומקבלים שרת באינטרנט.</p>

  <ul class="nav nav-pills nav-fill mb-4">
    <li class="nav-item"><button type="button" class="nav-link {% if tab != 'register' %}active{% endif %}" data-bs-toggle="pill" data-bs-target="#pane-login">התחברות</button></li>
    <li class="nav-item"><button type="button" class="nav-link {% if tab == 'register' %}active{% endif %}" data-bs-toggle="pill" data-bs-target="#pane-register">הרשמה</button></li>
  </ul>

  <div class="tab-content">
    <div class="tab-pane fade {% if tab != 'register' %}show active{% endif %}" id="pane-login">
      <form method="post" action="{{ url_for('login_page') }}">
        __CSRF__
        <input type="hidden" name="action" value="login">
        <label class="form-label">שם משתמש</label>
        <input type="text" name="username" class="form-control ltr mb-3" data-lower required autocomplete="username" autocapitalize="none" value="{% if tab != 'register' %}{{ prefill|default('') }}{% endif %}">
        <label class="form-label">סיסמה</label>
        <div class="input-group mb-4">
          <input type="password" name="password" class="form-control ltr" required autocomplete="current-password">
          <button type="button" class="btn btn-outline-secondary js-eye" tabindex="-1">הצג</button>
        </div>
        <button type="submit" class="btn btn-primary w-100 py-2 js-load">התחבר</button>
      </form>
    </div>

    <div class="tab-pane fade {% if tab == 'register' %}show active{% endif %}" id="pane-register">
      <form method="post" action="{{ url_for('login_page') }}">
        __CSRF__
        <input type="hidden" name="action" value="register">
        <label class="form-label">שם משתמש</label>
        <input type="text" name="username" class="form-control ltr" data-lower required pattern="[a-z][a-z0-9_]{2,29}" title="3 עד 30 תווים: אותיות אנגליות קטנות, ספרות או _, ומתחיל באות" autocomplete="username" autocapitalize="none" value="{% if tab == 'register' %}{{ prefill|default('') }}{% endif %}">
        <div class="form-text mb-3">אנגלית קטנה, ספרות ו-_ בלבד. השם הופך לחלק מהכתובת של השרתים שלך.</div>
        <label class="form-label">סיסמה</label>
        <div class="input-group">
          <input type="password" name="password" class="form-control ltr" required minlength="8" autocomplete="new-password">
          <button type="button" class="btn btn-outline-secondary js-eye" tabindex="-1">הצג</button>
        </div>
        <div class="form-text mb-4">לפחות 8 תווים. אין שחזור סיסמה, אז כדאי לשמור אותה.</div>
        <button type="submit" class="btn btn-primary w-100 py-2 js-load">צור חשבון</button>
      </form>
    </div>
  </div>

  {% if google_enabled %}
  <div class="d-flex align-items-center gap-2 my-4 text-muted small"><hr class="flex-grow-1 m-0">או<hr class="flex-grow-1 m-0"></div>
  <a href="{{ url_for('auth_google') }}" class="btn btn-outline-dark w-100 py-2">המשך עם Google</a>
  {% endif %}
</div>
</div>
{% endblock %}
{% block scripts %}
<script>
document.querySelectorAll('.js-eye').forEach(function(b){b.addEventListener('click',function(){
  var i=b.parentElement.querySelector('input'); var s=i.type==='password';
  i.type=s?'text':'password'; b.textContent=s?'הסתר':'הצג';
});});
document.querySelectorAll('[data-lower]').forEach(function(i){i.addEventListener('input',function(){i.value=i.value.toLowerCase();});});
</script>
{% endblock %}"""

ERROR = """{% extends 'base.html' %}
{% block title %}שגיאה{% endblock %}
{% block content %}
<div class="d-flex justify-content-center pt-5">
  <div class="card p-5 text-center" style="max-width:480px">
    <div class="brand-mark" style="background:#dc3545">!</div>
    <h4 class="mb-2">משהו השתבש</h4>
    <p class="text-muted">{{ message }}</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary mt-2">חזרה לדף הבית</a>
  </div>
</div>
{% endblock %}"""

DASHBOARD = """{% extends 'base.html' %}
{% block title %}לוח בקרה{% endblock %}
{% block content %}
<div class="mb-4">
  <h3 class="mb-0">שלום, {{ current_user.username }}</h3>
  <div class="text-muted">כאן פורסים שרתים חדשים ומנהלים את הקיימים.</div>
</div>

{% if current_user.is_admin %}
<div class="card p-4 mb-4 border-start border-4 border-warning">
  <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
    <h5 class="mb-0">ממתינים לאישור <span class="badge bg-warning text-dark">{{ pending|length }}</span></h5>
    <span class="text-muted small">{{ users_count }} משתמשים · {{ active_count }} שרתים פעילים</span>
  </div>
  {% for r in pending %}
  <div class="d-flex justify-content-between align-items-center py-2 border-top flex-wrap gap-2">
    <div><span class="url-chip ltr d-inline-block">{{ r.full_path }}</span> <span class="text-muted small">{{ r.source_lang }}</span></div>
    <a href="{{ url_for('review_route', route_id=r.id) }}" class="btn btn-sm btn-warning">בדוק ואשר</a>
  </div>
  {% else %}
  <div class="text-muted">אין בקשות ממתינות.</div>
  {% endfor %}
</div>
{% endif %}

<div class="row g-4 mb-4">
  <div class="col-lg-7">
    <div class="card p-4 h-100">
      <h5 class="mb-3">פריסת שרת חדש</h5>
      <form method="post" action="{{ url_for('deploy_server') }}">
        __CSRF__
        <div class="row g-3 mb-3">
          <div class="col-sm-6">
            <label class="form-label">שם הנתיב</label>
            <input type="text" name="route_name" class="form-control ltr" placeholder="hello" required data-lower pattern="[a-z0-9][a-z0-9_]{0,39}" title="אותיות אנגליות קטנות, ספרות או _ (עד 40 תווים)" autocapitalize="none">
            <div class="form-text">הכתובת: <span class="ltr d-inline-block">/{{ current_user.username }}/<b id="rnPreview">...</b></span></div>
          </div>
          <div class="col-sm-6">
            <label class="form-label">שפת הקוד שהדבקת</label>
            <input type="text" name="source_lang" id="lang" list="langs" class="form-control ltr" value="Python" required maxlength="30">
            <datalist id="langs"><option value="Python"><option value="PHP"><option value="JavaScript"><option value="Node.js"><option value="Java"><option value="C#"><option value="Go"><option value="Ruby"></datalist>
          </div>
        </div>

        <div id="pyBox" class="form-check mb-3 d-none">
          <input class="form-check-input" type="checkbox" name="force_ai" value="1" id="force_ai">
          <label class="form-check-label" for="force_ai">לתרגם גם את קוד ה-Python דרך AI (לסקריפט שאינו Blueprint)</label>
        </div>
        <div id="aiBox" class="mb-3 d-none">
          <label class="form-label">ספק AI לתרגום</label>
          <select name="provider" class="form-select">
            {% for key, label in providers.items() %}
            <option value="{{ key }}">{{ label }}{% if key in saved_providers %} ✓{% else %} (אין מפתח){% endif %}</option>
            {% endfor %}
          </select>
        </div>
        <div id="modeHint" class="alert alert-light border small"></div>

        <label class="form-label">הקוד</label>
        <textarea name="code" class="form-control ltr code mb-3" rows="10" required placeholder="הדבק כאן את הקוד..."></textarea>
        <button type="submit" class="btn btn-primary px-4 js-load">שלח לפריסה</button>
      </form>
    </div>
  </div>

  <div class="col-lg-5">
    <div class="card p-4 h-100">
      <h5 class="mb-1">מפתחות API</h5>
      <div class="text-muted small mb-3">נדרשים רק לתרגום קוד משפות שאינן Python. נשמרים מוצפנים.</div>
      {% for key, label in providers.items() %}
      <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
        <span>{{ label }}</span>
        {% if key in saved_providers %}
        <form method="post" action="{{ url_for('update_key') }}" class="m-0 d-flex align-items-center gap-2">
          __CSRF__
          <input type="hidden" name="provider" value="{{ key }}">
          <span class="badge bg-success">שמור</span>
          <button name="action" value="delete" class="btn btn-sm btn-outline-danger">מחק</button>
        </form>
        {% else %}
        <span class="badge bg-secondary">לא הוגדר</span>
        {% endif %}
      </div>
      {% endfor %}
      <form method="post" action="{{ url_for('update_key') }}" class="mt-3">
        __CSRF__
        <label class="form-label small">הוספה או החלפה של מפתח</label>
        <select name="provider" class="form-select mb-2">
          {% for key, label in providers.items() %}<option value="{{ key }}">{{ label }}</option>{% endfor %}
        </select>
        <input type="password" name="api_key" class="form-control ltr mb-2" placeholder="הדבק מפתח" autocomplete="off" required>
        <button name="action" value="save" class="btn btn-outline-primary w-100">שמור מפתח</button>
      </form>
    </div>
  </div>
</div>

<div class="card p-4">
  <h5 class="mb-3">השרתים שלך</h5>
  {% if routes %}
  <div class="table-responsive">
    <table class="table align-middle mb-0">
      <thead><tr><th>כתובת</th><th>סטטוס</th><th></th></tr></thead>
      <tbody>
      {% for route in routes %}
      <tr>
        <td><span class="url-chip ltr d-inline-block">{{ request.host_url.rstrip('/') }}{{ route.full_path }}</span></td>
        <td>
          {% if route.status == 'active' %}<span class="badge bg-success">פעיל</span>
          {% elif route.status == 'rejected' %}<span class="badge bg-danger">נדחה</span>
          {% else %}<span class="badge bg-warning text-dark">ממתין לאישור</span>{% endif %}
          {% if route.status == 'active' and route.pending_code %}<span class="badge bg-warning text-dark">עדכון ממתין</span>{% endif %}
        </td>
        <td class="text-end text-nowrap">
          {% if route.status == 'active' %}
          <button type="button" class="btn btn-sm btn-outline-secondary js-copy" data-url="{{ request.host_url.rstrip('/') }}{{ route.full_path }}">העתק</button>
          <a href="{{ route.full_path }}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary">פתח</a>
          {% endif %}
          <a href="{{ url_for('view_logs', route_id=route.id) }}" class="btn btn-sm btn-outline-secondary">יומנים</a>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="text-muted mb-3">עוד אין לך שרתים. כך זה עובד:</div>
  <div class="d-flex flex-column gap-2">
    <div class="d-flex gap-2 align-items-center"><span class="step-num">1</span>בוחרים שם נתיב ומדביקים קוד בטופס למעלה.</div>
    <div class="d-flex gap-2 align-items-center"><span class="step-num">2</span>מנהל קורא את הקוד ומאשר אותו.</div>
    <div class="d-flex gap-2 align-items-center"><span class="step-num">3</span>השרת עולה בכתובת שמופיעה כאן, ואפשר להעתיק אותה בלחיצה.</div>
  </div>
  {% endif %}
</div>
{% endblock %}
{% block scripts %}
<script>
(function(){
  var PY=['python','py','python3','flask'];
  var lang=document.getElementById('lang'), aiBox=document.getElementById('aiBox'), pyBox=document.getElementById('pyBox');
  var force=document.getElementById('force_ai'), hint=document.getElementById('modeHint');
  function upd(){
    var isPy=PY.indexOf(lang.value.trim().toLowerCase())>-1;
    pyBox.classList.toggle('d-none',!isPy);
    var useAi=!isPy||force.checked;
    aiBox.classList.toggle('d-none',!useAi);
    hint.textContent=useAi
      ? 'הקוד יתורגם ל-Flask על ידי ספק ה-AI שבחרת (נדרש מפתח API שמור).'
      : 'קוד Python נשלח ישירות לבדיקה, בלי AI. הוא חייב להגדיר Blueprint בשם bp עם נתיבים יחסיים, למשל /.';
  }
  lang.addEventListener('input',upd); force.addEventListener('change',upd); upd();
  var rn=document.querySelector('[name=route_name]'), pv=document.getElementById('rnPreview');
  rn.addEventListener('input',function(){pv.textContent=rn.value||'...';});
  document.querySelectorAll('[data-lower]').forEach(function(i){i.addEventListener('input',function(){i.value=i.value.toLowerCase();});});
  document.querySelectorAll('.js-copy').forEach(function(b){b.addEventListener('click',function(){
    navigator.clipboard.writeText(b.dataset.url).then(function(){var t=b.textContent;b.textContent='הועתק';setTimeout(function(){b.textContent=t;},1500);});
  });});
})();
</script>
{% endblock %}"""

REVIEW = """{% extends 'base.html' %}
{% block title %}בדיקת קוד{% endblock %}
{% block content %}
<a href="{{ url_for('index') }}" class="text-decoration-none">&rarr; חזרה ללוח הבקרה</a>
<h3 class="mt-2">בדיקת קוד</h3>
<div class="text-muted mb-3">
  {{ route.owner.username }} · <span class="url-chip ltr d-inline-block">{{ route.full_path }}</span> · שפת מקור: {{ route.source_lang }}
</div>
<div class="alert alert-warning">הקוד ירוץ בתוך תהליך השרת. אשר רק אם קראת אותו עד הסוף והוא לא נוגע בסודות, בקבצים או במסד הנתונים.</div>
<pre class="code ltr p-3 rounded-3 text-light" style="background:#1e1e2e;white-space:pre-wrap;max-height:60vh;overflow:auto">{{ route.pending_code }}</pre>
<div class="d-flex gap-2">
  <form method="post" action="{{ url_for('approve_route', route_id=route.id) }}">__CSRF__<button class="btn btn-success px-4">אשר ופרוס</button></form>
  <form method="post" action="{{ url_for('reject_route', route_id=route.id) }}">__CSRF__<button class="btn btn-outline-danger px-4">דחה</button></form>
</div>
{% endblock %}"""

LOGS = """{% extends 'base.html' %}
{% block title %}יומנים{% endblock %}
{% block content %}
<a href="{{ url_for('index') }}" class="text-decoration-none">&rarr; חזרה ללוח הבקרה</a>
<h3 class="mt-2 mb-3">יומנים: <span class="url-chip ltr d-inline-block">{{ route.full_path }}</span></h3>
<div class="card p-3">
  {% if logs %}
  <div class="table-responsive"><table class="table table-sm align-middle mb-0">
    <thead><tr><th>זמן (UTC)</th><th>פרטים</th></tr></thead>
    <tbody>
    {% for log in logs %}
      <tr><td class="text-nowrap ltr">{{ log.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</td><td class="text-muted ltr">{{ log.message }}</td></tr>
    {% endfor %}
    </tbody>
  </table></div>
  {% else %}
  <div class="text-center text-muted py-4">עוד לא הגיעו בקשות לשרת הזה.</div>
  {% endif %}
</div>
{% endblock %}"""

TEMPLATES = {
    "base.html": BASE,
    "login.html": LOGIN,
    "error.html": ERROR,
    "dashboard.html": DASHBOARD,
    "review.html": REVIEW,
    "logs.html": LOGS,
}
TEMPLATES = {name: tpl.replace("__CSRF__", CSRF) for name, tpl in TEMPLATES.items()}

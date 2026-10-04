"""תבניות Jinja. כל המשתנים עוברים דרך {{ }} (escape אוטומטי) - אף פעם לא דרך f-string."""

CSRF = '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'

BASE = """<!DOCTYPE html>
<html dir="rtl" lang="he" data-bs-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}SH{% endblock %} · SH</title>
<script>try{document.documentElement.setAttribute('data-bs-theme',localStorage.getItem('sh-theme')||'dark');}catch(e){}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
<style>
:root{--brand:#5b5ff0;--brand-d:#4a4ed6;--bg:#f6f6f8;--panel:#ffffff;--panel-2:#f0f0f4;--border:#e2e3e9;--text:#14151a;--muted:#6b6f7b;--ok:#16a34a;--warn:#d97706;--bad:#dc2626}
[data-bs-theme=dark]{--brand:#7377ff;--brand-d:#8a8dff;--bg:#0c0d10;--panel:#131418;--panel-2:#1b1c22;--border:#272930;--text:#e7e8ec;--muted:#8b8f9b;--ok:#34d399;--warn:#fbbf24;--bad:#f87171}
body{font-family:'Heebo',system-ui,sans-serif;background:var(--bg);color:var(--text);--bs-body-bg:var(--bg);--bs-body-color:var(--text);--bs-border-color:var(--border);--bs-secondary-color:var(--muted);--bs-tertiary-bg:var(--panel-2);--bs-emphasis-color:var(--text)}
.text-muted{color:var(--muted)!important}
a{color:var(--brand)}a:hover{color:var(--brand-d)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;box-shadow:none;color:var(--text)}
.btn{border-radius:8px;font-weight:500;font-size:.9rem}
.btn-primary{--bs-btn-bg:var(--brand);--bs-btn-border-color:var(--brand);--bs-btn-color:#fff;--bs-btn-hover-bg:var(--brand-d);--bs-btn-hover-border-color:var(--brand-d);--bs-btn-hover-color:#fff;--bs-btn-active-bg:var(--brand-d);--bs-btn-active-border-color:var(--brand-d);--bs-btn-disabled-bg:var(--brand);--bs-btn-disabled-border-color:var(--brand)}
.btn-outline-primary{--bs-btn-color:var(--brand);--bs-btn-border-color:var(--border);--bs-btn-hover-bg:var(--panel-2);--bs-btn-hover-color:var(--brand);--bs-btn-hover-border-color:var(--brand);--bs-btn-active-bg:var(--panel-2);--bs-btn-active-color:var(--brand)}
.btn-outline-secondary{--bs-btn-color:var(--text);--bs-btn-border-color:var(--border);--bs-btn-hover-bg:var(--panel-2);--bs-btn-hover-color:var(--text);--bs-btn-hover-border-color:var(--muted);--bs-btn-active-bg:var(--panel-2);--bs-btn-active-color:var(--text)}
.btn-outline-danger{--bs-btn-color:var(--bad);--bs-btn-border-color:var(--border);--bs-btn-hover-bg:var(--bad);--bs-btn-hover-border-color:var(--bad);--bs-btn-hover-color:#fff}
.form-control,.form-select{background-color:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text)}
.form-control:focus,.form-select:focus{background-color:var(--bg);color:var(--text);border-color:var(--brand);box-shadow:0 0 0 3px color-mix(in srgb,var(--brand) 25%,transparent)}
.form-control::placeholder{color:var(--muted);opacity:.7}
.form-text,.form-label{color:var(--muted)}
.form-label{font-size:.85rem;font-weight:500}
.table{--bs-table-bg:transparent;--bs-table-color:var(--text);--bs-table-border-color:var(--border);--bs-table-hover-bg:var(--panel-2)}
.alert{border-radius:10px;border:1px solid var(--border)}
.alert-light{background:var(--panel-2);color:var(--muted);border-color:var(--border)}
.badge.bg-dark{background:var(--panel-2)!important;color:var(--text)!important;border:1px solid var(--border)}
.badge.bg-secondary{background:var(--panel-2)!important;color:var(--muted)!important;border:1px solid var(--border)}
.nav-pills .nav-link{border-radius:8px;color:var(--muted)}
.nav-pills .nav-link.active{background:var(--panel-2);color:var(--text);box-shadow:inset 0 0 0 1px var(--border)}
.dropdown-menu{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:.4rem}
.dropdown-item{border-radius:6px;color:var(--text);font-size:.9rem}.dropdown-item:hover{background:var(--panel-2);color:var(--text)}
.ltr{direction:ltr;text-align:left}
.code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.88rem}
textarea.code{background:var(--bg)}
details>summary{cursor:pointer;color:var(--muted)}
/* סרגל עליון */
.topbar{background:var(--panel);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:20}
.topbar .inner{height:56px}
.brand-mark{width:56px;height:56px;border-radius:14px;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:22px;margin:0 auto 14px}
.brand-sm{width:28px;height:28px;font-size:12px;border-radius:7px;margin:0}
.topnav a{color:var(--muted);text-decoration:none;font-size:.9rem;padding:.35rem .7rem;border-radius:6px}
.topnav a:hover,.topnav a.on{color:var(--text);background:var(--panel-2)}
.avatar{width:30px;height:30px;border-radius:50%;background:var(--panel-2);border:1px solid var(--border);color:var(--text);font-weight:600;font-size:.8rem;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0}
.step-num{width:26px;height:26px;border-radius:50%;background:var(--panel-2);border:1px solid var(--border);color:var(--text);display:inline-flex;align-items:center;justify-content:center;font-weight:600;font-size:.8rem;flex:none}
/* רשימת שרתים בסגנון Render */
.srv-list{border:1px solid var(--border);border-radius:10px;background:var(--panel);overflow:hidden}
.srv{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.9rem 1.1rem;border-bottom:1px solid var(--border);flex-wrap:wrap}
.srv:last-child{border-bottom:0}
.srv:hover{background:var(--panel-2)}
.srv-name{font-weight:600;color:var(--text);text-decoration:none;font-size:1rem}
.srv-name:hover{color:var(--brand)}
.srv-meta{color:var(--muted);font-size:.82rem;display:flex;gap:.9rem;flex-wrap:wrap;align-items:center;margin-top:.25rem}
.srv-meta a{color:var(--muted);text-decoration:none}.srv-meta a:hover{color:var(--brand);text-decoration:underline}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:none}
.dot-ok{background:var(--ok);box-shadow:0 0 0 3px color-mix(in srgb,var(--ok) 22%,transparent)}
.dot-warn{background:var(--warn);box-shadow:0 0 0 3px color-mix(in srgb,var(--warn) 22%,transparent)}
.dot-bad{background:var(--bad);box-shadow:0 0 0 3px color-mix(in srgb,var(--bad) 22%,transparent)}
.chip{display:inline-flex;align-items:center;gap:.3rem;font-size:.72rem;color:var(--muted);background:var(--panel-2);border:1px solid var(--border);border-radius:6px;padding:.08rem .5rem}
.srv-actions{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}
.srv-actions form{margin:0}
.empty{border:1px dashed var(--border);border-radius:10px;padding:2rem;text-align:center;color:var(--muted)}
#deploy,.scroll-target{scroll-margin-top:76px}
.diff{background:#14151c;color:#cdd6f4;white-space:pre-wrap;overflow:auto;max-height:50vh;border:1px solid var(--border)}
.diff span{display:block}
.d-add{background:rgba(46,160,67,.28)}.d-del{background:rgba(248,81,73,.28)}.d-hunk{color:#89b4fa}
.url-chip{background:var(--panel-2);border:1px solid var(--border);border-radius:6px;padding:2px 8px;font-size:.85rem;word-break:break-all;color:var(--text)}
.log-row.s-err td{color:var(--bad)!important}
/* טבלת שרתים בסגנון Render */
.tbl{border:1px solid var(--border);border-radius:10px;background:var(--panel);overflow:hidden}
.srv-row{display:grid;grid-template-columns:minmax(0,2.4fr) minmax(0,1.3fr) minmax(0,1.3fr) minmax(0,1fr) 40px;align-items:center;gap:1rem;padding:.8rem 1.1rem}
.tbl-head{color:var(--muted);font-size:.78rem;font-weight:500;border-bottom:1px solid var(--border);padding-top:.6rem;padding-bottom:.6rem;background:var(--panel)}
.tbl .srv{border-bottom:1px solid var(--border);font-size:.9rem}
.tbl .srv:last-child{border-bottom:0}
.tbl .srv:hover{background:var(--panel-2)}
.svc-ico{width:34px;height:34px;border-radius:8px;background:color-mix(in srgb,var(--brand) 18%,var(--panel-2));border:1px solid var(--border);color:var(--brand);font-weight:700;font-size:.8rem;display:inline-flex;align-items:center;justify-content:center;flex:none}
.svc-ico-lg{width:44px;height:44px;border-radius:10px;font-size:.95rem}
.srv-url{color:var(--muted);font-size:.78rem}
.kebab{background:transparent;border:1px solid transparent;color:var(--muted);border-radius:6px;width:32px;height:32px;font-size:1.2rem;line-height:1}
.kebab:hover,.kebab[aria-expanded=true]{background:var(--panel-2);border-color:var(--border);color:var(--text)}
.crumbs{font-size:.85rem;color:var(--muted)}.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:var(--text)}
/* עמוד שרת: סרגל צד */
.svc-layout{display:grid;grid-template-columns:200px minmax(0,1fr);gap:2rem;border-top:1px solid var(--border);padding-top:1.5rem}
.svc-nav{display:flex;flex-direction:column;gap:2px;position:sticky;top:76px;align-self:start}
.svc-nav-title{font-size:.72rem;color:var(--muted);font-weight:600;padding:.2rem .7rem;margin-bottom:.2rem}
.svc-nav a{color:var(--muted);text-decoration:none;font-size:.9rem;padding:.42rem .7rem;border-radius:6px}
.svc-nav a:hover{background:var(--panel-2);color:var(--text)}
.svc-nav a.on{background:var(--panel-2);color:var(--text);font-weight:600}
@media (max-width:820px){
  .srv-row{grid-template-columns:minmax(0,1fr) auto 40px}.c-runtime,.c-upd,.tbl-head{display:none}
  .svc-layout{grid-template-columns:1fr;gap:1rem}
  .svc-nav{flex-direction:row;overflow-x:auto;position:static;border-bottom:1px solid var(--border);padding-bottom:.5rem}.svc-nav-title{display:none}
}

:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
</style>
</head>
<body>
{% if current_user %}
<header class="topbar mb-4"><div class="container inner d-flex justify-content-between align-items-center" style="max-width:1180px">
  <div class="d-flex align-items-center gap-3">
    <a href="{{ url_for('index') }}" class="d-flex align-items-center gap-2 text-decoration-none fw-bold" style="color:var(--text)">
      <span class="brand-mark brand-sm">SH</span><span class="d-none d-sm-inline">מערכת שרתים</span>
    </a>
    <nav class="topnav d-flex gap-1">
      <a href="{{ url_for('index') }}" class="{% if request.endpoint in ('index','edit_route','view_logs') %}on{% endif %}">שרתים</a>
      <a href="{{ url_for('account') }}" class="{% if request.endpoint == 'account' %}on{% endif %}">הגדרות חשבון</a>
    </nav>
  </div>
  <div class="d-flex align-items-center gap-2">
    <div class="dropdown">
      <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="dropdown" aria-expanded="false">חדש +</button>
      <ul class="dropdown-menu dropdown-menu-end" style="min-width:230px">
        <li><a class="dropdown-item" href="{{ url_for('new_server') }}?mode=paste">שרת מקוד שהודבק</a></li>
        <li><a class="dropdown-item" href="{{ url_for('new_server') }}?mode=repo">ריפו שלם מ-GitHub</a></li>
        <li><a class="dropdown-item" href="{{ url_for('new_server') }}?mode=github">קובץ בודד מ-GitHub</a></li>
      </ul>
    </div>
    <div class="dropdown">
      <button type="button" class="avatar" data-bs-toggle="dropdown" aria-expanded="false" aria-label="תפריט משתמש">{{ current_user.username[:1]|upper }}</button>
      <ul class="dropdown-menu dropdown-menu-end" style="min-width:210px">
        <li class="px-2 py-1"><div class="fw-semibold ltr">{{ current_user.username }}</div><div class="small text-muted">{% if current_user.is_admin %}מנהל{% else %}משתמש{% endif %}</div></li>
        <li><hr class="dropdown-divider" style="border-color:var(--border)"></li>
        <li><a class="dropdown-item" href="{{ url_for('account') }}">הגדרות חשבון</a></li>
        <li><button type="button" class="dropdown-item js-theme">מצב בהיר / כהה</button></li>
        <li><form method="post" action="{{ url_for('logout') }}" class="m-0">__CSRF__<button class="dropdown-item">התנתק</button></form></li>
      </ul>
    </div>
  </div>
</div></header>
{% endif %}
<main class="container pb-5" style="max-width:1180px">
{% with messages = get_flashed_messages(with_categories=true) %}{% for cat, msg in messages %}
<div class="alert alert-{{ cat }} alert-dismissible fade show" role="alert">{{ msg }}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="סגור"></button></div>
{% endfor %}{% endwith %}
{% block content %}{% endblock %}
</main>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
document.querySelectorAll('form[data-confirm]').forEach(function(f){f.addEventListener('submit',function(e){
  if(!confirm(f.dataset.confirm)){e.preventDefault();e.stopImmediatePropagation();}
});});
document.querySelectorAll('.js-theme').forEach(function(b){b.addEventListener('click',function(){
  var r=document.documentElement,n=r.getAttribute('data-bs-theme')==='dark'?'light':'dark';
  r.setAttribute('data-bs-theme',n);try{localStorage.setItem('sh-theme',n);}catch(e){}
});});
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
    <div class="brand-mark" style="background:var(--bad)">!</div>
    <h4 class="mb-2">משהו השתבש</h4>
    <p class="text-muted">{{ message }}</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary mt-2">חזרה לדף הבית</a>
  </div>
</div>
{% endblock %}"""

DASHBOARD = """{% extends 'base.html' %}
{% block title %}שרתים{% endblock %}
{% block content %}
{% if current_user.is_admin %}
<div class="card p-4 mb-4" style="border-inline-start:3px solid var(--warn)">
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

<div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
  <h4 class="mb-0 fw-semibold">שרתים</h4>
  <a href="{{ url_for('new_server') }}" class="btn btn-primary btn-sm">שרת חדש +</a>
</div>
<div class="d-flex gap-2 flex-wrap mb-3">
  <input type="search" id="srvSearch" class="form-control form-control-sm" style="max-width:320px" placeholder="חיפוש שרתים...">
  <select id="srvFilter" class="form-select form-select-sm" style="width:auto">
    <option value="">כל הסטטוסים</option><option value="active">פעיל</option><option value="pending">ממתין לאישור</option><option value="rejected">נדחה</option>
  </select>
  <span class="text-muted small align-self-center ms-auto">{{ routes|length }} שרתים</span>
</div>
{% if routes %}
<div class="tbl mb-5" id="srvList">
  <div class="tbl-head srv-row"><div>שם</div><div>סטטוס</div><div class="c-runtime">סביבת הרצה</div><div class="c-upd">עודכן</div><div></div></div>
  {% for route in routes %}
  {% set url = request.host_url.rstrip('/') ~ route.full_path %}
  {% set is_bundle = (route.live_code or route.pending_code or '').startswith('{"bundle"') %}
  <div class="srv-row srv position-relative" data-name="{{ route.route_name }} {{ route.full_path }}" data-status="{{ route.status }}">
    <div class="d-flex align-items-center gap-3" style="min-width:0">
      <span class="svc-ico">Py</span>
      <div style="min-width:0">
        {% if route.live_code or route.pending_code %}<a href="{{ url_for('edit_route', route_id=route.id) }}" class="srv-name stretched-link">{{ route.route_name }}</a>{% else %}<span class="srv-name">{{ route.route_name }}</span>{% endif %}
        <div class="srv-url ltr text-truncate">{{ route.full_path }}</div>
      </div>
    </div>
    <div class="d-flex align-items-center gap-2 flex-wrap">
      <span class="dot {% if route.status == 'active' %}dot-ok{% elif route.status == 'rejected' %}dot-bad{% else %}dot-warn{% endif %}"></span>
      <span>{% if route.status == 'active' %}פעיל{% elif route.status == 'rejected' %}נדחה{% else %}ממתין לאישור{% endif %}</span>
      {% if route.status == 'active' and route.pending_code %}<span class="chip" style="color:var(--warn)">עדכון ממתין</span>{% endif %}
    </div>
    <div class="c-runtime text-muted">Python 3{% if route.source %} · GitHub{% endif %}{% if is_bundle %} · כמה קבצים{% endif %}</div>
    <div class="c-upd text-muted">{{ route.updated_at|timeago }}</div>
    <div class="dropdown position-relative" style="z-index:3">
      <button type="button" class="kebab" data-bs-toggle="dropdown" aria-expanded="false" aria-label="פעולות">&#8943;</button>
      <ul class="dropdown-menu dropdown-menu-end">
        {% if route.status == 'active' %}
        <li><a class="dropdown-item" href="{{ route.full_path }}" target="_blank" rel="noopener">פתח את השרת</a></li>
        <li><button type="button" class="dropdown-item js-copy" data-url="{{ url }}">העתק כתובת</button></li>
        {% endif %}
        {% if route.live_code or route.pending_code %}<li><a class="dropdown-item" href="{{ url_for('edit_route', route_id=route.id) }}">ערוך קוד</a></li>{% endif %}
        <li><a class="dropdown-item" href="{{ url_for('view_logs', route_id=route.id) }}">יומנים</a></li>
        <li><hr class="dropdown-divider" style="border-color:var(--border)"></li>
        <li><form method="post" action="{{ url_for('delete_route', route_id=route.id) }}" data-confirm="למחוק את השרת {{ route.full_path }} לצמיתות? אי אפשר לשחזר.">__CSRF__<button class="dropdown-item" style="color:var(--bad)">מחק שרת</button></form></li>
      </ul>
    </div>
  </div>
  {% endfor %}
</div>
<div id="srvNone" class="empty mb-5 d-none">לא נמצאו שרתים שמתאימים לחיפוש.</div>
{% else %}
<div class="empty mb-5">
  <div class="fw-semibold mb-1" style="color:var(--text);font-size:1.1rem">עוד אין לך שרתים</div>
  <div class="mb-3">מדביקים קוד או מייבאים ריפו מ-GitHub, ומקבלים כתובת באינטרנט.</div>
  <a href="{{ url_for('new_server') }}" class="btn btn-primary">שרת חדש +</a>
</div>
{% endif %}
{% endblock %}
{% block scripts %}
<script>
(function(){
  function $(id){return document.getElementById(id);}
  document.querySelectorAll('.js-copy').forEach(function(b){b.addEventListener('click',function(){
    navigator.clipboard.writeText(b.dataset.url).then(function(){var t=b.textContent;b.textContent='הועתק';setTimeout(function(){b.textContent=t;},1500);});
  });});
  var q=$('srvSearch'), f=$('srvFilter');
  function filt(){
    if(!q) return;
    var t=q.value.trim().toLowerCase(), st=f.value, shown=0;
    document.querySelectorAll('#srvList .srv').forEach(function(r){
      var ok=(!t||r.dataset.name.toLowerCase().indexOf(t)>-1)&&(!st||r.dataset.status===st);
      r.classList.toggle('d-none',!ok); if(ok) shown++;
    });
    var none=$('srvNone'); if(none) none.classList.toggle('d-none',shown>0);
  }
  if(q){q.addEventListener('input',filt); f.addEventListener('change',filt);}
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
{% if route.source %}<div class="text-muted small mb-2">מקור: GitHub · <span class="ltr d-inline-block">{{ route.source.repo }}{% if route.source.path %}/{{ route.source.path }}{% endif %}</span> · <span class="ltr d-inline-block">{{ (route.source.sha or '')[:7] }}</span></div>{% endif %}
<div class="alert alert-warning">הקוד ירוץ בתוך תהליך השרת. אשר רק אם קראת אותו עד הסוף והוא לא נוגע בסודות, בקבצים או במסד הנתונים.</div>
<h6 class="mt-3">ספריות חיצוניות</h6>
<div class="mb-3">
  {% if libs %}
    {% for lib in libs %}
      {% if lib.status == 'installed' %}
        <span class="badge text-bg-success me-1 ltr">{{ lib.name }} · מותקנת</span>
      {% elif lib.status == 'will_install' %}
        <span class="badge text-bg-warning me-1 ltr">{{ lib.name }} · תותקן באישור ({{ lib.package }})</span>
      {% else %}
        <span class="badge text-bg-danger me-1 ltr">{{ lib.name }} · לא מותרת</span>
      {% endif %}
    {% endfor %}
    {% if libs | selectattr('status', 'equalto', 'blocked') | list %}
      <div class="text-danger small mt-2">יש ספרייה שלא ברשימה המותרת, ולכן האישור חסום. אפשר להוסיף אותה ל-ALLOWED ב-deps.py או במשתנה USER_LIBS_EXTRA ולרענן.</div>
    {% endif %}
  {% else %}
    <span class="text-muted small">הקוד משתמש רק ב-Flask ובספריית הסטנדרט.</span>
  {% endif %}
</div>
{% if bundle %}
<div class="alert alert-info small">שרת מרובה קבצים · {{ bundle.files|length }} קבצים · קובץ ראשי: <code class="ltr">{{ bundle.entry }}</code></div>
{% if bundle.changes is not none %}
<h6>קבצים ששונו לעומת הגרסה הפעילה ({{ bundle.changes|length }})</h6>
{% for c in bundle.changes %}
<details class="mb-2" {% if loop.index <= 3 %}open{% endif %}>
  <summary class="ltr">{{ c.path }} <span class="badge {% if c.status == 'new' %}bg-success{% elif c.status == 'deleted' %}bg-danger{% else %}bg-warning text-dark{% endif %}">{% if c.status == 'new' %}חדש{% elif c.status == 'deleted' %}נמחק{% else %}שונה{% endif %}</span></summary>
  <pre class="code ltr p-3 rounded-3 diff">{% for l in c.diff %}<span class="{% if l.startswith('+') and not l.startswith('+++') %}d-add{% elif l.startswith('-') and not l.startswith('---') %}d-del{% elif l.startswith('@@') %}d-hunk{% endif %}">{{ l }}</span>{% endfor %}</pre>
</details>
{% else %}
<div class="text-muted small mb-2">אין הבדלים לעומת הגרסה הפעילה.</div>
{% endfor %}
{% endif %}
<h6 class="mt-3">כל הקבצים</h6>
{% for path, src in bundle.files.items() %}
<details class="mb-2"><summary class="ltr">{{ path }}</summary><pre class="code ltr p-3 rounded-3 text-light" style="background:#1e1e2e;white-space:pre-wrap;max-height:50vh;overflow:auto">{{ src }}</pre></details>
{% endfor %}
{% else %}
{% if diff_lines %}
<h6>שינויים לעומת הגרסה הפעילה</h6>
<pre class="code ltr p-3 rounded-3 diff">{% for l in diff_lines %}<span class="{% if l.startswith('+') and not l.startswith('+++') %}d-add{% elif l.startswith('-') and not l.startswith('---') %}d-del{% elif l.startswith('@@') %}d-hunk{% endif %}">{{ l }}</span>{% endfor %}</pre>
{% elif route.live_code %}
<div class="text-muted small mb-2">אין הבדלים לעומת הגרסה הפעילה.</div>
{% endif %}
<h6>הקוד המלא</h6>
<pre class="code ltr p-3 rounded-3 text-light" style="background:#1e1e2e;white-space:pre-wrap;max-height:60vh;overflow:auto">{{ route.pending_code }}</pre>
{% endif %}
<div class="d-flex gap-2">
  <form method="post" action="{{ url_for('approve_route', route_id=route.id) }}">__CSRF__<button class="btn btn-success px-4"{% if libs | selectattr('status', 'equalto', 'blocked') | list %} disabled{% endif %}>אשר ופרוס</button></form>
  <form method="post" action="{{ url_for('reject_route', route_id=route.id) }}">__CSRF__<button class="btn btn-outline-danger px-4">דחה</button></form>
</div>
{% endblock %}"""

LOGS = """{% extends 'service.html' %}
{% block title %}יומנים{% endblock %}
{% block service_content %}
<div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
  <h5 class="fw-semibold mb-0">יומנים</h5>
  <div class="d-flex align-items-center gap-3">
    <div class="form-check form-switch m-0"><input class="form-check-input" type="checkbox" id="autoRefresh"><label class="form-check-label small text-muted" for="autoRefresh">רענון אוטומטי (5 שניות)</label></div>
    <a href="{{ url_for('view_logs', route_id=route.id) }}" class="btn btn-sm btn-outline-secondary">רענן</a>
  </div>
</div>
<div class="card p-3">
  {% if logs %}
  <div class="table-responsive"><table class="table table-sm table-hover align-middle mb-0">
    <thead><tr><th>זמן (UTC)</th><th>פרטים</th></tr></thead>
    <tbody>
    {% for log in logs %}
      <tr class="log-row{% if 'Status: 5' in log.message %} s-err{% endif %}"><td class="text-nowrap ltr">{{ log.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</td><td class="text-muted ltr code">{{ log.message }}</td></tr>
    {% endfor %}
    </tbody>
  </table></div>
  <div class="small text-muted pt-2">מוצגות {{ logs|length }} הבקשות האחרונות.</div>
  {% else %}
  <div class="text-center text-muted py-4">עוד לא הגיעו בקשות לשרת הזה.</div>
  {% endif %}
</div>
{% endblock %}
{% block scripts %}
<script>
(function(){
  var cb=document.getElementById('autoRefresh'), t=null;
  try{cb.checked=sessionStorage.getItem('sh-auto-logs')==='1';}catch(e){}
  function apply(){
    try{sessionStorage.setItem('sh-auto-logs',cb.checked?'1':'0');}catch(e){}
    if(t){clearInterval(t);t=null;}
    if(cb.checked){t=setInterval(function(){location.reload();},5000);}
  }
  cb.addEventListener('change',apply); apply();
})();
</script>
{% endblock %}"""

EDIT = """{% extends 'service.html' %}
{% block title %}עריכת שרת{% endblock %}
{% block service_content %}
<h5 class="fw-semibold mb-3">קוד</h5>
{% if route.pending_code and route.live_code %}
<div class="alert alert-warning">יש כבר גרסה חדשה שממתינה לאישור. העריכה ממשיכה ממנה, והגרסה הפעילה ממשיכה לרוץ בינתיים.</div>
{% endif %}
<div class="alert alert-light border small">
  {% if current_user.is_admin %}כמנהל, שמירה מפעילה את השינוי מיד.{% else %}אחרי השמירה השינוי נשלח לאישור מנהל. עד אז הגרסה הפעילה ממשיכה לרוץ בלי שינוי.{% endif %}
  הקוד צריך להגדיר <code>app = Flask(__name__)</code> (או Blueprint בשם <code>bp</code>).
</div>

{% if route.source %}
<div class="card p-3 mb-3">
  <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
    <div>
      <span class="badge bg-dark">GitHub</span>
      <span class="ltr d-inline-block">{{ route.source.repo }}{% if route.source.path %}/{{ route.source.path }}{% endif %}{% if route.source.ref %} @ {{ route.source.ref }}{% endif %}</span>{% if bundle %}<span class="text-muted small">(כמה קבצים)</span>{% endif %}
      <span class="text-muted small ltr d-inline-block">{{ (route.source.sha or '')[:7] }}</span>
    </div>
    {% if bundle or route.source.path.lower().endswith('.py') %}
    <form method="post" action="{{ url_for('sync_route', route_id=route.id) }}" class="m-0">__CSRF__<button class="btn btn-sm btn-outline-primary js-load">משוך גרסה עדכנית מ-GitHub</button></form>
    {% endif %}
  </div>
  <div class="form-text mt-1">גרסה חדשה שנמשכת מהריפו עוברת את אותו אישור מנהל כמו כל שינוי קוד.</div>
</div>
{% endif %}

{% if not bundle %}
<div class="card p-3 mb-3">
  <h6 class="mb-2">עריכה בעזרת AI</h6>
  <form method="post" action="{{ url_for('edit_route_ai', route_id=route.id) }}" id="aiForm">
    __CSRF__
    <input type="hidden" name="code" id="aiCode">
    <div class="row g-2">
      <div class="col-md-8">
        <textarea name="instruction" class="form-control" rows="3" maxlength="2000" required placeholder="תאר מה לשנות, למשל: הוסף בדיקה שהפרמטר id קיים, והחזר שגיאה 400 אם לא">{{ instruction|default('') }}</textarea>
      </div>
      <div class="col-md-4 d-flex flex-column gap-2">
        <select name="provider" class="form-select">
          {% for key, label in providers.items() %}<option value="{{ key }}">{{ label }}{% if key in saved_providers %} ✓{% else %} (אין מפתח){% endif %}</option>{% endfor %}
        </select>
        <button type="submit" class="btn btn-outline-primary js-load">הצע שינוי</button>
      </div>
    </div>
    <div class="form-text mt-2">ה-AI מקבל את הקוד שנמצא כרגע בעורך, ומחזיר גרסה מוצעת. שום דבר לא נשמר עד שתלחץ "שמור שינויים". הפעולה יכולה לקחת כדקה.</div>
  </form>
</div>

{% if ai_diff is defined and ai_diff is not none %}
<div class="alert alert-info d-flex justify-content-between align-items-center flex-wrap gap-2">
  <span>{% if ai_diff %}ההצעה של ה-AI הוכנסה לעורך שלמטה ועדיין לא נשמרה. כך הקוד השתנה:{% else %}ה-AI לא ביצע שינוי בקוד.{% endif %}</span>
  {% if ai_diff %}<button type="button" class="btn btn-sm btn-outline-secondary" id="undoAi">החזר למה שהיה לפני ההצעה</button>{% endif %}
</div>
{% if ai_diff %}
<pre class="code ltr p-3 rounded-3 diff mb-3">{% for l in ai_diff %}<span class="{% if l.startswith('+') and not l.startswith('+++') %}d-add{% elif l.startswith('-') and not l.startswith('---') %}d-del{% elif l.startswith('@@') %}d-hunk{% endif %}">{{ l }}</span>{% endfor %}</pre>
<textarea id="origCode" hidden>
{{ original_code }}</textarea>
{% endif %}
{% endif %}

<form method="post" action="{{ url_for('edit_route', route_id=route.id) }}" id="editForm">
  __CSRF__
  <textarea name="code" id="code" class="form-control ltr code mb-1" rows="24" spellcheck="false" required data-max="{{ max_code_chars }}" data-dirty="{{ '1' if ai_diff else '' }}">
{{ code }}</textarea>
  <div id="codeCount" class="form-text text-end mb-3"></div>
  <div class="d-flex gap-2 align-items-center">
    <button type="submit" class="btn btn-primary px-4 js-load">שמור שינויים</button>
    <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">ביטול</a>
    <span class="text-muted small">Ctrl+S לשמירה · Tab להזחה</span>
  </div>
</form>
{% else %}
<div class="alert alert-info small">שרת מרובה קבצים: {{ bundle.files|length }} קבצים, קובץ ראשי <code class="ltr">{{ bundle.entry }}</code>. אפשר לערוך את תוכן הקבצים. כדי להוסיף או למחוק קבצים, משוך מחדש מ-GitHub. עריכה בעזרת AI זמינה רק לשרתים של קובץ בודד.</div>
<form method="post" action="{{ url_for('edit_route', route_id=route.id) }}" id="bundleForm">
  __CSRF__
  <input type="hidden" name="bundle_json" id="bundleJson">
  <div class="d-flex gap-2 align-items-center mb-2 flex-wrap">
    <select id="fileSel" class="form-select ltr" style="max-width:420px"></select>
    <span class="text-muted small" id="fileInfo"></span>
  </div>
  <textarea id="bcode" class="form-control ltr code mb-1" rows="24" spellcheck="false"></textarea>
  <div class="form-text text-end mb-3" id="bcount"></div>
  <div class="d-flex gap-2 align-items-center">
    <button type="submit" class="btn btn-primary px-4 js-load">שמור שינויים</button>
    <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">ביטול</a>
    <span class="text-muted small">Ctrl+S לשמירה · Tab להזחה</span>
  </div>
</form>
<script type="application/json" id="bundleData">{{ bundle|tojson }}</script>
{% endif %}

<div class="card p-3 mt-4 scroll-target" id="env">
  <h6 class="mb-1">משתני סביבה</h6>
  <div class="text-muted small mb-3">
    לסודות כמו מפתחות API. נשמרים מוצפנים ולא מוצגים אחרי השמירה. בקוד קוראים אותם כך:
    <code class="ltr d-inline-block">env.get("NAME")</code> (המשתנה <code>env</code> קיים אוטומטית, אין צורך לייבא).
    שינוי משתנה נכנס לתוקף מיד, בלי אישור מנהל.
  </div>
  {% for n in env_names %}
  <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
    <span class="ltr"><code>{{ n }}</code> <span class="text-muted">= ••••••••</span></span>
    <form method="post" action="{{ url_for('delete_env_var', route_id=route.id) }}" class="m-0" data-confirm="למחוק את המשתנה {{ n }}?">
      __CSRF__<input type="hidden" name="name" value="{{ n }}"><button class="btn btn-sm btn-outline-danger">מחק</button>
    </form>
  </div>
  {% else %}
  <div class="text-muted small mb-2">עוד לא הוגדרו משתנים.</div>
  {% endfor %}
  <form method="post" action="{{ url_for('set_env_var', route_id=route.id) }}" class="row g-2 mt-2">
    __CSRF__
    <div class="col-md-4"><input name="name" class="form-control ltr" placeholder="NAME" required pattern="[A-Za-z_][A-Za-z0-9_]{0,63}" autocomplete="off" autocapitalize="characters"></div>
    <div class="col-md-6"><input type="password" name="value" class="form-control ltr" placeholder="ערך" required autocomplete="off"></div>
    <div class="col-md-2"><button class="btn btn-outline-primary w-100 js-load">שמור</button></div>
  </form>
  <div class="form-text">שמירה בשם קיים מחליפה את הערך.</div>
</div>
{% endblock %}
{% block scripts %}
{% if not bundle %}
<script>
(function(){
  var t=document.getElementById('code'), c=document.getElementById('codeCount'), f=document.getElementById('editForm'), ai=document.getElementById('aiForm');
  var max=parseInt(t.dataset.max,10), dirty=t.dataset.dirty==='1';
  function count(){var n=t.value.length;c.textContent=n.toLocaleString('en-US')+' / '+max.toLocaleString('en-US')+' תווים';c.classList.toggle('text-danger',n>max);}
  t.addEventListener('input',function(){dirty=true;count();}); count();
  t.addEventListener('keydown',function(e){
    if(e.key==='Tab'&&!e.shiftKey){e.preventDefault();var s=t.selectionStart,en=t.selectionEnd;t.value=t.value.substring(0,s)+'    '+t.value.substring(en);t.selectionStart=t.selectionEnd=s+4;dirty=true;count();}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();f.requestSubmit();}
  });
  f.addEventListener('submit',function(){dirty=false;});
  ai.addEventListener('submit',function(){document.getElementById('aiCode').value=t.value;dirty=false;});
  var u=document.getElementById('undoAi');
  if(u){u.addEventListener('click',function(){t.value=document.getElementById('origCode').value;count();});}
  window.addEventListener('beforeunload',function(e){if(dirty){e.preventDefault();e.returnValue='';}});
})();
</script>
{% else %}
<script>
(function(){
  var data=JSON.parse(document.getElementById('bundleData').textContent), files=data.files, entry=data.entry;
  var sel=document.getElementById('fileSel'), ta=document.getElementById('bcode'), cnt=document.getElementById('bcount');
  var info=document.getElementById('fileInfo'), form=document.getElementById('bundleForm');
  var cur=null, dirty=false, names=Object.keys(files).sort();
  names.forEach(function(p){var o=document.createElement('option');o.value=p;o.textContent=(p===entry?'★ ':'')+p;sel.appendChild(o);});
  function count(){cnt.textContent=ta.value.length.toLocaleString('en-US')+' תווים בקובץ';}
  function save(){if(cur!==null){files[cur]=ta.value;}}
  function show(p){cur=p;sel.value=p;ta.value=files[p];info.textContent=p===entry?'קובץ ראשי':'';count();}
  sel.addEventListener('change',function(){save();show(sel.value);});
  ta.addEventListener('input',function(){dirty=true;count();});
  ta.addEventListener('keydown',function(e){
    if(e.key==='Tab'&&!e.shiftKey){e.preventDefault();var s=ta.selectionStart,en=ta.selectionEnd;ta.value=ta.value.substring(0,s)+'    '+ta.value.substring(en);ta.selectionStart=ta.selectionEnd=s+4;dirty=true;count();}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();form.requestSubmit();}
  });
  form.addEventListener('submit',function(){save();document.getElementById('bundleJson').value=JSON.stringify(files);dirty=false;});
  window.addEventListener('beforeunload',function(e){if(dirty){e.preventDefault();e.returnValue='';}});
  show(files[entry]!==undefined?entry:names[0]);
})();
</script>
{% endif %}
{% endblock %}"""

NEW = """{% extends 'base.html' %}
{% block title %}שרת חדש{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width:780px">
  <div class="crumbs mb-2"><a href="{{ url_for('index') }}">שרתים</a> <span>/</span> <span>שרת חדש</span></div>
  <h4 class="fw-semibold mb-1">שרת חדש</h4>
  <div class="text-muted mb-4">מדביקים קוד Python או מייבאים מ-GitHub. מנהל מאשר, והשרת עולה בכתובת משלו.</div>
<div class="card p-4">
      <h5 class="mb-3">שרת חדש</h5>
      <form method="post" action="{{ url_for('deploy_server') }}">
        __CSRF__
        <div class="btn-group w-100 mb-3" role="group">
          <input type="radio" class="btn-check" name="source_mode" id="mode_paste" value="paste" checked>
          <label class="btn btn-outline-primary" for="mode_paste">הדבקת קוד</label>
          <input type="radio" class="btn-check" name="source_mode" id="mode_github" value="github">
          <label class="btn btn-outline-primary" for="mode_github">קובץ מ-GitHub</label>
          <input type="radio" class="btn-check" name="source_mode" id="mode_repo" value="repo">
          <label class="btn btn-outline-primary" for="mode_repo">ריפו שלם מ-GitHub</label>
        </div>

        <div class="row g-3 mb-3">
          <div class="col-sm-6">
            <label class="form-label">שם הנתיב</label>
            <input type="text" name="route_name" class="form-control ltr" placeholder="hello" required data-lower pattern="[a-z0-9][a-z0-9_]{0,39}" title="אותיות אנגליות קטנות, ספרות או _ (עד 40 תווים)" autocapitalize="none">
            <div class="form-text">הכתובת: <span class="ltr d-inline-block">/{{ current_user.username }}/<b id="rnPreview">...</b></span></div>
          </div>
          <div class="col-sm-6 paste-only">
            <label class="form-label">שפת הקוד שהדבקת</label>
            <input type="text" name="source_lang" id="lang" list="langs" class="form-control ltr" value="Python" required maxlength="30">
            <datalist id="langs"><option value="Python"><option value="PHP"><option value="JavaScript"><option value="Node.js"><option value="Java"><option value="C#"><option value="Go"><option value="Ruby"></datalist>
          </div>
        </div>

        <div class="gh-any d-none">
          <label class="form-label">כתובת הריפו או הקובץ ב-GitHub</label>
          <input type="text" name="github_url" id="github_url" class="form-control ltr mb-1" placeholder="https://github.com/user/repo">
          <div class="form-text mb-3 gh-file-only">אפשר להדביק קישור ישיר לקובץ (…/blob/main/app.py), או רק את הריפו ולמלא נתיב.</div>
          <div class="form-text mb-3 repo-only">אפשר להדביק גם קישור לתיקייה בתוך הריפו (…/tree/main/server).</div>
          <div class="row g-3 mb-3">
            <div class="col-sm-4 gh-file-only"><label class="form-label">נתיב הקובץ (אם לא בקישור)</label><input type="text" name="github_path" class="form-control ltr" placeholder="app.py"></div>
            <div class="col-sm-4 repo-only"><label class="form-label">תיקייה בריפו (אופציונלי)</label><input type="text" name="github_subdir" class="form-control ltr" placeholder="server"></div>
            <div class="col-sm-4 repo-only"><label class="form-label">קובץ ראשי (אופציונלי)</label><input type="text" name="github_entry" class="form-control ltr" placeholder="app.py"></div>
            <div class="col-sm-4"><label class="form-label">ענף (אופציונלי)</label><input type="text" name="github_ref" class="form-control ltr" placeholder="main"></div>
          </div>
          <div class="form-text mb-3">
            {% if 'github' in saved_providers %}GitHub מחובר, ואפשר לייבא גם מריפו פרטי.{% else %}ריפו ציבורי לא דורש חיבור. לריפו פרטי חבר טוקן בכרטיס "חיבור GitHub".{% endif %}
            <span class="gh-file-only">מיובא קובץ אחד. קובץ py נשלח ישירות, וסוגי קבצים אחרים מתורגמים ב-AI.</span>
            <span class="repo-only">הריפו כולו (קבצי טקסט, עד 100 קבצים ו-1.5MB) נשמר כשרת אחד. בלי AI.</span>
          </div>
        </div>

        <div id="pyBox" class="form-check mb-3 d-none">
          <input class="form-check-input" type="checkbox" name="force_ai" value="1" id="force_ai">
          <label class="form-check-label" for="force_ai">לתרגם גם את קוד ה-Python דרך AI (לסקריפט שאינו אפליקציית Flask)</label>
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

        <div class="paste-only">
          <label class="form-label">הקוד</label>
          <textarea name="code" id="code" class="form-control ltr code" rows="10" required placeholder="הדבק כאן את הקוד..." data-max-direct="{{ max_code_chars }}" data-max-ai="{{ max_ai_chars }}"></textarea>
          <div id="codeCount" class="form-text mb-3 text-end"></div>
        </div>
        <button type="submit" class="btn btn-primary px-4 js-load">שלח לפריסה</button>
      </form>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
(function(){
  var PY=['python','py','python3','flask'];
  function $(id){return document.getElementById(id);}
  var lang=$('lang'), aiBox=$('aiBox'), pyBox=$('pyBox'), force=$('force_ai'), hint=$('modeHint');
  var code=$('code'), cnt=$('codeCount'), ghUrl=$('github_url');
  function mode(){return document.querySelector('input[name=source_mode]:checked').value;}
  function isPy(){return PY.indexOf(lang.value.trim().toLowerCase())>-1;}
  function show(sel,on){document.querySelectorAll(sel).forEach(function(e){e.classList.toggle('d-none',!on);});}
  function upd(){
    var m=mode(), gh=m!=='paste', repo=m==='repo', file=m==='github';
    show('.paste-only',!gh); show('.gh-any',gh); show('.gh-file-only',file); show('.repo-only',repo);
    code.required=!gh; lang.required=!gh; ghUrl.required=gh;
    pyBox.classList.toggle('d-none',gh||!isPy());
    var useAi=file||(!gh&&(!isPy()||force.checked));
    aiBox.classList.toggle('d-none',!useAi);
    hint.textContent=repo
      ? 'הריפו (או התיקייה) מורד כ-ZIP. הקובץ הראשי חייב להגדיר app (Flask) או bp (Blueprint), והקבצים יכולים לייבא זה את זה, להשתמש ב-templates וב-static. ספריות חיצוניות מותקנות אוטומטית רק אם הן ברשימת ההיתר.'
      : file
      ? 'הקובץ נמשך מ-GitHub. קובץ py נשלח ישירות לבדיקה, בלי AI. סוגי קבצים אחרים יתורגמו ב-AI של הספק שבחרת (נדרש מפתח שמור).'
      : (useAi ? 'הקוד יתורגם ל-Flask על ידי ספק ה-AI שבחרת (נדרש מפתח API שמור).'
               : 'קוד Python נשלח ישירות לבדיקה, בלי AI. אפשר להדביק אפליקציית Flask רגילה (app = Flask(__name__)) בלי שינוי.');
    var max=parseInt(useAi?code.dataset.maxAi:code.dataset.maxDirect,10), n=code.value.length;
    cnt.textContent=n.toLocaleString('en-US')+' / '+max.toLocaleString('en-US')+' תווים'+(useAi?' (תרגום ב-AI)':' (Python ישיר)');
    cnt.classList.toggle('text-danger',n>max);
  }
  document.querySelectorAll('input[name=source_mode]').forEach(function(r){r.addEventListener('change',upd);});
  var qm=new URLSearchParams(location.search).get('mode'); if(qm){var qr=document.getElementById('mode_'+qm); if(qr){qr.checked=true;}}
  lang.addEventListener('input',upd); force.addEventListener('change',upd); code.addEventListener('input',upd); upd();
  var rn=document.querySelector('[name=route_name]'), pv=$('rnPreview');
  rn.addEventListener('input',function(){pv.textContent=rn.value||'...';});
  document.querySelectorAll('[data-lower]').forEach(function(i){i.addEventListener('input',function(){i.value=i.value.toLowerCase();});});
})();
</script>
{% endblock %}"""

ACCOUNT = """{% extends 'base.html' %}
{% block title %}הגדרות חשבון{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width:780px">
  <div class="crumbs mb-2"><a href="{{ url_for('index') }}">שרתים</a> <span>/</span> <span>הגדרות חשבון</span></div>
  <h4 class="fw-semibold mb-4">הגדרות חשבון</h4>
  <div class="card p-4">
      <h5 class="mb-1">חיבור GitHub</h5>
      <div class="text-muted small mb-3">לייבוא קוד מריפו פרטי. ריפו ציבורי לא דורש חיבור.</div>
      {% if 'github' in saved_providers %}
      <div class="d-flex justify-content-between align-items-center">
        <span class="badge bg-success">מחובר</span>
        <form method="post" action="{{ url_for('update_github') }}" class="m-0" data-confirm="לנתק את החיבור ל-GitHub?">
          __CSRF__<button name="action" value="delete" class="btn btn-sm btn-outline-danger">נתק</button>
        </form>
      </div>
      {% else %}
      <form method="post" action="{{ url_for('update_github') }}">
        __CSRF__
        <input type="password" name="token" class="form-control ltr mb-2" placeholder="github_pat_..." autocomplete="off" required>
        <button name="action" value="save" class="btn btn-outline-primary w-100">חבר GitHub</button>
      </form>
      <details class="mt-3 small text-muted">
        <summary>איך יוצרים טוקן קריאה בלבד?</summary>
        <ol class="ps-3 mb-0 mt-2">
          <li>ב-GitHub: Settings, Developer settings, Personal access tokens, Fine-grained tokens.</li>
          <li>Generate new token. ב-Repository access בחר רק את הריפו שצריך.</li>
          <li>ב-Repository permissions הגדר Contents: Read-only.</li>
          <li>העתק את הטוקן והדבק כאן. הוא נשמר מוצפן ומשמש לקריאה בלבד.</li>
        </ol>
      </details>
      {% endif %}
    </div>
  <div class="mb-4"></div>
  <div class="card p-4 mb-4">
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
{% endblock %}"""

SERVICE = """{% extends 'base.html' %}
{% block content %}
<div class="crumbs mb-2"><a href="{{ url_for('index') }}">שרתים</a> <span>/</span> <span class="ltr d-inline-block">{{ route.route_name }}</span></div>
<div class="d-flex justify-content-between align-items-start flex-wrap gap-3 mb-3">
  <div class="d-flex align-items-center gap-3" style="min-width:0">
    <span class="svc-ico svc-ico-lg">Py</span>
    <div style="min-width:0">
      <h4 class="mb-1 fw-semibold ltr">{{ route.route_name }}</h4>
      <div class="d-flex gap-2 align-items-center flex-wrap small">
        <span class="chip">Web Service</span><span class="chip">Python 3</span>
        <span class="d-inline-flex align-items-center gap-1">
          <span class="dot {% if route.status == 'active' %}dot-ok{% elif route.status == 'rejected' %}dot-bad{% else %}dot-warn{% endif %}"></span>
          {% if route.status == 'active' %}פעיל{% elif route.status == 'rejected' %}נדחה{% else %}ממתין לאישור{% endif %}
        </span>
        {% if route.status == 'active' %}<a href="{{ route.full_path }}" target="_blank" rel="noopener" class="ltr text-muted text-decoration-none">{{ request.host_url.rstrip('/') }}{{ route.full_path }}</a>{% else %}<span class="ltr text-muted">{{ route.full_path }}</span>{% endif %}
      </div>
    </div>
  </div>
  {% if route.status == 'active' %}<a href="{{ route.full_path }}" target="_blank" rel="noopener" class="btn btn-outline-secondary btn-sm">פתח את השרת</a>{% endif %}
</div>
<div class="svc-layout">
  <nav class="svc-nav">
    <div class="svc-nav-title">ניהול</div>
    <a href="{{ url_for('edit_route', route_id=route.id) }}" class="{% if request.endpoint == 'edit_route' %}on{% endif %}">קוד</a>
    <a href="{{ url_for('edit_route', route_id=route.id) }}#env">משתני סביבה</a>
    <a href="{{ url_for('view_logs', route_id=route.id) }}" class="{% if request.endpoint == 'view_logs' %}on{% endif %}">יומנים</a>
  </nav>
  <section class="svc-main">{% block service_content %}{% endblock %}</section>
</div>
{% endblock %}"""

TEMPLATES = {
    "base.html": BASE,
    "edit.html": EDIT,
    "login.html": LOGIN,
    "error.html": ERROR,
    "dashboard.html": DASHBOARD,
    "new.html": NEW,
    "account.html": ACCOUNT,
    "service.html": SERVICE,
    "review.html": REVIEW,
    "logs.html": LOGS,
}
TEMPLATES = {name: tpl.replace("__CSRF__", CSRF) for name, tpl in TEMPLATES.items()}

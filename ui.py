"""תבניות Jinja. כל המשתנים עוברים דרך {{ }} (עם escape אוטומטי) - אף פעם לא דרך f-string."""

CSRF = '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'

BASE = """<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}מערכת שרתים{% endblock %}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
  body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
  .card { border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,.05); }
</style>
</head>
<body>
{% if current_user %}
<nav class="navbar navbar-dark bg-dark mb-4">
  <div class="container d-flex justify-content-between">
    <span class="navbar-brand">
      {% if current_user.is_admin %}מערכת שרתים - אזור ניהול{% else %}השרתים של {{ current_user.username }}{% endif %}
    </span>
    <form method="post" action="{{ url_for('logout') }}" class="m-0">
      __CSRF__
      <button class="btn btn-outline-light btn-sm">התנתק</button>
    </form>
  </div>
</nav>
{% endif %}
<div class="container pb-5">
{% block content %}{% endblock %}
</div>
</body>
</html>""".replace("__CSRF__", CSRF)

LOGIN = """{% extends 'base.html' %}
{% block title %}התחברות{% endblock %}
{% block content %}
<div class="d-flex justify-content-center pt-5">
  <div class="card p-5 text-center shadow" style="width: 450px;">
    <h2 class="mb-4">התחברות למערכת</h2>
    <form method="post" action="{{ url_for('login_page') }}">
      __CSRF__
      <input type="text" name="username" class="form-control mb-3" placeholder="שם משתמש (אנגלית קטנה, ספרות, _)" required dir="ltr">
      <input type="password" name="password" class="form-control mb-3" placeholder="סיסמה (לפחות 8 תווים)" required>
      <div class="row px-2">
        <div class="col-6 pe-1"><button type="submit" name="action" value="login" class="btn btn-primary w-100">התחבר</button></div>
        <div class="col-6 ps-1"><button type="submit" name="action" value="register" class="btn btn-outline-primary w-100">הרשמה</button></div>
      </div>
    </form>
    {% if google_enabled %}
    <hr class="my-4">
    <a href="{{ url_for('auth_google') }}" class="btn btn-danger btn-lg w-100">התחבר באמצעות Google</a>
    {% endif %}
  </div>
</div>
{% endblock %}""".replace("__CSRF__", CSRF)

ERROR = """{% extends 'base.html' %}
{% block title %}שגיאה{% endblock %}
{% block content %}
<div class="d-flex justify-content-center pt-5">
  <div class="card p-5 text-center shadow-lg">
    <h1 class="display-4 text-danger">⚠️</h1>
    <h2 class="mb-3">משהו השתבש</h2>
    <p class="text-muted">{{ message }}</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary mt-3">חזור לדף הבית</a>
  </div>
</div>
{% endblock %}"""

DASHBOARD = """{% extends 'base.html' %}
{% block title %}לוח בקרה{% endblock %}
{% block content %}

{% if current_user.is_admin %}
<div class="row mb-2">
  <div class="col-md-6"><div class="card p-3 mb-3"><h5>משתמשים רשומים ({{ users_count }})</h5></div></div>
  <div class="col-md-6"><div class="card p-3 mb-3"><h5>שרתים פעילים ({{ active_count }})</h5></div></div>
</div>
<div class="card p-4 mb-4">
  <h5 class="mb-3">ממתינים לאישור ({{ pending|length }})</h5>
  <table class="table table-hover mb-0">
    <tbody>
      {% for r in pending %}
      <tr>
        <td dir="ltr">{{ r.full_path }}</td>
        <td>{{ r.source_lang }}</td>
        <td class="text-end"><a href="{{ url_for('review_route', route_id=r.id) }}" class="btn btn-sm btn-warning">בדוק ואשר</a></td>
      </tr>
      {% else %}
      <tr><td class="text-center text-muted">אין בקשות ממתינות.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}

<div class="row">
  <div class="col-md-4">
    <div class="card p-4 mb-4">
      <h5 class="mb-3">מפתחות API</h5>
      {% for key, label in providers.items() %}
      <div class="d-flex justify-content-between align-items-center mb-2">
        <span>{{ label }}</span>
        {% if key in saved_providers %}
        <form method="post" action="{{ url_for('update_key') }}" class="m-0">
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
      <hr>
      <form method="post" action="{{ url_for('update_key') }}">
        __CSRF__
        <select name="provider" class="form-select mb-2">
          {% for key, label in providers.items() %}<option value="{{ key }}">{{ label }}</option>{% endfor %}
        </select>
        <input type="password" name="api_key" class="form-control mb-2" placeholder="הדבק מפתח חדש" autocomplete="off" dir="ltr">
        <button name="action" value="save" class="btn btn-success w-100">שמור / החלף מפתח</button>
      </form>
    </div>
  </div>

  <div class="col-md-8">
    <div class="card p-4 mb-4">
      <h5 class="mb-3">פריסת שרת חדש / עדכון קיים</h5>
      <form method="post" action="{{ url_for('deploy_server') }}">
        __CSRF__
        <div class="row mb-3">
          <div class="col"><input type="text" name="route_name" class="form-control" placeholder="שם נתיב (למשל: ivr)" required dir="ltr"></div>
          <div class="col"><input type="text" name="source_lang" class="form-control" placeholder="שפת מקור (למשל PHP, Python)" required dir="ltr"></div>
        </div>
        <div class="row mb-3">
          <div class="col">
            <select name="provider" class="form-select">
              {% for key, label in providers.items() %}<option value="{{ key }}">{{ label }}</option>{% endfor %}
            </select>
          </div>
          <div class="col d-flex align-items-center">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" name="force_ai" value="1" id="force_ai">
              <label class="form-check-label" for="force_ai">גם ל-Python: תרגם דרך AI</label>
            </div>
          </div>
        </div>
        <textarea name="code" class="form-control mb-3" rows="8" placeholder="הדבק את הקוד כאן..." required dir="ltr"></textarea>
        <div class="form-text mb-3">קוד Python חייב להגדיר Blueprint בשם bp, עם נתיבים יחסיים (למשל '/'). בלי AI זה נשלח ישר לבדיקה.</div>
        <button type="submit" class="btn btn-primary">שלח לפריסה</button>
      </form>
    </div>
  </div>
</div>

<div class="card p-4">
  <h5 class="mb-3">השרתים שלך</h5>
  <table class="table table-hover">
    <thead class="table-light"><tr><th>נתיב</th><th>כתובת מלאה</th><th>סטטוס</th><th>פעולות</th></tr></thead>
    <tbody>
      {% for route in routes %}
      <tr>
        <td dir="ltr">{{ route.route_name }}</td>
        <td dir="ltr">{{ route.full_path }}</td>
        <td>
          {% if route.status == 'active' %}<span class="badge bg-success">פעיל</span>{% elif route.status == 'rejected' %}<span class="badge bg-danger">נדחה</span>{% else %}<span class="badge bg-warning text-dark">ממתין לאישור</span>{% endif %}
          {% if route.status == 'active' and route.pending_code %}<span class="badge bg-warning text-dark">עדכון ממתין</span>{% endif %}
        </td>
        <td><a href="{{ url_for('view_logs', route_id=route.id) }}" class="btn btn-sm btn-outline-secondary">יומני רישום</a></td>
      </tr>
      {% else %}
      <tr><td colspan="4" class="text-center">אין שרתים עדיין.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}""".replace("__CSRF__", CSRF)

REVIEW = """{% extends 'base.html' %}
{% block title %}בדיקת קוד{% endblock %}
{% block content %}
<h3 class="mb-3">בדיקת קוד: <span dir="ltr">{{ route.full_path }}</span></h3>
<p class="text-muted">שפת מקור: {{ route.source_lang }}. הקוד ירוץ בתוך תהליך השרת, אשר רק אם קראת אותו.</p>
<div class="card p-3 mb-3"><pre dir="ltr" class="mb-0" style="white-space: pre-wrap;">{{ route.pending_code }}</pre></div>
<div class="d-flex gap-2">
  <form method="post" action="{{ url_for('approve_route', route_id=route.id) }}">__CSRF__<button class="btn btn-success">אשר ופרוס</button></form>
  <form method="post" action="{{ url_for('reject_route', route_id=route.id) }}">__CSRF__<button class="btn btn-danger">דחה</button></form>
  <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">חזור</a>
</div>
{% endblock %}""".replace("__CSRF__", CSRF)

LOGS = """{% extends 'base.html' %}
{% block title %}יומני רישום{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2>יומני רישום: <span dir="ltr">{{ route.full_path }}</span></h2>
  <a href="{{ url_for('index') }}" class="btn btn-outline-primary">חזור ללוח הבקרה</a>
</div>
<div class="card p-3">
  <ul class="list-group list-group-flush">
    {% for log in logs %}
    <li class="list-group-item d-flex justify-content-between align-items-center">
      <span dir="ltr"><strong>{{ log.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</strong></span>
      <span class="text-muted">{{ log.message }}</span>
    </li>
    {% else %}
    <li class="list-group-item text-center">לא נמצאו יומנים עבור שרת זה.</li>
    {% endfor %}
  </ul>
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

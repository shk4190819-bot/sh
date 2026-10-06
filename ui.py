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
:root{--brand:#5b5ff0;--brand-d:#4a4ed6;--bg:#f6f6f8;--panel:#ffffff;--panel-2:#f0f0f4;--border:#e2e3e9;--text:#14151a;--muted:#6b6f7b;--ok:#16a34a;--warn:#d97706;--bad:#dc2626;--r-sm:6px;--r:10px;--r-lg:14px;--ok-bg:color-mix(in srgb,var(--ok) 14%,transparent);--warn-bg:color-mix(in srgb,var(--warn) 14%,transparent);--bad-bg:color-mix(in srgb,var(--bad) 14%,transparent)}
[data-bs-theme=dark]{--brand:#7377ff;--brand-d:#8a8dff;--bg:#0c0d10;--panel:#131418;--panel-2:#1b1c22;--border:#272930;--text:#e7e8ec;--muted:#8b8f9b;--ok:#34d399;--warn:#fbbf24;--bad:#f87171}
body{font-family:'Heebo',system-ui,sans-serif;background:var(--bg);color:var(--text);--bs-body-bg:var(--bg);--bs-body-color:var(--text);--bs-border-color:var(--border);--bs-secondary-color:var(--muted);--bs-tertiary-bg:var(--panel-2);--bs-emphasis-color:var(--text)}
.text-muted{color:var(--muted)!important}
a{color:var(--brand)}a:hover{color:var(--brand-d)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;box-shadow:none;color:var(--text)}
.btn{border-radius:8px;font-weight:500;font-size:.9rem}
.btn-primary{--bs-btn-bg:var(--brand);--bs-btn-border-color:var(--brand);--bs-btn-color:#fff;--bs-btn-hover-bg:var(--brand-d);--bs-btn-hover-border-color:var(--brand-d);--bs-btn-hover-color:#fff;--bs-btn-active-bg:var(--brand-d);--bs-btn-active-border-color:var(--brand-d);--bs-btn-disabled-bg:var(--brand);--bs-btn-disabled-border-color:var(--brand)}
.btn-outline-primary{--bs-btn-color:var(--brand);--bs-btn-border-color:var(--border);--bs-btn-hover-bg:var(--panel-2);--bs-btn-hover-color:var(--brand);--bs-btn-hover-border-color:var(--brand);--bs-btn-active-bg:var(--panel-2);--bs-btn-active-color:var(--brand)}
.btn-outline-secondary{--bs-btn-color:var(--text);--bs-btn-border-color:var(--border);--bs-btn-hover-bg:var(--panel-2);--bs-btn-hover-color:var(--text);--bs-btn-hover-border-color:var(--muted);--bs-btn-active-bg:var(--panel-2);--bs-btn-active-color:var(--text)}
.btn-success{--bs-btn-bg:var(--ok);--bs-btn-border-color:var(--ok);--bs-btn-color:#04210f;--bs-btn-hover-bg:color-mix(in srgb,var(--ok) 85%,#000);--bs-btn-hover-border-color:color-mix(in srgb,var(--ok) 85%,#000);--bs-btn-hover-color:#04210f;--bs-btn-active-bg:color-mix(in srgb,var(--ok) 80%,#000);--bs-btn-active-color:#04210f}
.btn-warning{--bs-btn-bg:var(--warn);--bs-btn-border-color:var(--warn);--bs-btn-color:#2a1700;--bs-btn-hover-bg:color-mix(in srgb,var(--warn) 85%,#000);--bs-btn-hover-border-color:color-mix(in srgb,var(--warn) 85%,#000);--bs-btn-hover-color:#2a1700;--bs-btn-active-bg:color-mix(in srgb,var(--warn) 80%,#000);--bs-btn-active-color:#2a1700}
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
.topbar{background:var(--panel);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
.topbar .inner{min-height:56px;display:flex;align-items:center;gap:.5rem 1rem;flex-wrap:wrap}
.topbar .tb-brand{display:flex;align-items:center;gap:.5rem;text-decoration:none;font-weight:700;color:var(--text)}
.topbar .tb-actions{display:flex;align-items:center;gap:.5rem;margin-inline-start:auto}
.topnav{display:flex;gap:.25rem}
.brand-mark{width:56px;height:56px;border-radius:14px;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:22px;margin:0 auto 14px}
.brand-sm{width:28px;height:28px;font-size:12px;border-radius:7px;margin:0}
.topnav a{color:var(--muted);text-decoration:none;font-size:.9rem;padding:.35rem .7rem;border-radius:var(--r-sm);white-space:nowrap}
.topnav a:hover,.topnav a.on{color:var(--text);background:var(--panel-2)}
.avatar{width:32px;height:32px;border-radius:50%;background:var(--panel-2);border:1px solid var(--border);color:var(--text);font-weight:600;font-size:.8rem;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;padding:0}
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
#deploy,.scroll-target{scroll-margin-top:calc(var(--tb-h,56px) + 72px)}
.diff{background:var(--panel-2);color:var(--text);white-space:pre-wrap;overflow:auto;max-height:40vh;border:1px solid var(--border);font-size:.8rem}
.diff span{display:block}
.d-add{background:color-mix(in srgb,var(--ok) 18%,transparent)}.d-del{background:color-mix(in srgb,var(--bad) 18%,transparent)}.d-hunk{color:var(--brand)}
.url-chip{background:var(--panel-2);border:1px solid var(--border);border-radius:6px;padding:2px 8px;font-size:.85rem;word-break:break-all;color:var(--text)}
/* טבלת שרתים בסגנון Render */
.tbl{border:1px solid var(--border);border-radius:var(--r);background:var(--panel)}
.tbl>:first-child{border-radius:var(--r) var(--r) 0 0}.tbl>:last-child{border-radius:0 0 var(--r) var(--r)}
.srv-row{display:grid;grid-template-columns:minmax(0,2.4fr) minmax(0,1.3fr) minmax(0,1.3fr) minmax(0,1fr) 40px;align-items:center;gap:1rem;padding:.8rem 1.1rem}
.tbl-head{color:var(--muted);font-size:.78rem;font-weight:500;border-bottom:1px solid var(--border);padding-top:.6rem;padding-bottom:.6rem;background:var(--panel)}
.tbl .srv{border-bottom:1px solid var(--border);font-size:.9rem}
.tbl .srv:last-child{border-bottom:0}
.tbl .srv:hover{background:var(--panel-2)}
.svc-ico{width:34px;height:34px;border-radius:8px;background:color-mix(in srgb,var(--brand) 18%,var(--panel-2));border:1px solid var(--border);color:var(--brand);font-weight:700;font-size:.8rem;display:inline-flex;align-items:center;justify-content:center;flex:none}
.svc-ico-lg{width:44px;height:44px;border-radius:10px;font-size:.95rem}
.srv-url{color:var(--muted);font-size:.78rem}
.srv.is-open{z-index:5}
.tbl .dropdown-menu{min-width:11rem;box-shadow:0 12px 32px -12px rgba(0,0,0,.45)}
.page-head{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:.75rem;margin-bottom:1rem}
.page-head h1{font-size:1.5rem;font-weight:700;margin:0;line-height:1.2}.page-head .sub{color:var(--muted);font-size:.85rem;margin-top:.2rem}
.toolbar{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-bottom:.75rem}.toolbar .count{margin-inline-start:auto;color:var(--muted);font-size:.82rem}
.st{display:inline-flex;align-items:center;gap:.4rem;font-size:.78rem;font-weight:500;border-radius:999px;padding:.12rem .6rem;border:1px solid transparent;white-space:nowrap}
.st::before{content:'';width:7px;height:7px;border-radius:50%;background:currentColor}
.st-ok{color:var(--ok);background:var(--ok-bg);border-color:color-mix(in srgb,var(--ok) 30%,transparent)}
.st-warn{color:var(--warn);background:var(--warn-bg);border-color:color-mix(in srgb,var(--warn) 30%,transparent)}
.st-bad{color:var(--bad);background:var(--bad-bg);border-color:color-mix(in srgb,var(--bad) 30%,transparent)}
.attn{border:1px solid var(--border);border-inline-start:3px solid var(--warn);border-radius:var(--r);background:var(--panel);margin-bottom:.75rem}
.attn-head{display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;padding:.55rem .9rem;font-size:.88rem;font-weight:600}
.attn-head .more{font-weight:400;font-size:.8rem}
.attn-body{max-height:190px;overflow:auto;border-top:1px solid var(--border)}
.attn-row{display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;padding:.4rem .9rem;font-size:.85rem;border-bottom:1px solid var(--border)}.attn-row:last-child{border-bottom:0}
.attn-row .btn{--bs-btn-padding-y:.1rem;--bs-btn-padding-x:.55rem;--bs-btn-font-size:.78rem}
.empty .em-ico{width:48px;height:48px;border-radius:12px;margin:0 auto 1rem;display:flex;align-items:center;justify-content:center;font-size:1.4rem;color:var(--brand);background:color-mix(in srgb,var(--brand) 14%,var(--panel-2));border:1px solid var(--border)}
.notice{display:flex;gap:.6rem;align-items:flex-start;padding:.5rem .8rem;border-radius:var(--r);border:1px solid var(--border);background:var(--panel-2);color:var(--muted);font-size:.84rem;margin-bottom:.75rem}
.notice-warn{background:var(--warn-bg);border-color:color-mix(in srgb,var(--warn) 35%,transparent);color:var(--text)}
.notice-info{background:color-mix(in srgb,var(--brand) 10%,transparent);border-color:color-mix(in srgb,var(--brand) 30%,transparent);color:var(--text)}
.notice .grow{flex:1;min-width:0}
.sec{display:flex;gap:.75rem;align-items:center;margin:1.4rem 0 .8rem;font-weight:600;font-size:.95rem}.sec:first-child{margin-top:0}
.url-preview{display:flex;align-items:center;gap:.1rem;direction:ltr;margin-top:.5rem;padding:.55rem .8rem;border:1px solid var(--border);border-radius:var(--r);background:var(--panel-2);font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.9rem;word-break:break-all}
.url-preview .up-host{color:var(--muted)}.url-preview .up-name{color:var(--text);font-weight:600}
.url-preview.is-empty .up-name{color:var(--muted);font-weight:400;opacity:.7}
.url-preview.is-bad{border-color:var(--bad);background:var(--bad-bg)}
.form-actions{position:sticky;bottom:0;z-index:10;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:1.5rem -1.5rem -1.5rem;padding:.8rem 1.5rem;border-top:1px solid var(--border);background:var(--panel);border-radius:0 0 var(--r) var(--r)}
.actionbar{position:sticky;top:calc(var(--tb-h,56px) + 8px);z-index:15;display:flex;gap:.5rem .75rem;align-items:center;flex-wrap:wrap;padding:.55rem .75rem;margin-bottom:.75rem;border:1px solid var(--border);border-radius:var(--r);background:var(--panel)}
.actionbar .spacer{flex:1}.actionbar .hint{color:var(--muted);font-size:.78rem}
.save-state{font-size:.78rem}
.editor{min-height:clamp(320px,60vh,720px);line-height:1.55;font-size:.86rem;tab-size:4;resize:vertical}
.panel{border:1px solid var(--border);border-radius:var(--r);background:var(--panel);margin-top:.75rem}
.panel>summary{list-style:none;padding:.65rem .9rem;font-weight:600;font-size:.9rem;color:var(--text);display:flex;align-items:center;gap:.5rem}
.panel>summary::-webkit-details-marker{display:none}
.panel>summary::after{content:'\\25BE';margin-inline-start:auto;color:var(--muted);transition:transform .15s}
.panel[open]>summary::after{transform:rotate(180deg)}
.panel-body{padding:0 .9rem .9rem}
@media (max-width:640px){.actionbar .hint{display:none}.form-actions{margin-inline:-1rem;padding-inline:1rem}}
.st-mute{color:var(--muted);background:var(--panel-2);border-color:var(--border)}
.st-info{color:var(--brand);background:color-mix(in srgb,var(--brand) 12%,transparent);border-color:color-mix(in srgb,var(--brand) 30%,transparent)}
.code-view{direction:ltr;text-align:left;background:var(--panel-2);color:var(--text);white-space:pre-wrap;overflow:auto;max-height:60vh;border:1px solid var(--border);border-radius:var(--r);padding:.8rem 1rem;margin:0;font-size:.82rem}
.log-list{direction:ltr;border:1px solid var(--border);border-radius:var(--r);background:var(--panel);overflow:hidden;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.78rem;line-height:1.5}
.log-day{padding:.2rem .8rem;font-size:.68rem;letter-spacing:.04em;color:var(--muted);background:var(--panel-2);border-bottom:1px solid var(--border)}
.log-row{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:.7rem;padding:.22rem .8rem;border-bottom:1px solid color-mix(in srgb,var(--border) 60%,transparent);border-inline-start:2px solid transparent}
.log-row:last-child{border-bottom:0}
.log-row:hover{background:color-mix(in srgb,var(--text) 4.5%,transparent)}
.log-row.is-5{border-inline-start-color:var(--bad);background:color-mix(in srgb,var(--bad) 7%,transparent)}
.log-row.is-5:hover{background:color-mix(in srgb,var(--bad) 12%,transparent)}
.log-t{color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.log-m{min-width:6ch;color:var(--text);opacity:.8;white-space:nowrap}
.log-s{min-width:3ch;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap}
.lg-2{color:color-mix(in srgb,var(--ok) 78%,#000)}
.lg-3{color:#2563eb}
.lg-4{color:color-mix(in srgb,var(--warn) 80%,#000)}
.lg-5{color:var(--bad)}
.lg-x{color:var(--muted)}
[data-bs-theme=dark] .lg-2{color:var(--ok)}
[data-bs-theme=dark] .lg-3{color:#60a5fa}
[data-bs-theme=dark] .lg-4{color:var(--warn)}
.log-msg{flex:0 1 auto;min-width:0;overflow-wrap:anywhere;color:var(--text)}
.log-row.is-5 .log-msg{color:var(--bad)}
.log-ip{font-size:.7rem;color:var(--muted);white-space:nowrap}
.log-row.is-raw .log-msg{color:var(--muted)}
@media (max-width:640px){
  .log-row{padding:.4rem .7rem;row-gap:.05rem}
  .log-msg,.log-ip{flex:1 1 100%}
  .log-ip{order:5}
}
.acct{padding:1.25rem 1.4rem;margin-bottom:1rem}
.acct-head{display:flex;gap:.75rem;align-items:flex-start;flex-wrap:wrap;margin-bottom:1rem}
.acct-head .grow{flex:1;min-width:0}.acct-head h2{font-size:1.05rem;font-weight:600;margin:0}.acct-head p{margin:.15rem 0 0;color:var(--muted);font-size:.84rem}
.acct-row{display:flex;justify-content:space-between;align-items:center;gap:.6rem;flex-wrap:wrap;padding:.6rem 0;border-bottom:1px solid var(--border)}
.acct-row:last-of-type{border-bottom:0}
.acct-add{margin-top:.9rem;padding-top:1rem;border-top:1px solid var(--border)}
.usr-row[data-status=pending]{border-inline-start:3px solid var(--warn);padding-inline-start:calc(1.1rem - 3px)}
.kebab{background:transparent;border:1px solid transparent;color:var(--muted);border-radius:var(--r-sm);width:36px;height:36px;font-size:1.2rem;line-height:1}
.kebab:hover,.kebab[aria-expanded=true]{background:var(--panel-2);border-color:var(--border);color:var(--text)}
.crumbs{font-size:.85rem;color:var(--muted)}.crumbs a{color:var(--muted);text-decoration:none}.crumbs a:hover{color:var(--text)}
/* עמוד שרת: סרגל צד */
.svc-layout{display:grid;grid-template-columns:200px minmax(0,1fr);gap:2rem;border-top:1px solid var(--border);padding-top:1.5rem}
.svc-nav{display:flex;flex-direction:column;gap:2px;position:sticky;top:calc(var(--tb-h,56px) + 16px);align-self:start}
.svc-nav-title{font-size:.72rem;color:var(--muted);font-weight:600;padding:.2rem .7rem;margin-bottom:.2rem}
.svc-nav a{color:var(--muted);text-decoration:none;font-size:.9rem;padding:.42rem .7rem;border-radius:6px}
.svc-nav a:hover{background:var(--panel-2);color:var(--text)}
.svc-nav a.on{background:var(--panel-2);color:var(--text);font-weight:600}
@media (max-width:640px){
  .topbar .inner{padding-block:.5rem}.topnav{order:3;flex:0 0 100%;overflow-x:auto;margin-inline:-.25rem;padding-bottom:.15rem}
  .toolbar #srvSearch{max-width:none!important;flex:1 1 100%}
}
@media (max-width:820px){
  .srv-row{grid-template-columns:minmax(0,1fr) auto 40px}.c-runtime,.c-upd,.tbl-head{display:none}
  .svc-layout{grid-template-columns:1fr;gap:1rem}
  .svc-nav{flex-direction:row;overflow-x:auto;position:static;border-bottom:1px solid var(--border);padding-bottom:.5rem}.svc-nav-title{display:none}
}

.usr-row{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1.1fr) minmax(0,.7fr) minmax(0,.9fr) auto;align-items:center;gap:1rem;padding:.8rem 1.1rem}
@media (max-width:820px){.usr-row{grid-template-columns:minmax(0,1fr) auto}.usr-row .c-hide{display:none}}
.hero h1{font-size:2.4rem;line-height:1.25}
@media (max-width:576px){.hero h1{font-size:1.8rem}}
.feat{height:100%}
.feat .fi{width:36px;height:36px;border-radius:9px;background:color-mix(in srgb,var(--brand) 18%,var(--panel-2));border:1px solid var(--border);color:var(--brand);display:inline-flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:.7rem}
/* דף פתיחה בסגנון Render */
.lp{position:relative}
.lp-glow{position:absolute;inset:-80px -50vw auto -50vw;height:620px;pointer-events:none;z-index:0;background:radial-gradient(60% 55% at 50% 0%,color-mix(in srgb,var(--brand) 38%,transparent),transparent 70%),radial-gradient(35% 40% at 85% 10%,color-mix(in srgb,#22d3ee 18%,transparent),transparent 70%)}
.lp>*{position:relative;z-index:1}.lp>.lp-glow{position:absolute}
.lp-nav{display:flex;align-items:center;justify-content:space-between;padding:1.1rem 0}
.lp-logo{display:flex;align-items:center;gap:.6rem;font-weight:700;color:var(--text);text-decoration:none;font-size:1.05rem}
.lp-links{display:flex;gap:1.6rem}.lp-links a{color:var(--muted);text-decoration:none;font-size:.92rem}.lp-links a:hover{color:var(--text)}
.lp-hero{text-align:center;padding:4.5rem 0 3rem;max-width:860px;margin:0 auto}
.lp-pill{display:inline-flex;align-items:center;gap:.5rem;font-size:.8rem;color:var(--muted);border:1px solid var(--border);background:color-mix(in srgb,var(--panel) 70%,transparent);border-radius:999px;padding:.25rem .8rem;margin-bottom:1.4rem}
.lp-hero h1{font-size:clamp(2.2rem,5.4vw,3.9rem);font-weight:700;line-height:1.12;letter-spacing:-.02em;margin-bottom:1.2rem}
.lp-grad{background:linear-gradient(90deg,var(--brand),#22d3ee);-webkit-background-clip:text;background-clip:text;color:transparent}
.lp-hero p{font-size:1.15rem;color:var(--muted);max-width:620px;margin:0 auto 2rem}
.lp-btn{padding:.7rem 1.5rem;font-size:.95rem;border-radius:9px}
.lp-demo{max-width:760px;margin:2.5rem auto 0;text-align:left;direction:ltr;border:1px solid var(--border);border-radius:14px;background:var(--panel);box-shadow:0 30px 80px -30px color-mix(in srgb,var(--brand) 45%,transparent);overflow:hidden}
.lp-demo-bar{display:flex;align-items:center;gap:.4rem;padding:.65rem 1rem;border-bottom:1px solid var(--border);background:var(--panel-2)}
.lp-demo-bar i{width:10px;height:10px;border-radius:50%;background:var(--border);display:inline-block}
.lp-demo-bar span{margin-left:.6rem;font-size:.78rem;color:var(--muted)}
.lp-demo-body{padding:1.2rem 1.3rem;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.86rem;line-height:1.9;color:var(--muted)}
.lp-demo-body .ok{color:var(--ok)}.lp-demo-body .hl{color:var(--text)}
.lp-demo-body div{opacity:0;animation:lpIn .45s ease forwards}
.lp-demo-body div:nth-child(1){animation-delay:.2s}.lp-demo-body div:nth-child(2){animation-delay:.8s}.lp-demo-body div:nth-child(3){animation-delay:1.4s}.lp-demo-body div:nth-child(4){animation-delay:2s}.lp-demo-body div:nth-child(5){animation-delay:2.6s}
@keyframes lpIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.lp-demo-body div{animation:none;opacity:1}}
.lp-live{display:inline-flex;align-items:center;gap:.4rem;font-size:.75rem;color:var(--ok);border:1px solid color-mix(in srgb,var(--ok) 40%,transparent);background:color-mix(in srgb,var(--ok) 12%,transparent);border-radius:6px;padding:0 .5rem;margin-left:.5rem}
.lp-sec{padding:4rem 0 1rem}
.lp-sec h2{font-size:clamp(1.6rem,3.2vw,2.2rem);font-weight:700;letter-spacing:-.01em;text-align:center;margin-bottom:.6rem}
.lp-sec .sub{color:var(--muted);text-align:center;max-width:560px;margin:0 auto 2.2rem}
.lp-card{height:100%;padding:1.5rem;border:1px solid var(--border);border-radius:12px;background:var(--panel);transition:border-color .15s,transform .15s}
.lp-card:hover{border-color:color-mix(in srgb,var(--brand) 55%,var(--border));transform:translateY(-2px)}
.lp-card h6{font-weight:600;margin:.9rem 0 .35rem}.lp-card p{color:var(--muted);font-size:.9rem;margin:0}
.lp-ico{width:40px;height:40px;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;color:var(--brand);background:color-mix(in srgb,var(--brand) 16%,var(--panel-2));border:1px solid var(--border)}
.lp-steps{counter-reset:st}.lp-step{position:relative;padding:1.5rem;border:1px solid var(--border);border-radius:12px;background:var(--panel);height:100%}
.lp-step::before{counter-increment:st;content:counter(st);display:inline-flex;width:28px;height:28px;border-radius:50%;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;color:#fff;background:var(--brand);margin-bottom:.9rem}
.lp-step h6{font-weight:600}.lp-step p{color:var(--muted);font-size:.9rem;margin:0}
.lp-cta{margin:4.5rem 0 2rem;padding:3rem 1.5rem;text-align:center;border:1px solid var(--border);border-radius:16px;background:radial-gradient(70% 120% at 50% 0%,color-mix(in srgb,var(--brand) 22%,var(--panel)),var(--panel))}
.lp-cta h2{font-weight:700;margin-bottom:.6rem}.lp-cta p{color:var(--muted);margin-bottom:1.6rem}
.lp-foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.8rem;border-top:1px solid var(--border);padding:1.4rem 0;color:var(--muted);font-size:.82rem}
.lp-foot a{color:var(--muted);text-decoration:none}.lp-foot a:hover{color:var(--text)}
@media (max-width:640px){.lp-links{display:none}.lp-hero{padding-top:2.5rem}}
/* כניסה בסגנון Render */
.auth-card{background:var(--panel);border:1px solid var(--border);border-radius:14px;box-shadow:0 30px 70px -40px color-mix(in srgb,var(--brand) 55%,transparent)}
.btn-oauth{display:flex;align-items:center;justify-content:center;gap:.6rem;width:100%;padding:.62rem;border-radius:8px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);font-weight:500;text-decoration:none;font-size:.92rem}
.btn-oauth:hover{border-color:var(--muted);color:var(--text)}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
</style>
</head>
<body>
{% if current_user and (current_user.is_approved or current_user.is_admin) %}
<header class="topbar mb-4"><div class="container inner" style="max-width:1180px">
  <a href="{{ url_for('index') }}" class="tb-brand"><span class="brand-mark brand-sm">SH</span><span class="d-none d-sm-inline">מערכת שרתים</span></a>
  <nav class="topnav" aria-label="ניווט ראשי">
    <a href="{{ url_for('index') }}" class="{% if request.endpoint in ('index','edit_route','view_logs','new_server','review_route') %}on{% endif %}"{% if request.endpoint in ('index','edit_route','view_logs','new_server','review_route') %} aria-current="page"{% endif %}>שרתים</a>
    {% if current_user.is_admin %}<a href="{{ url_for('admin_users') }}" class="{% if request.endpoint in ('admin_users','admin_user') %}on{% endif %}"{% if request.endpoint in ('admin_users','admin_user') %} aria-current="page"{% endif %}>משתמשים{% if pending_users_count %} <span class="badge bg-warning text-dark">{{ pending_users_count }}</span>{% endif %}</a>{% endif %}
    <a href="{{ url_for('account') }}" class="{% if request.endpoint == 'account' %}on{% endif %}"{% if request.endpoint == 'account' %} aria-current="page"{% endif %}>הגדרות חשבון</a>
  </nav>
  <div class="tb-actions">
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
(function(){var tb=document.querySelector('.topbar');if(!tb)return;function h(){document.documentElement.style.setProperty('--tb-h',tb.offsetHeight+'px');}h();window.addEventListener('resize',h);})();
document.addEventListener('show.bs.dropdown',function(e){var r=e.target.closest('.srv');if(r)r.classList.add('is-open');});
document.addEventListener('hidden.bs.dropdown',function(e){var r=e.target.closest('.srv');if(r)r.classList.remove('is-open');});
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
<div class="auth-card p-4 p-md-5 w-100" style="max-width:440px">
  <div class="brand-mark">SH</div>
  <h3 class="text-center mb-1 fw-bold">{% if tab == 'register' %}יצירת חשבון{% else %}התחברות{% endif %}</h3>
  <p class="text-center text-muted mb-4">מדביקים קוד, ומקבלים שרת באינטרנט.</p>
  {% if google_enabled %}
  <a href="{{ url_for('auth_google') }}" class="btn-oauth mb-3">המשך עם Google</a>
  <div class="d-flex align-items-center gap-2 mb-3 text-muted small"><hr class="flex-grow-1 m-0">או עם שם משתמש<hr class="flex-grow-1 m-0"></div>
  {% endif %}

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
        <div class="form-text mb-3">אנגלית קטנה, ספרות ו-_ בלבד. השם מזהה אותך במערכת ולא מופיע בכתובות השרתים.</div>
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

  <div class="text-center small mt-4"><a href="{{ url_for('index') }}" class="text-muted text-decoration-none">&rarr; על השירות</a></div>
  <div class="text-center small text-muted mt-2">חשבון חדש מתחיל לעבוד אחרי אישור מנהל.</div>
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
<div class="page-head">
  <div>
    <h1>שרתים</h1>
    <div class="sub">{% if current_user.is_admin %}{{ active_count }} שרתים פעילים · {{ users_count }} משתמשים · <a href="{{ url_for('admin_users') }}">ניהול משתמשים</a>{% else %}{{ routes|length }} שרתים{% endif %}</div>
  </div>
  <a href="{{ url_for('new_server') }}" class="btn btn-primary btn-sm">שרת חדש +</a>
</div>
{% if current_user.is_admin %}
{% if pending_users %}
<section class="attn" aria-label="משתמשים שממתינים לאישור">
  <div class="attn-head">
    <span>משתמשים שממתינים לאישור <span class="badge bg-warning text-dark">{{ pending_users|length }}</span></span>
    <a href="{{ url_for('admin_users') }}" class="more">כל המשתמשים</a>
  </div>
  <div class="attn-body">
  {% for u in pending_users %}
  <div class="attn-row">
    <div class="text-truncate" style="min-width:0">
      <a href="{{ url_for('admin_user', user_id=u.id) }}" class="fw-semibold ltr d-inline-block text-decoration-none">{{ u.username }}</a>
      <span class="text-muted small">· {% if u.email %}<span class="ltr d-inline-block">{{ u.email }}</span>{% else %}נרשם עם סיסמה{% endif %} · {{ u.created_at|timeago }}</span>
    </div>
    <div class="d-flex gap-2">
      <form method="post" action="{{ url_for('approve_user', user_id=u.id) }}" class="m-0">__CSRF__<input type="hidden" name="back" value="index"><button class="btn btn-sm btn-success">אשר</button></form>
      <form method="post" action="{{ url_for('delete_user', user_id=u.id) }}" class="m-0" data-confirm="לדחות ולמחוק את המשתמש {{ u.username }}?">__CSRF__<input type="hidden" name="back" value="index"><button class="btn btn-sm btn-outline-danger">דחה</button></form>
    </div>
  </div>
  {% endfor %}
  </div>
</section>
{% endif %}
{% if pending %}
<section class="attn" aria-label="שרתים ישנים שממתינים לאישור">
  <div class="attn-head">
    <span>שרתים ישנים שממתינים לאישור <span class="badge bg-warning text-dark">{{ pending|length }}</span></span>
    <span class="more text-muted">נשלחו לפני המעבר לאישור משתמשים. שרתים חדשים עולים מיד.</span>
  </div>
  <div class="attn-body">
  {% for r in pending %}
  <div class="attn-row">
    <div class="text-truncate" style="min-width:0"><span class="url-chip ltr d-inline-block">{{ r.full_path }}</span> <span class="text-muted small">{{ r.source_lang }}</span></div>
    <a href="{{ url_for('review_route', route_id=r.id) }}" class="btn btn-sm btn-warning">בדוק ואשר</a>
  </div>
  {% endfor %}
  </div>
</section>
{% endif %}
{% endif %}

{% if routes %}
<div class="toolbar">
  <input type="search" id="srvSearch" class="form-control form-control-sm" style="max-width:320px" placeholder="חיפוש שרתים..." aria-label="חיפוש שרתים">
  <select id="srvFilter" class="form-select form-select-sm" style="width:auto" aria-label="סינון לפי סטטוס">
    <option value="">כל הסטטוסים</option><option value="active">פעיל</option><option value="pending">לא פעיל</option><option value="rejected">נדחה</option>
  </select>
  <span class="count" id="srvCount" aria-live="polite">{{ routes|length }} שרתים</span>
</div>
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
      <span class="st {% if route.status == 'active' %}st-ok{% elif route.status == 'rejected' %}st-bad{% else %}st-warn{% endif %}">{% if route.status == 'active' %}פעיל{% elif route.status == 'rejected' %}נדחה{% else %}לא פעיל{% endif %}</span>
      {% if route.status == 'active' and route.pending_code %}<span class="chip" style="color:var(--warn)">העדכון האחרון לא עלה</span>{% endif %}
    </div>
    <div class="c-runtime text-muted">Python 3{% if route.source %} · GitHub{% endif %}{% if is_bundle %} · כמה קבצים{% endif %}</div>
    <div class="c-upd text-muted">{{ route.updated_at|timeago }}</div>
    <div class="dropdown position-relative" style="z-index:3">
      <button type="button" class="kebab" data-bs-toggle="dropdown" aria-expanded="false" aria-label="פעולות עבור {{ route.route_name }}">&#8943;</button>
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
<div id="srvNone" class="empty mb-5 d-none">
  <div class="em-ico" aria-hidden="true">&#8981;</div>
  <div class="fw-semibold mb-1" style="color:var(--text)">לא נמצאו שרתים</div>
  <div class="mb-3">אין שרתים שמתאימים לחיפוש או לסינון.</div>
  <button type="button" class="btn btn-outline-secondary btn-sm" id="srvReset">נקה סינון</button>
</div>
{% else %}
<div class="empty mb-5">
  <div class="em-ico" aria-hidden="true">&#9889;</div>
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
    var l=$('srvList'); if(l) l.classList.toggle('d-none',shown===0);
    var c=$('srvCount'); if(c) c.textContent=shown+' שרתים';
  }
  if(q){q.addEventListener('input',filt); f.addEventListener('change',filt);}
  var rs=$('srvReset'); if(rs) rs.addEventListener('click',function(){q.value='';f.value='';filt();q.focus();});
})();
</script>
{% endblock %}"""

REVIEW = """{% extends 'base.html' %}
{% block title %}בדיקת קוד{% endblock %}
{% block content %}
{% set blocked = libs | selectattr('status', 'equalto', 'blocked') | list %}
<div class="crumbs mb-2"><a href="{{ url_for('index') }}">שרתים</a> <span>/</span> <span>בדיקת קוד</span></div>
<div class="page-head">
  <div>
    <h1>בדיקת קוד <span class="st st-warn align-middle fs-6">ממתין לאישור</span></h1>
    <div class="sub">{{ route.owner.username }} · <span class="url-chip ltr d-inline-block">{{ route.full_path }}</span> · שפת מקור: {{ route.source_lang }}
    {% if route.source %}<br>מקור: GitHub · <span class="ltr d-inline-block">{{ route.source.repo }}{% if route.source.path %}/{{ route.source.path }}{% endif %}</span> · <span class="ltr d-inline-block">{{ (route.source.sha or '')[:7] }}</span>{% endif %}</div>
  </div>
</div>
<div class="actionbar" role="group" aria-label="פעולות בדיקה">
  <form method="post" action="{{ url_for('approve_route', route_id=route.id) }}" class="m-0">__CSRF__<button class="btn btn-success px-4"{% if blocked %} disabled title="יש ספרייה שלא ברשימה המותרת"{% endif %}>אשר ופרוס</button></form>
  <form method="post" action="{{ url_for('reject_route', route_id=route.id) }}" class="m-0">__CSRF__<button class="btn btn-outline-danger px-4">דחה</button></form>
  <span class="spacer"></span>
  {% if blocked %}<span class="st st-bad">האישור חסום</span>{% endif %}
</div>
<div class="notice notice-warn" role="note"><span class="grow">הקוד ירוץ בתוך תהליך השרת. אשר רק אם קראת אותו עד הסוף והוא לא נוגע בסודות, בקבצים או במסד הנתונים.</span></div>

<div class="sec">ספריות חיצוניות</div>
<div class="d-flex gap-2 flex-wrap">
  {% if libs %}
    {% for lib in libs %}
      {% if lib.status == 'installed' %}
        <span class="st st-ok ltr">{{ lib.name }} · מותקנת</span>
      {% elif lib.status == 'will_install' %}
        <span class="st st-warn ltr">{{ lib.name }} · תותקן באישור ({{ lib.package }})</span>
      {% else %}
        <span class="st st-bad ltr">{{ lib.name }} · לא מותרת</span>
      {% endif %}
    {% endfor %}
  {% else %}
    <span class="text-muted small">הקוד משתמש רק ב-Flask ובספריית הסטנדרט.</span>
  {% endif %}
</div>
{% if blocked %}
<div class="text-danger small mt-2">יש ספרייה שלא ברשימה המותרת, ולכן האישור חסום. אפשר להוסיף אותה ל-ALLOWED ב-deps.py או במשתנה USER_LIBS_EXTRA ולרענן.</div>
{% endif %}

{% if bundle %}
<div class="notice notice-info mt-3"><span class="grow">שרת מרובה קבצים · {{ bundle.files|length }} קבצים · קובץ ראשי: <code class="ltr">{{ bundle.entry }}</code></span></div>
{% if bundle.changes is not none %}
<div class="sec">קבצים ששונו לעומת הגרסה הפעילה ({{ bundle.changes|length }})</div>
{% for c in bundle.changes %}
<details class="panel" {% if loop.index <= 3 %}open{% endif %}>
  <summary><span class="ltr">{{ c.path }}</span> <span class="st {% if c.status == 'new' %}st-ok{% elif c.status == 'deleted' %}st-bad{% else %}st-warn{% endif %}">{% if c.status == 'new' %}חדש{% elif c.status == 'deleted' %}נמחק{% else %}שונה{% endif %}</span></summary>
  <div class="panel-body"><pre class="code ltr p-3 rounded-3 diff mb-0">{% for l in c.diff %}<span class="{% if l.startswith('+') and not l.startswith('+++') %}d-add{% elif l.startswith('-') and not l.startswith('---') %}d-del{% elif l.startswith('@@') %}d-hunk{% endif %}">{{ l }}</span>{% endfor %}</pre></div>
</details>
{% else %}
<div class="text-muted small">אין הבדלים לעומת הגרסה הפעילה.</div>
{% endfor %}
{% endif %}
<div class="sec">כל הקבצים</div>
{% for path, src in bundle.files.items() %}
<details class="panel"><summary><span class="ltr">{{ path }}</span></summary><div class="panel-body"><pre class="code code-view">{{ src }}</pre></div></details>
{% endfor %}
{% else %}
{% if diff_lines %}
<div class="sec">שינויים לעומת הגרסה הפעילה</div>
<pre class="code ltr p-3 rounded-3 diff">{% for l in diff_lines %}<span class="{% if l.startswith('+') and not l.startswith('+++') %}d-add{% elif l.startswith('-') and not l.startswith('---') %}d-del{% elif l.startswith('@@') %}d-hunk{% endif %}">{{ l }}</span>{% endfor %}</pre>
{% elif route.live_code %}
<div class="text-muted small mt-3">אין הבדלים לעומת הגרסה הפעילה.</div>
{% endif %}
<details class="panel" {% if not diff_lines %}open{% endif %}>
  <summary>הקוד המלא</summary>
  <div class="panel-body"><pre class="code code-view">{{ route.pending_code }}</pre></div>
</details>
{% endif %}
{% endblock %}"""

LOGS = """{% extends 'service.html' %}
{% block title %}יומנים{% endblock %}
{% block service_content %}
{% set ns = namespace(e4=0, e5=0) %}
{% for log in logs %}{% set p = log.message.split(' | ') %}{% if p|length >= 2 and p[0].startswith('Method: ') and p[1].startswith('Status: ') %}{% set c = p[1][8:]|trim %}{% if c[:1] == '5' %}{% set ns.e5 = ns.e5 + 1 %}{% elif c[:1] == '4' %}{% set ns.e4 = ns.e4 + 1 %}{% endif %}{% endif %}{% endfor %}
<div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
  <div>
    <h5 class="fw-semibold mb-0">יומנים</h5>
    {% if logs %}<div class="small text-muted mt-1 d-flex flex-wrap gap-2 align-items-center"><span>{{ logs|length }} רשומות אחרונות</span>{% if ns.e4 %}<span class="lg-4 fw-semibold" dir="ltr">{{ ns.e4 }} &times; 4xx</span>{% endif %}{% if ns.e5 %}<span class="lg-5 fw-semibold" dir="ltr">{{ ns.e5 }} &times; 5xx</span>{% endif %}</div>{% endif %}
  </div>
  <div class="d-flex align-items-center gap-3">
    <div class="form-check form-switch m-0"><input class="form-check-input" type="checkbox" id="autoRefresh"><label class="form-check-label small text-muted" for="autoRefresh">רענון אוטומטי (5 שניות)</label></div>
    <a href="{{ url_for('view_logs', route_id=route.id) }}" class="btn btn-sm btn-outline-secondary">רענן</a>
  </div>
</div>
{% if logs %}
{% set d = namespace(last='') %}
<div class="log-list" role="log" aria-label="בקשות אחרונות לשרת">
  {% for log in logs %}
  {% set day = log.timestamp.strftime('%Y-%m-%d') %}
  {% if day != d.last %}{% set d.last = day %}<div class="log-day">{{ day }} UTC</div>{% endif %}
  {% set parts = log.message.split(' | ') %}
  {% set parsed = parts|length >= 2 and parts[0].startswith('Method: ') and parts[1].startswith('Status: ') %}
  {% set code = parts[1][8:]|trim if parsed else '' %}
  {% set x = namespace(ip='', extra=[]) %}
  {% if parsed %}{% for part in parts[2:] %}{% if part.startswith('IP: ') and not x.ip %}{% set x.ip = part[4:] %}{% else %}{% set x.extra = x.extra + [part] %}{% endif %}{% endfor %}{% endif %}
  <div class="log-row{% if code[:1] == '5' %} is-5{% endif %}{% if not parsed %} is-raw{% endif %}" title="{{ log.timestamp.strftime('%Y-%m-%d %H:%M:%S') }} UTC"><span class="log-t">{{ log.timestamp.strftime('%H:%M:%S') }}</span>{% if parsed %}<span class="log-m">{{ parts[0][8:] }}</span><span class="log-s {% if code[:1] == '2' %}lg-2{% elif code[:1] == '3' %}lg-3{% elif code[:1] == '4' %}lg-4{% elif code[:1] == '5' %}lg-5{% else %}lg-x{% endif %}">{{ code }}</span>{% if x.extra %}<span class="log-msg">{{ x.extra|join(' · ') }}</span>{% endif %}{% if x.ip %}<span class="log-ip">{{ x.ip }}</span>{% endif %}{% else %}<span class="log-msg">{{ log.message }}</span>{% endif %}</div>
  {% endfor %}
</div>
{% else %}
<div class="empty">
  <div class="em-ico" aria-hidden="true">&#9776;</div>
  <div class="fw-semibold mb-1" style="color:var(--text)">אין עדיין בקשות להצגה</div>
  <div>כשיגיעו בקשות לשרת הזה הן יופיעו כאן, מהחדשה לישנה. אפשר להפעיל רענון אוטומטי ולפתוח את כתובת השרת כדי לראות רשומה ראשונה.</div>
</div>
{% endif %}
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
{% if route.pending_code and route.live_code %}
<div class="notice notice-warn" role="alert"><span class="grow">הגרסה האחרונה שנשמרה לא עלתה (כנראה שגיאת טעינה). העריכה ממשיכה ממנה, והגרסה הקודמת ממשיכה לרוץ בינתיים.</span></div>
{% endif %}

{% if not bundle %}
{% set saved_code = route.pending_code or route.live_code or '' %}
{% set is_dirty = ai_diff or (code|trim != saved_code|trim) %}
<form method="post" action="{{ url_for('edit_route', route_id=route.id) }}" id="editForm">
  __CSRF__
  <div class="actionbar">
    <button type="submit" class="btn btn-primary px-3 js-load" title="שומר ומפעיל את הקוד מיד">שמור ופרוס</button>
    <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">ביטול</a>
    <span class="st save-state {% if is_dirty %}st-warn{% else %}st-ok{% endif %}" id="saveState" aria-live="polite">{% if is_dirty %}שינויים שלא נשמרו{% else %}שמור{% endif %}</span>
    <span class="spacer"></span>
    <span class="hint">Ctrl+S לשמירה · Tab להזחה</span>
  </div>
  {% if ai_diff is defined and ai_diff is not none %}
  <div class="notice notice-info" role="status">
    <span class="grow">{% if ai_diff %}ההצעה של ה-AI הוכנסה לעורך ועדיין לא נשמרה.{% else %}ה-AI לא ביצע שינוי בקוד.{% endif %}
    {% if ai_diff %}<details class="mt-1"><summary class="d-inline">הצג את השינויים</summary>
      <pre class="code ltr p-3 rounded-3 diff mt-2 mb-0">{% for l in ai_diff %}<span class="{% if l.startswith('+') and not l.startswith('+++') %}d-add{% elif l.startswith('-') and not l.startswith('---') %}d-del{% elif l.startswith('@@') %}d-hunk{% endif %}">{{ l }}</span>{% endfor %}</pre>
    </details>{% endif %}</span>
    {% if ai_diff %}<button type="button" class="btn btn-sm btn-outline-secondary" id="undoAi">בטל הצעה</button>{% endif %}
  </div>
  {% if ai_diff %}<textarea id="origCode" hidden>
{{ original_code }}</textarea>{% endif %}
  {% endif %}
  <textarea name="code" id="code" class="form-control ltr code editor mb-1" rows="24" spellcheck="false" required aria-label="קוד השרת" data-max="{{ max_code_chars }}" data-dirty="{{ '1' if is_dirty else '' }}">
{{ code }}</textarea>
  <div id="codeCount" class="form-text text-end mb-2"></div>
  <div class="form-text">הקוד צריך להגדיר <code>app = Flask(__name__)</code> (או Blueprint בשם <code>bp</code>). שמירה מפעילה את השינוי מיד.</div>
</form>

<details class="panel" {% if instruction or (ai_diff is defined and ai_diff is not none) %}open{% endif %}>
  <summary>עריכה בעזרת AI</summary>
  <div class="panel-body">
  <form method="post" action="{{ url_for('edit_route_ai', route_id=route.id) }}" id="aiForm">
    __CSRF__
    <input type="hidden" name="code" id="aiCode">
    <div class="row g-2">
      <div class="col-md-8">
        <textarea name="instruction" class="form-control" rows="3" maxlength="2000" required aria-label="הוראה ל-AI" placeholder="תאר מה לשנות, למשל: הוסף בדיקה שהפרמטר id קיים, והחזר שגיאה 400 אם לא">{{ instruction|default('') }}</textarea>
      </div>
      <div class="col-md-4 d-flex flex-column gap-2">
        <select name="provider" class="form-select" aria-label="ספק AI">
          {% for key, label in providers.items() %}<option value="{{ key }}">{{ label }}{% if key in saved_providers %} ✓{% else %} (אין מפתח){% endif %}</option>{% endfor %}
        </select>
        <button type="submit" class="btn btn-outline-primary js-load">הצע שינוי</button>
      </div>
    </div>
    <div class="form-text mt-2">ה-AI מקבל את הקוד שנמצא כרגע בעורך ומחזיר גרסה מוצעת. שום דבר לא נשמר עד שתלחץ "שמור ופרוס". הפעולה יכולה לקחת כדקה.</div>
  </form>
  </div>
</details>
{% else %}
<form method="post" action="{{ url_for('edit_route', route_id=route.id) }}" id="bundleForm">
  __CSRF__
  <input type="hidden" name="bundle_json" id="bundleJson">
  <div class="actionbar">
    <button type="submit" class="btn btn-primary px-3 js-load" title="שומר ומפעיל את הקוד מיד">שמור ופרוס</button>
    <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">ביטול</a>
    <span class="st save-state st-ok" id="saveState" aria-live="polite">שמור</span>
    <span class="spacer"></span>
    <span class="hint">Ctrl+S לשמירה · Tab להזחה</span>
  </div>
  <div class="d-flex gap-2 align-items-center mb-2 flex-wrap">
    <select id="fileSel" class="form-select ltr" style="max-width:420px" aria-label="קובץ לעריכה"></select>
    <span class="text-muted small" id="fileInfo"></span>
  </div>
  <textarea id="bcode" class="form-control ltr code editor mb-1" rows="24" spellcheck="false" aria-label="תוכן הקובץ"></textarea>
  <div class="form-text text-end mb-2" id="bcount"></div>
  <div class="form-text">שרת מרובה קבצים: {{ bundle.files|length }} קבצים, קובץ ראשי <code class="ltr">{{ bundle.entry }}</code>. כדי להוסיף או למחוק קבצים, משוך מחדש מ-GitHub. עריכה בעזרת AI זמינה רק לשרתים של קובץ בודד.</div>
</form>
<script type="application/json" id="bundleData">{{ bundle|tojson }}</script>
{% endif %}

{% if route.source %}
<div class="panel mt-3 p-3">
  <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
    <div class="small">
      <span class="badge bg-dark">GitHub</span>
      <span class="ltr d-inline-block">{{ route.source.repo }}{% if route.source.path %}/{{ route.source.path }}{% endif %}{% if route.source.ref %} @ {{ route.source.ref }}{% endif %}</span>{% if bundle %} <span class="text-muted">(כמה קבצים)</span>{% endif %}
      <span class="text-muted ltr d-inline-block">{{ (route.source.sha or '')[:7] }}</span>
    </div>
    {% if bundle or route.source.path.lower().endswith('.py') %}
    <form method="post" action="{{ url_for('sync_route', route_id=route.id) }}" class="m-0">__CSRF__<button class="btn btn-sm btn-outline-primary js-load">משוך גרסה עדכנית מ-GitHub</button></form>
    {% endif %}
  </div>
  <div class="form-text mt-1">גרסה חדשה שנמשכת מהריפו מופעלת מיד.</div>
</div>
{% endif %}

<div class="card p-3 mt-3 scroll-target" id="env">
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
    <div class="col-md-4"><input name="name" class="form-control ltr" placeholder="NAME" aria-label="שם המשתנה" required pattern="[A-Za-z_][A-Za-z0-9_]{0,63}" autocomplete="off" autocapitalize="characters"></div>
    <div class="col-md-6"><input type="password" name="value" class="form-control ltr" placeholder="ערך" aria-label="ערך המשתנה" required autocomplete="off"></div>
    <div class="col-md-2"><button class="btn btn-outline-primary w-100 js-load">שמור</button></div>
  </form>
  <div class="form-text">שמירה בשם קיים מחליפה את הערך.</div>
</div>
{% endblock %}
{% block scripts %}
{% if not bundle %}
<script>
(function(){
  var t=document.getElementById('code'), c=document.getElementById('codeCount'), f=document.getElementById('editForm'), ai=document.getElementById('aiForm'), st=document.getElementById('saveState');
  var max=parseInt(t.dataset.max,10), dirty=t.dataset.dirty==='1';
  function state(){st.textContent=dirty?'שינויים שלא נשמרו':'שמור';st.classList.toggle('st-warn',dirty);st.classList.toggle('st-ok',!dirty);}
  function count(){var n=t.value.length;c.textContent=n.toLocaleString('en-US')+' / '+max.toLocaleString('en-US')+' תווים';c.classList.toggle('text-danger',n>max);}
  function touch(){dirty=true;state();count();}
  t.addEventListener('input',touch); count();
  t.addEventListener('keydown',function(e){
    if(e.key==='Tab'&&!e.shiftKey){e.preventDefault();var s=t.selectionStart,en=t.selectionEnd;t.value=t.value.substring(0,s)+'    '+t.value.substring(en);t.selectionStart=t.selectionEnd=s+4;touch();}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();f.requestSubmit();}
  });
  f.addEventListener('submit',function(){dirty=false;});
  ai.addEventListener('submit',function(){document.getElementById('aiCode').value=t.value;dirty=false;});
  var u=document.getElementById('undoAi');
  if(u){u.addEventListener('click',function(){t.value=document.getElementById('origCode').value;dirty=false;state();count();});}
  window.addEventListener('beforeunload',function(e){if(dirty){e.preventDefault();e.returnValue='';}});
})();
</script>
{% else %}
<script>
(function(){
  var data=JSON.parse(document.getElementById('bundleData').textContent), files=data.files, entry=data.entry;
  var sel=document.getElementById('fileSel'), ta=document.getElementById('bcode'), cnt=document.getElementById('bcount'), st=document.getElementById('saveState');
  var info=document.getElementById('fileInfo'), form=document.getElementById('bundleForm');
  var cur=null, dirty=false, names=Object.keys(files).sort();
  names.forEach(function(p){var o=document.createElement('option');o.value=p;o.textContent=(p===entry?'★ ':'')+p;sel.appendChild(o);});
  function state(){st.textContent=dirty?'שינויים שלא נשמרו':'שמור';st.classList.toggle('st-warn',dirty);st.classList.toggle('st-ok',!dirty);}
  function count(){cnt.textContent=ta.value.length.toLocaleString('en-US')+' תווים בקובץ';}
  function save(){if(cur!==null){files[cur]=ta.value;}}
  function show(p){cur=p;sel.value=p;ta.value=files[p];info.textContent=p===entry?'קובץ ראשי':'';count();}
  function touch(){dirty=true;state();count();}
  sel.addEventListener('change',function(){save();show(sel.value);});
  ta.addEventListener('input',touch);
  ta.addEventListener('keydown',function(e){
    if(e.key==='Tab'&&!e.shiftKey){e.preventDefault();var s=ta.selectionStart,en=ta.selectionEnd;ta.value=ta.value.substring(0,s)+'    '+ta.value.substring(en);ta.selectionStart=ta.selectionEnd=s+4;touch();}
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
{% set f = form|default({}) %}
{% set m = f.get('source_mode', 'paste') %}
<div class="mx-auto" style="max-width:780px">
  <div class="crumbs mb-2"><a href="{{ url_for('index') }}">שרתים</a> <span>/</span> <span>שרת חדש</span></div>
  <h1 class="fs-4 fw-semibold mb-1">שרת חדש</h1>
  <div class="text-muted mb-3">מדביקים קוד Python או מייבאים מ-GitHub, והשרת עולה מיד בכתובת משלו.</div>
<div class="card p-4">
      <form method="post" action="{{ url_for('deploy_server') }}">
        __CSRF__
        <div class="sec"><span class="step-num">1</span>מקור הקוד</div>
        <div class="btn-group w-100" role="group" aria-label="מקור הקוד">
          <input type="radio" class="btn-check" name="source_mode" id="mode_paste" value="paste" {% if m == 'paste' %}checked{% endif %}>
          <label class="btn btn-outline-primary" for="mode_paste">הדבקת קוד</label>
          <input type="radio" class="btn-check" name="source_mode" id="mode_github" value="github" {% if m == 'github' %}checked{% endif %}>
          <label class="btn btn-outline-primary" for="mode_github">קובץ מ-GitHub</label>
          <input type="radio" class="btn-check" name="source_mode" id="mode_repo" value="repo" {% if m == 'repo' %}checked{% endif %}>
          <label class="btn btn-outline-primary" for="mode_repo">ריפו שלם מ-GitHub</label>
        </div>

        <div class="sec"><span class="step-num">2</span>כתובת השרת</div>
        <div class="row g-3">
          <div class="col-12">
            <label class="form-label" for="route_name">שם הנתיב</label>
            <input type="text" name="route_name" id="route_name" class="form-control ltr" placeholder="my-api" required data-lower maxlength="40" pattern="[a-z0-9][a-z0-9_\\-]{0,39}" title="אותיות אנגליות קטנות, ספרות, _ או - (עד 40 תווים). השם ייחודי לכל המשתמשים" autocapitalize="none" autocomplete="off" value="{{ f.get('route_name', '') }}">
            <div class="url-preview is-empty" id="urlBox" aria-live="polite"><span class="up-host">{{ request.host_url.rstrip('/') }}/</span><span class="up-name" id="rnPreview">my-api</span></div>
            <div class="form-text" id="rnHint">אותיות אנגליות קטנות, ספרות, _ או -, עד 40 תווים. השם ייחודי לכל המשתמשים.</div>
          </div>
          <div class="col-sm-6 paste-only">
            <label class="form-label" for="lang">שפת הקוד שהדבקת</label>
            <input type="text" name="source_lang" id="lang" list="langs" class="form-control ltr" value="{{ f.get('source_lang', 'Python') }}" required maxlength="30">
            <datalist id="langs"><option value="Python"><option value="PHP"><option value="JavaScript"><option value="Node.js"><option value="Java"><option value="C#"><option value="Go"><option value="Ruby"></datalist>
          </div>
        </div>

        <div class="sec"><span class="step-num">3</span><span class="paste-only">הקוד</span><span class="gh-any d-none">הקוד מ-GitHub</span></div>
        <div class="gh-any d-none">
          <label class="form-label" for="github_url">כתובת הריפו או הקובץ ב-GitHub</label>
          <input type="text" name="github_url" id="github_url" class="form-control ltr mb-1" placeholder="https://github.com/user/repo" value="{{ f.get('github_url', '') }}">
          <div class="form-text mb-3 gh-file-only">אפשר להדביק קישור ישיר לקובץ (…/blob/main/app.py), או רק את הריפו ולמלא נתיב.</div>
          <div class="form-text mb-3 repo-only">אפשר להדביק גם קישור לתיקייה בתוך הריפו (…/tree/main/server).</div>
          <div class="row g-3 mb-3">
            <div class="col-sm-4 gh-file-only"><label class="form-label" for="github_path">נתיב הקובץ (אם לא בקישור)</label><input type="text" name="github_path" id="github_path" class="form-control ltr" placeholder="app.py" value="{{ f.get('github_path', '') }}"></div>
            <div class="col-sm-4 repo-only"><label class="form-label" for="github_subdir">תיקייה בריפו (אופציונלי)</label><input type="text" name="github_subdir" id="github_subdir" class="form-control ltr" placeholder="server" value="{{ f.get('github_subdir', '') }}"></div>
            <div class="col-sm-4 repo-only"><label class="form-label" for="github_entry">קובץ ראשי (אופציונלי)</label><input type="text" name="github_entry" id="github_entry" class="form-control ltr" placeholder="app.py" value="{{ f.get('github_entry', '') }}"></div>
            <div class="col-sm-4"><label class="form-label" for="github_ref">ענף (אופציונלי)</label><input type="text" name="github_ref" id="github_ref" class="form-control ltr" placeholder="main" value="{{ f.get('github_ref', '') }}"></div>
          </div>
          <div class="form-text mb-3">
            {% if 'github' in saved_providers %}GitHub מחובר, ואפשר לייבא גם מריפו פרטי.{% else %}ריפו ציבורי לא דורש חיבור. לריפו פרטי חבר טוקן בכרטיס "חיבור GitHub".{% endif %}
            <span class="gh-file-only">מיובא קובץ אחד. קובץ py נשלח ישירות, וסוגי קבצים אחרים מתורגמים ב-AI.</span>
            <span class="repo-only">הריפו כולו (קבצי טקסט, עד 100 קבצים ו-1.5MB) נשמר כשרת אחד. בלי AI.</span>
          </div>
        </div>

        <div id="pyBox" class="form-check mb-3 d-none">
          <input class="form-check-input" type="checkbox" name="force_ai" value="1" id="force_ai" {% if f.get('force_ai') %}checked{% endif %}>
          <label class="form-check-label" for="force_ai">לתרגם גם את קוד ה-Python דרך AI (לסקריפט שאינו אפליקציית Flask)</label>
        </div>
        <div id="aiBox" class="mb-3 d-none">
          <label class="form-label" for="provider">ספק AI לתרגום</label>
          <select name="provider" id="provider" class="form-select">
            {% for key, label in providers.items() %}
            <option value="{{ key }}" {% if f.get('provider') == key %}selected{% endif %}>{{ label }}{% if key in saved_providers %} ✓{% else %} (אין מפתח){% endif %}</option>
            {% endfor %}
          </select>
        </div>
        <div id="modeHint" class="notice notice-info"></div>

        <div class="paste-only">
          <label class="form-label" for="code">הקוד</label>
          <textarea name="code" id="code" class="form-control ltr code editor" rows="10" required placeholder="הדבק כאן את הקוד..." data-max-direct="{{ max_code_chars }}" data-max-ai="{{ max_ai_chars }}">
{{ f.get('code', '') }}</textarea>
          <div id="codeCount" class="form-text text-end"></div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary px-4 js-load">פרוס שרת</button>
          <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">ביטול</a>
          <span class="text-muted small">השרת עולה מיד אחרי הפריסה.</span>
        </div>
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
  var rn=$('route_name'), pv=$('rnPreview'), box=$('urlBox'), rh=$('rnHint'), okMsg=rh.textContent;
  var NAME_RE=/^[a-z0-9][a-z0-9_-]{0,39}$/;
  function prev(){
    var v=rn.value; pv.textContent=v||'my-api'; box.classList.toggle('is-empty',!v);
    var bad=v&&!NAME_RE.test(v); box.classList.toggle('is-bad',!!bad);
    rh.textContent=bad?'השם לא תקין: אותיות אנגליות קטנות, ספרות, _ או - בלבד, מתחיל באות או ספרה, עד 40 תווים.':okMsg;
    rh.classList.toggle('text-danger',!!bad);
  }
  rn.addEventListener('input',function(){rn.value=rn.value.toLowerCase();prev();}); prev();
  document.querySelectorAll('[data-lower]').forEach(function(i){i.addEventListener('input',function(){i.value=i.value.toLowerCase();});});
})();
</script>
{% endblock %}"""


ACCOUNT = """{% extends 'base.html' %}
{% block title %}הגדרות חשבון{% endblock %}
{% block content %}
<div class="mx-auto" style="max-width:780px">
  <div class="crumbs mb-2"><a href="{{ url_for('index') }}">שרתים</a> <span>/</span> <span>הגדרות חשבון</span></div>
  <h1 class="fs-4 fw-semibold mb-3">הגדרות חשבון</h1>

  <section class="card acct" aria-labelledby="h-profile">
    <div class="acct-head">
      <span class="svc-ico svc-ico-lg" aria-hidden="true">{{ current_user.username[:1]|upper }}</span>
      <div class="grow"><h2 id="h-profile" class="ltr">{{ current_user.username }}</h2><p>{% if current_user.email %}<span class="ltr d-inline-block">{{ current_user.email }}</span>{% else %}חשבון עם סיסמה{% endif %}</p></div>
      <span class="st {% if current_user.is_admin %}st-info{% else %}st-mute{% endif %}">{% if current_user.is_admin %}מנהל{% else %}משתמש{% endif %}</span>
    </div>
  </section>

  <section class="card acct" aria-labelledby="h-github">
    <div class="acct-head">
      <span class="svc-ico" aria-hidden="true">GH</span>
      <div class="grow"><h2 id="h-github">חיבור GitHub</h2><p>לייבוא קוד מריפו פרטי. ריפו ציבורי לא דורש חיבור.</p></div>
      {% if 'github' in saved_providers %}<span class="st st-ok">מחובר</span>{% else %}<span class="st st-mute">לא מחובר</span>{% endif %}
    </div>
    {% if 'github' in saved_providers %}
    <form method="post" action="{{ url_for('update_github') }}" class="m-0 d-flex justify-content-between align-items-center flex-wrap gap-2" data-confirm="לנתק את החיבור ל-GitHub?">
      __CSRF__<span class="text-muted small">הטוקן שמור מוצפן ומשמש לקריאה בלבד.</span><button name="action" value="delete" class="btn btn-sm btn-outline-danger">נתק</button>
    </form>
    {% else %}
    <form method="post" action="{{ url_for('update_github') }}">
      __CSRF__
      <label class="form-label" for="gh_token">טוקן גישה</label>
      <input type="password" id="gh_token" name="token" class="form-control ltr mb-2" placeholder="github_pat_..." autocomplete="off" required>
      <button name="action" value="save" class="btn btn-primary">חבר GitHub</button>
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
  </section>

  <section class="card acct" aria-labelledby="h-keys">
    <div class="acct-head">
      <span class="svc-ico" aria-hidden="true">AI</span>
      <div class="grow"><h2 id="h-keys">מפתחות API</h2><p>נדרשים רק לתרגום קוד משפות שאינן Python ולעריכה בעזרת AI. נשמרים מוצפנים.</p></div>
    </div>
    {% for key, label in providers.items() %}
    <div class="acct-row">
      <span class="fw-medium">{{ label }}</span>
      {% if key in saved_providers %}
      <form method="post" action="{{ url_for('update_key') }}" class="m-0 d-flex align-items-center gap-2">
        __CSRF__
        <input type="hidden" name="provider" value="{{ key }}">
        <span class="st st-ok">שמור</span>
        <button name="action" value="delete" class="btn btn-sm btn-outline-danger" aria-label="מחק את המפתח של {{ label }}">מחק</button>
      </form>
      {% else %}
      <span class="st st-mute">לא הוגדר</span>
      {% endif %}
    </div>
    {% endfor %}
    <form method="post" action="{{ url_for('update_key') }}" class="acct-add">
      __CSRF__
      <div class="fw-semibold small mb-2">הוספה או החלפה של מפתח</div>
      <div class="row g-2">
        <div class="col-sm-4"><label class="form-label" for="key_provider">ספק</label>
          <select name="provider" id="key_provider" class="form-select">{% for key, label in providers.items() %}<option value="{{ key }}">{{ label }}</option>{% endfor %}</select></div>
        <div class="col-sm-8"><label class="form-label" for="key_value">מפתח</label>
          <input type="password" id="key_value" name="api_key" class="form-control ltr" placeholder="הדבק מפתח" autocomplete="off" required></div>
      </div>
      <button name="action" value="save" class="btn btn-primary mt-3">שמור מפתח</button>
    </form>
  </section>
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
        <span class="st {% if route.status == 'active' %}st-ok{% elif route.status == 'rejected' %}st-bad{% else %}st-warn{% endif %}">{% if route.status == 'active' %}פעיל{% elif route.status == 'rejected' %}נדחה{% else %}לא פעיל{% endif %}</span>
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


LANDING = """{% extends 'base.html' %}
{% block title %}שרתים בלחיצה{% endblock %}
{% block content %}
<div class="lp">
<div class="lp-glow"></div>
<nav class="lp-nav">
  <a href="{{ url_for('index') }}" class="lp-logo"><span class="brand-mark brand-sm">SH</span>מערכת שרתים</a>
  <div class="lp-links"><a href="#features">תכונות</a><a href="#how">איך זה עובד</a></div>
  <div class="d-flex gap-2 align-items-center">
    <a href="{{ url_for('login_page') }}" class="btn btn-outline-secondary btn-sm">התחברות</a>
    <a href="{{ url_for('login_page') }}?tab=register" class="btn btn-primary btn-sm">התחל עכשיו</a>
  </div>
</nav>

<section class="lp-hero">
  <div class="lp-pill"><span class="dot dot-ok"></span>פריסה בשניות, בלי תשתית</div>
  <h1>מדביקים קוד.<br><span class="lp-grad">מקבלים שרת באינטרנט.</span></h1>
  <p>מעלים אפליקציית Flask או מייבאים ריפו מ-GitHub, והשרת עולה מיד בכתובת משלו. בלי להקים שרתים ובלי להתעסק בפריסה.</p>
  <div class="d-flex justify-content-center gap-2 flex-wrap">
    <a href="{{ url_for('login_page') }}?tab=register" class="btn btn-primary lp-btn">התחל עכשיו</a>
    <a href="{{ url_for('login_page') }}" class="btn btn-outline-secondary lp-btn">התחברות</a>
  </div>

  <div class="lp-demo" aria-hidden="true">
    <div class="lp-demo-bar"><i></i><i></i><i></i><span>deploy · hello</span></div>
    <div class="lp-demo-body">
      <div>$ <span class="hl">deploy</span> github.com/alice/hello</div>
      <div><span class="ok">&#10003;</span> Code validated</div>
      <div><span class="ok">&#10003;</span> Dependencies installed</div>
      <div><span class="ok">&#10003;</span> Environment variables loaded</div>
      <div><span class="hl">/hello</span><span class="lp-live"><span class="dot dot-ok"></span>Live</span></div>
    </div>
  </div>
</section>

<section class="lp-sec" id="features">
  <h2>כל מה שצריך כדי להעלות שרת</h2>
  <div class="sub">פשוט כמו להדביק קוד, עם הכלים שמצפים להם משירות אירוח.</div>
  <div class="row g-3">
    <div class="col-md-6 col-lg-4"><div class="lp-card"><span class="lp-ico">Py</span><h6>Python ישירות</h6><p>קוד Flask רץ כמו שהוא, בלי שינוי ובלי AI.</p></div></div>
    <div class="col-md-6 col-lg-4"><div class="lp-card"><span class="lp-ico">GH</span><h6>ייבוא מ-GitHub</h6><p>קובץ בודד או ריפו שלם, גם פרטי עם טוקן קריאה בלבד, ומשיכת גרסה עדכנית בלחיצה.</p></div></div>
    <div class="col-md-6 col-lg-4"><div class="lp-card"><span class="lp-ico">AI</span><h6>תרגום משפות אחרות</h6><p>PHP, JavaScript, Java, Go, Ruby ו-C# מתורגמים ל-Flask. נדרש מפתח API משלך.</p></div></div>
    <div class="col-md-6 col-lg-4"><div class="lp-card"><span class="lp-ico">&#9998;</span><h6>עורך קוד באתר</h6><p>עורכים בדפדפן, או מבקשים מה-AI שינוי ורואים מה השתנה לפני השמירה.</p></div></div>
    <div class="col-md-6 col-lg-4"><div class="lp-card"><span class="lp-ico">&#128274;</span><h6>משתני סביבה מוצפנים</h6><p>מפתחות וסיסמאות נשמרים מוצפנים ולא מוצגים אחרי השמירה.</p></div></div>
    <div class="col-md-6 col-lg-4"><div class="lp-card"><span class="lp-ico">&#9776;</span><h6>יומנים</h6><p>הבקשות האחרונות לכל שרת, עם רענון אוטומטי.</p></div></div>
  </div>
</section>

<section class="lp-sec" id="how">
  <h2>איך זה עובד</h2>
  <div class="sub">שלושה צעדים מהקוד לכתובת חיה.</div>
  <div class="row g-3 lp-steps">
    <div class="col-md-4"><div class="lp-step"><h6>פותחים חשבון</h6><p>שם משתמש וסיסמה{% if google_enabled %}, או Google{% endif %}. מנהל המערכת מאשר כל חשבון חדש.</p></div></div>
    <div class="col-md-4"><div class="lp-step"><h6>מדביקים או מייבאים</h6><p>מדביקים קוד, או מחברים קובץ וריפו מ-GitHub.</p></div></div>
    <div class="col-md-4"><div class="lp-step"><h6>השרת עולה מיד</h6><p>אחרי שהחשבון אושר אין אישור לכל שרת. מקבלים כתובת ועובדים איתה.</p></div></div>
  </div>
</section>

<section class="lp-cta">
  <h2>מוכנים להעלות את השרת הראשון?</h2>
  <p>ההרשמה פתוחה. החשבון מתחיל לעבוד אחרי אישור מנהל.</p>
  <a href="{{ url_for('login_page') }}?tab=register" class="btn btn-primary lp-btn">יצירת חשבון</a>
</section>

<footer class="lp-foot">
  <span>© מערכת שרתים</span>
  <span><a href="{{ url_for('login_page') }}">התחברות</a> · <a href="{{ url_for('login_page') }}?tab=register">הרשמה</a></span>
</footer>
</div>
{% endblock %}"""

PENDING = """{% extends 'base.html' %}
{% block title %}ממתין לאישור{% endblock %}
{% block content %}
<div class="d-flex justify-content-center pt-5">
  <div class="card p-4 p-md-5 text-center w-100" style="max-width:480px" role="status">
    <div class="brand-mark" style="background:var(--warn)">&#8987;</div>
    <h4 class="mb-2">החשבון ממתין לאישור</h4>
    <div class="mb-3"><span class="st st-warn">ממתין לאישור מנהל</span></div>
    <p class="text-muted mb-1">שלום <span class="ltr d-inline-block fw-semibold" style="color:var(--text)">{{ current_user.username }}</span>, החשבון נוצר.</p>
    <p class="text-muted">מנהל המערכת צריך לאשר אותו לפני שאפשר ליצור שרתים. אם הגישה שלך הושעתה, גם זה המסך שתראה. אפשר לרענן את הדף אחרי שהמנהל אישר.</p>
    <div class="d-flex justify-content-center gap-2 mt-2">
      <a href="{{ url_for('pending_page') }}" class="btn btn-primary">רענן</a>
      <form method="post" action="{{ url_for('logout') }}" class="m-0">__CSRF__<button class="btn btn-outline-secondary">התנתק</button></form>
    </div>
  </div>
</div>
{% endblock %}"""

ADMIN_USERS = """{% extends 'base.html' %}
{% block title %}משתמשים{% endblock %}
{% block content %}
{% set pend_n = users|rejectattr('is_approved')|rejectattr('is_admin')|list|length %}
<div class="page-head">
  <div><h1>משתמשים</h1><div class="sub">{{ users|length }} משתמשים{% if pend_n %} · <span class="st st-warn">{{ pend_n }} ממתינים לאישור</span>{% endif %}</div></div>
</div>
<div class="toolbar">
  <input type="search" id="usrSearch" class="form-control form-control-sm" style="max-width:320px" placeholder="חיפוש לפי שם או מייל..." aria-label="חיפוש משתמשים">
  <select id="usrFilter" class="form-select form-select-sm" style="width:auto" aria-label="סינון לפי סטטוס">
    <option value="">כולם</option><option value="pending">ממתינים לאישור</option><option value="approved">מאושרים</option><option value="admin">מנהלים</option>
  </select>
  <span class="count" id="usrCount" aria-live="polite">{{ users|length }} משתמשים</span>
</div>
<div class="tbl mb-5" id="usrList">
  <div class="tbl-head usr-row"><div>משתמש</div><div class="c-hide">סטטוס</div><div class="c-hide">שרתים</div><div class="c-hide">נרשם</div><div></div></div>
  {% for u in users %}
  <div class="usr-row srv" data-name="{{ u.username }} {{ u.email or '' }}" data-status="{% if u.is_admin %}admin{% elif u.is_approved %}approved{% else %}pending{% endif %}">
    <div style="min-width:0">
      <a href="{{ url_for('admin_user', user_id=u.id) }}" class="srv-name ltr d-inline-block">{{ u.username }}</a>
      <div class="srv-url text-truncate">{% if u.email %}<span class="ltr d-inline-block">{{ u.email }}</span>{% else %}חשבון סיסמה{% endif %}</div>
    </div>
    <div class="c-hide"><span class="st {% if u.is_admin %}st-info{% elif u.is_approved %}st-ok{% else %}st-warn{% endif %}">{% if u.is_admin %}מנהל{% elif u.is_approved %}מאושר{% else %}ממתין לאישור{% endif %}</span></div>
    <div class="c-hide text-muted">{{ counts.get(u.id, 0) }}</div>
    <div class="c-hide text-muted">{{ u.created_at|timeago }}</div>
    <div class="srv-actions justify-content-end">
      {% if not u.is_approved and not u.is_admin %}
      <form method="post" action="{{ url_for('approve_user', user_id=u.id) }}">__CSRF__<button class="btn btn-sm btn-success">אשר</button></form>
      {% endif %}
      <a href="{{ url_for('admin_user', user_id=u.id) }}" class="btn btn-sm btn-outline-secondary">פרטים</a>
    </div>
  </div>
  {% endfor %}
</div>
<div id="usrNone" class="empty mb-5 d-none">
  <div class="em-ico" aria-hidden="true">&#8981;</div>
  <div class="fw-semibold mb-1" style="color:var(--text)">לא נמצאו משתמשים</div>
  <div class="mb-3">אין משתמשים שמתאימים לחיפוש או לסינון.</div>
  <button type="button" class="btn btn-outline-secondary btn-sm" id="usrReset">נקה סינון</button>
</div>
{% endblock %}
{% block scripts %}
<script>
(function(){
  var q=document.getElementById('usrSearch'), f=document.getElementById('usrFilter');
  function filt(){
    var t=q.value.trim().toLowerCase(), st=f.value, shown=0;
    document.querySelectorAll('#usrList .srv').forEach(function(r){
      var ok=(!t||r.dataset.name.toLowerCase().indexOf(t)>-1)&&(!st||r.dataset.status===st);
      r.classList.toggle('d-none',!ok); if(ok) shown++;
    });
    document.getElementById('usrNone').classList.toggle('d-none',shown>0);
    document.getElementById('usrList').classList.toggle('d-none',shown===0);
    document.getElementById('usrCount').textContent=shown+' משתמשים';
  }
  q.addEventListener('input',filt); f.addEventListener('change',filt);
  document.getElementById('usrReset').addEventListener('click',function(){q.value='';f.value='';filt();q.focus();});
})();
</script>
{% endblock %}"""

ADMIN_USER = """{% extends 'base.html' %}
{% block title %}{{ target.username }}{% endblock %}
{% block content %}
<div class="crumbs mb-2"><a href="{{ url_for('admin_users') }}">משתמשים</a> <span>/</span> <span class="ltr d-inline-block">{{ target.username }}</span></div>
<div class="d-flex justify-content-between align-items-start flex-wrap gap-3 mb-4">
  <div>
    <h4 class="fw-semibold ltr mb-1">{{ target.username }}</h4>
    <div class="d-flex gap-2 align-items-center flex-wrap small text-muted">
      <span class="st {% if target.is_admin %}st-info{% elif target.is_approved %}st-ok{% else %}st-warn{% endif %}">{% if target.is_admin %}מנהל{% elif target.is_approved %}מאושר{% else %}ממתין לאישור{% endif %}</span>
      <span>·</span>
      <span>{% if target.email %}<span class="ltr d-inline-block">{{ target.email }}</span>{% else %}נרשם עם סיסמה{% endif %}</span>
      <span>·</span><span>נרשם {{ target.created_at|timeago }}</span>
    </div>
  </div>
  <div class="srv-actions">
    {% if not target.is_approved and not target.is_admin %}
    <form method="post" action="{{ url_for('approve_user', user_id=target.id) }}">__CSRF__<input type="hidden" name="back" value="user"><button class="btn btn-success btn-sm">אשר משתמש</button></form>
    {% endif %}
    {% if target.is_approved and not target.is_admin %}
    <form method="post" action="{{ url_for('suspend_user', user_id=target.id) }}" data-confirm="להשעות את {{ target.username }}? השרתים שלו יפסיקו להיות מוגשים עד שתאשר אותו שוב.">__CSRF__<input type="hidden" name="back" value="user"><button class="btn btn-outline-secondary btn-sm">השעה</button></form>
    {% endif %}
    {% if not target.is_admin %}
    <form method="post" action="{{ url_for('delete_user', user_id=target.id) }}" data-confirm="למחוק את המשתמש {{ target.username }} ואת כל השרתים שלו לצמיתות? אי אפשר לשחזר.">__CSRF__<button class="btn btn-outline-danger btn-sm">מחק משתמש</button></form>
    {% endif %}
  </div>
</div>

<h5 class="fw-semibold mb-3">שרתים של המשתמש <span class="text-muted fs-6">({{ routes|length }})</span></h5>
{% if routes %}
<div class="tbl mb-5">
  <div class="tbl-head srv-row"><div>שם</div><div>סטטוס</div><div class="c-runtime">סביבת הרצה</div><div class="c-upd">עודכן</div><div></div></div>
  {% for route in routes %}
  {% set is_bundle = (route.live_code or route.pending_code or '').startswith('{"bundle"') %}
  <div class="srv-row srv position-relative">
    <div class="d-flex align-items-center gap-3" style="min-width:0">
      <span class="svc-ico">Py</span>
      <div style="min-width:0">
        {% if route.live_code or route.pending_code %}<a href="{{ url_for('edit_route', route_id=route.id) }}" class="srv-name stretched-link">{{ route.route_name }}</a>{% else %}<span class="srv-name">{{ route.route_name }}</span>{% endif %}
        <div class="srv-url ltr text-truncate">{{ route.full_path }}</div>
      </div>
    </div>
    <div><span class="st {% if route.status == 'active' %}st-ok{% elif route.status == 'rejected' %}st-bad{% else %}st-warn{% endif %}">{% if route.status == 'active' %}פעיל{% elif route.status == 'rejected' %}נדחה{% else %}לא פעיל{% endif %}</span></div>
    <div class="c-runtime text-muted">Python 3{% if route.source %} · GitHub{% endif %}{% if is_bundle %} · כמה קבצים{% endif %}</div>
    <div class="c-upd text-muted">{{ route.updated_at|timeago }}</div>
    <div class="dropdown position-relative" style="z-index:3">
      <button type="button" class="kebab" data-bs-toggle="dropdown" aria-expanded="false" aria-label="פעולות עבור {{ route.route_name }}">&#8943;</button>
      <ul class="dropdown-menu dropdown-menu-end">
        {% if route.status == 'active' and target.is_approved %}<li><a class="dropdown-item" href="{{ route.full_path }}" target="_blank" rel="noopener">פתח את השרת</a></li>{% endif %}
        {% if route.live_code or route.pending_code %}<li><a class="dropdown-item" href="{{ url_for('edit_route', route_id=route.id) }}">צפה / ערוך קוד</a></li>{% endif %}
        <li><a class="dropdown-item" href="{{ url_for('view_logs', route_id=route.id) }}">יומנים</a></li>
        <li><hr class="dropdown-divider" style="border-color:var(--border)"></li>
        <li><form method="post" action="{{ url_for('delete_route', route_id=route.id) }}" data-confirm="למחוק את השרת {{ route.full_path }} לצמיתות? אי אפשר לשחזר.">__CSRF__<button class="dropdown-item" style="color:var(--bad)">מחק שרת</button></form></li>
      </ul>
    </div>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="empty mb-5">
  <div class="em-ico" aria-hidden="true">&#9889;</div>
  <div class="fw-semibold mb-1" style="color:var(--text)">אין עדיין שרתים</div>
  <div>למשתמש הזה עוד לא נוצרו שרתים.</div>
</div>
{% endif %}
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
    "landing.html": LANDING,
    "pending.html": PENDING,
    "admin_users.html": ADMIN_USERS,
    "admin_user.html": ADMIN_USER,
}
TEMPLATES = {name: tpl.replace("__CSRF__", CSRF) for name, tpl in TEMPLATES.items()}

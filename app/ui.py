"""واجهة Streamlit لاختيار الموديل والتصنيف وتشغيل السحب."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pipeline.paths import is_frozen, project_root, resource_root

_PROJECT_ROOT = project_root()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(resource_root()) not in sys.path and resource_root() != _PROJECT_ROOT:
    sys.path.insert(0, str(resource_root()))

import streamlit as st

from pipeline import catalog
from pipeline.constants import CATALOG_FILES

if not is_frozen():
    importlib.reload(catalog)
from pipeline.constants import MAP_PLACE_CATEGORIES
from pipeline.errors import PipelineError
from pipeline.field_mapping import WORKFLOW_TIP, build_pre_scrape_summary, field_source_rows
from pipeline.maps_runner import MapsRunRequest, run_maps_job
from pipeline.runner import CategoryRunRequest, run_category_job

st.set_page_config(
    page_title="تصدير المنتجات",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _warm_playwright_for_instashop() -> None:
    from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium

    ensure_playwright_chromium()


try:
    _warm_playwright_for_instashop()
except Exception as exc:
    st.session_state["_playwright_error"] = str(exc)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

    :root {
        --bg-white: #ffffff;
        --bg-soft: #f6faf7;
        --text-dark: #0f1f17;
        --text-muted: #52685c;
        --green: #0d5c3d;
        --green-dark: #063d2a;
        --green-light: #e8f5ee;
        --border: #d4e4da;
        --shadow-sm: 0 8px 22px rgba(13, 92, 61, 0.08);
        --shadow-md: 0 18px 44px rgba(13, 92, 61, 0.14);
    }

    /* ── خلفية بيضاء وتباين عالٍ ── */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top right, rgba(13, 92, 61, 0.10), transparent 34rem),
            linear-gradient(180deg, #ffffff 0%, #f8fbf9 100%) !important;
        color: var(--text-dark) !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    .block-container {
        padding-top: 0.75rem;
        padding-bottom: 3rem;
        max-width: 1200px;
        background: transparent;
    }

    /* ── RTL شامل لكل عناصر Streamlit ── */
    .stApp, section.main, section.main .block-container,
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div,
    [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"],
    [data-testid="column"], [data-testid="stMarkdownContainer"],
    .stSelectbox, .stTextInput, .stNumberInput, .stCheckbox,
    .stExpander, [data-testid="stAlert"], label, p, span, h1, h2, h3, li {
        direction: rtl !important;
        text-align: right !important;
    }

    /* الشريط الجانبي — يمين + أبيض */
    section[data-testid="stSidebar"] {
        right: 0 !important;
        left: auto !important;
        background: var(--bg-white) !important;
        border-left: none !important;
        border-right: 2px solid var(--border) !important;
        box-shadow: -4px 0 16px rgba(0,0,0,0.04);
    }
    section[data-testid="stSidebar"] * {
        color: var(--text-dark) !important;
    }

    /* ترتيب الأعمدة: أول عنصر في الكود يظهر يميناً مع اتجاه RTL */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        gap: 1.5rem;
    }

    /* حقول إدخال بيضاء وحدود واضحة ونص ظاهر */
    input, textarea, [data-baseweb="select"] > div,
    div[data-testid="stNumberInput"] input,
    [data-baseweb="popover"],
    [role="listbox"],
    [role="option"] {
        background: var(--bg-white) !important;
        color: var(--text-dark) !important;
        border-color: var(--border) !important;
        border-radius: 12px !important;
        text-align: right !important;
        direction: rtl !important;
    }
    [data-baseweb="select"] *, [data-baseweb="popover"] *,
    [role="listbox"] *, [role="option"] * {
        color: var(--text-dark) !important;
        direction: rtl !important;
        text-align: right !important;
    }
    input::placeholder, textarea::placeholder {
        color: #789083 !important;
        opacity: 1 !important;
    }
    label, .stSelectbox label, .stTextInput label {
        color: var(--text-dark) !important;
        font-weight: 600 !important;
    }

    /* الترويسة — أخضر غامق ونص أبيض (تباين عالٍ) */
    .hero {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at 10% 20%, rgba(255,255,255,0.20), transparent 18rem),
            linear-gradient(135deg, #063d2a 0%, #0d5c3d 48%, #13935f 100%);
        border-radius: 26px;
        padding: 2rem;
        margin-bottom: 1.1rem;
        color: #ffffff !important;
        box-shadow: var(--shadow-md);
        text-align: right !important;
        direction: rtl !important;
    }
    .hero::after {
        content: "";
        position: absolute;
        inset: auto -6rem -8rem auto;
        width: 22rem;
        height: 22rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.11);
    }
    .hero-content {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
        gap: 1.5rem;
        align-items: center;
    }
    .hero-badge {
        display: inline-flex;
        width: fit-content;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.26);
        border-radius: 999px;
        padding: 0.35rem 0.8rem;
        margin-bottom: 0.8rem;
        color: #ffffff !important;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .hero h1 {
        margin: 0 0 0.3rem 0;
        font-size: clamp(1.8rem, 4vw, 3.1rem);
        line-height: 1.15;
        font-weight: 800;
        color: #ffffff !important;
    }
    .hero p {
        margin: 0;
        color: #f0fff7 !important;
        font-size: 1rem;
        line-height: 1.8;
        max-width: 680px;
    }
    .hero-stats {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
    }
    .hero-stat {
        background: rgba(255,255,255,0.13);
        border: 1px solid rgba(255,255,255,0.24);
        border-radius: 18px;
        padding: 1rem;
        backdrop-filter: blur(8px);
    }
    .hero-stat strong {
        display: block;
        color: #ffffff !important;
        font-size: 1.2rem;
        font-weight: 800;
    }
    .hero-stat span {
        color: #e8fff2 !important;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .quick-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
        margin-bottom: 1.2rem;
    }
    .quick-card, .panel-card, .result-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid var(--border);
        border-radius: 20px;
        box-shadow: var(--shadow-sm);
    }
    .quick-card {
        padding: 0.9rem 1rem;
    }
    .quick-card strong {
        display: block;
        color: var(--green-dark) !important;
        font-size: 0.96rem;
        margin-bottom: 0.25rem;
    }
    .quick-card span {
        color: var(--text-muted) !important;
        font-size: 0.82rem;
    }
    .panel-card {
        padding: 1.1rem 1.15rem 1.2rem;
        margin-bottom: 1rem;
    }
    .section-kicker {
        color: var(--text-muted) !important;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .catalog-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin: 0.2rem 0 1rem;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.45rem 0.75rem;
        font-size: 0.82rem;
        font-weight: 700;
        border: 1px solid var(--border);
        background: var(--bg-white);
        color: var(--text-dark) !important;
    }
    .status-chip.ok {
        background: var(--green-light);
        color: var(--green-dark) !important;
        border-color: #b9ddc8;
    }
    .status-chip.missing {
        background: #fff7ed;
        color: #8a4b05 !important;
        border-color: #f3d7ae;
    }
    @media (max-width: 900px) {
        .hero-content, .quick-grid {
            grid-template-columns: 1fr;
        }
        .hero-stats {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    .panel-title {
        font-size: 1.08rem;
        font-weight: 800;
        color: var(--green) !important;
        margin-bottom: 0.85rem;
        padding-bottom: 0.45rem;
        border-bottom: 2px solid var(--green-light);
        text-align: right !important;
    }

    /* بطاقات المقاييس — أبيض + حدود خضراء */
    div[data-testid="stMetric"] {
        background: var(--bg-white) !important;
        border: 2px solid var(--border) !important;
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--green) !important;
        font-weight: 800 !important;
    }

    /* أزرار */
    .stButton > button {
        direction: rtl !important;
        font-family: 'Tajawal', sans-serif !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--green-dark), var(--green)) !important;
        color: #ffffff !important;
        border: 2px solid #064a2f !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        min-height: 3rem !important;
        box-shadow: 0 10px 24px rgba(13, 92, 61, 0.18);
    }
    .stButton > button[kind="secondary"] {
        background: var(--bg-white) !important;
        color: var(--green) !important;
        border: 2px solid var(--green) !important;
    }

    /* رفع الملفات — تباين واضح على خلفية بيضاء */
    [data-testid="stFileUploader"] {
        direction: rtl !important;
    }
    [data-testid="stFileUploader"] label {
        color: var(--text-dark) !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: var(--green-light) !important;
        border: 2px dashed var(--green) !important;
        border-radius: 10px !important;
        padding: 0.55rem 0.75rem !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        background: #dff0e8 !important;
        border-color: #064a2f !important;
    }
    [data-testid="stFileUploaderDropzone"] div,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] p,
    [data-testid="stFileUploaderDropzone"] small {
        color: var(--text-dark) !important;
        font-weight: 500 !important;
    }
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploader"] [data-testid="baseButton-secondary"] {
        background: var(--green) !important;
        color: #ffffff !important;
        border: 2px solid #064a2f !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }
    [data-testid="stFileUploader"] button:hover,
    [data-testid="stFileUploader"] [data-testid="baseButton-secondary"]:hover {
        background: #064a2f !important;
        color: #ffffff !important;
        border-color: #043d27 !important;
    }

    /* زر التنزيل بجانب الرفع */
    .stDownloadButton > button {
        background: var(--bg-white) !important;
        color: var(--green) !important;
        border: 2px solid var(--green) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        min-height: 2.6rem !important;
    }
    .stDownloadButton > button:hover {
        background: var(--green-light) !important;
        color: #064a2f !important;
        border-color: #064a2f !important;
    }

    /* جداول وتنبيهات */
    [data-testid="stDataFrame"] {
        direction: rtl !important;
    }
    [data-testid="stAlert"] {
        background: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-dark) !important;
    }

    /* expander و code */
    details summary {
        direction: rtl !important;
        text-align: right !important;
        color: var(--text-dark) !important;
    }
    code {
        direction: ltr;
        text-align: left;
        background: var(--green-light) !important;
        color: var(--green) !important;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
    }

    .log-box {
        background: #0f1f17;
        color: #e8fff2;
        border-radius: 10px;
        padding: 1rem;
        font-family: 'Menlo', monospace;
        font-size: 0.78rem;
        max-height: 220px;
        overflow-y: auto;
        direction: ltr;
        text-align: left;
        border: 1px solid var(--border);
    }

    .result-card {
        padding: 1.15rem;
        margin-top: 1rem;
    }

    /* إخفاء الشريط الجانبي وزر فتحه */
    section[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    section.main .block-container {
        max-width: 1180px;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* إخفاء شريط Streamlit العلوي والقائمة السوداء */
    header[data-testid="stHeader"],
    .stApp > header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        padding-top: 0 !important;
    }

    /* ── شبكة أمان للتباين: لا نص فاتح على خلفية فاتحة ولا داكن على داكن ── */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    [data-testid="stMarkdownContainer"],
    [data-testid="stRadio"] label, [data-testid="stCheckbox"] label,
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
        color: var(--text-dark);
    }
    /* الجداول و JSON على خلفية بيضاء بنص داكن */
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] *,
    [data-testid="stJson"], [data-testid="stJson"] *,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
        color: var(--text-dark) !important;
    }
    [data-testid="stExpander"] {
        background: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px;
    }
    /* عناصر النص الداكنة المقصودة تحتفظ بنصها الفاتح */
    .hero, .hero *, .log-box, .log-box *,
    .stButton > button[kind="primary"],
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploaderDropzone"] button {
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"] * {
        color: #ffffff !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

if "progress_log" not in st.session_state:
    st.session_state.progress_log = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_maps_result" not in st.session_state:
    st.session_state.last_maps_result = None

_DEFAULT_MODULE_ID = 3  # سوبر ماركت


def _modules_default_first(modules: list) -> list:
    preferred = [m for m in modules if m.module_id == _DEFAULT_MODULE_ID]
    others = sorted(
        (m for m in modules if m.module_id != _DEFAULT_MODULE_ID),
        key=lambda m: m.module_id,
    )
    return preferred + others


def _page_from_url(url: str) -> int:
    try:
        return max(1, int(parse_qs(urlparse(url).query).get("page", ["1"])[0]))
    except (ValueError, TypeError):
        return 1


def _progress_log(phase: str, current: int, total: int, message: str):
    st.session_state.progress_log.append(f"[{phase}] {current}/{total}: {message}")


# ── الشريط الجانبي ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 خطوات العمل")
    st.markdown(
        """
1. **اختر المصدر**: موقع، خريطة، أو خيارات أخرى  
2. **من موقع**: ارفع ملفات Excel واختر التصنيف والرابط  
3. **من خريطة**: المدينة، المساحة، والتصنيفات  
4. اضغط **بدء السحب** أو **سحب من الخريطة**
        """
    )
    st.divider()
    st.markdown("### 📊 ملفات الكتالوج (محلي)")
    st.markdown(
        '<p style="color:#3d5247;font-size:0.88rem;margin:0 0 0.5rem 0;">'
        "ارفع ملف Excel — يُحفظ في <code>catalog/</code> وتُعرض خياراته مباشرة في القوائم"
        "</p>",
        unsafe_allow_html=True,
    )

    if "catalog_saved" not in st.session_state:
        st.session_state.catalog_saved = {}

    sources = catalog.catalog_sources()
    for fname, label in CATALOG_FILES.items():
        ok = sources.get(fname, False)
        st.markdown(f"{'✅' if ok else '❌'} **{label}** — `{fname}`")

        col_up, col_dl = st.columns([2, 1])
        with col_up:
            uploaded = st.file_uploader(
                f"📤 رفع {label}",
                type=["xlsx"],
                key=f"upload_{fname}",
                help=f"اختر ملف {fname}",
            )
        with col_dl:
            existing = catalog.read_catalog_file(fname)
            if existing:
                st.download_button(
                    "⬇️",
                    data=existing,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{fname}",
                    help=f"تنزيل {fname}",
                )

        if uploaded is not None:
            sig = f"{uploaded.name}:{uploaded.size}"
            if st.session_state.catalog_saved.get(fname) != sig:
                catalog.save_catalog_file(fname, uploaded.getvalue())
                st.session_state.catalog_saved[fname] = sig
                st.success(f"تم حفظ `{fname}`")
                st.rerun()

    if st.button("🔄 تحديث الكتالوج", width="stretch"):
        catalog.clear_cache()
        st.rerun()
    st.divider()
    st.markdown("### 📁 المخرجات")
    st.caption("Excel + صور WebP في مجلد `output/`")
    st.caption("معرفات عالمية متصلة عبر التصنيفات")

# ── الترويسة ──────────────────────────────────────────────────
catalog_sources = catalog.catalog_sources()
catalog_ready = sum(1 for fname in CATALOG_FILES if catalog_sources.get(fname, False))
catalog_total = len(CATALOG_FILES)

if st.session_state.get("_playwright_error"):
    st.warning(
        "تعذّر تهيئة متصفح Instashop على السيرفر. "
        "سيتم إعادة المحاولة عند السحب. "
        f"({st.session_state['_playwright_error']})"
    )

st.markdown(
    f"""
<div class="hero">
  <div class="hero-content">
    <div>
      <div class="hero-badge">لوحة تحكم المنتج</div>
      <h1>نظام السحب والتصدير الذكي</h1>
      <p>من موقع إلكتروني أو من خريطة Google — اختر المصدر، حدّد الإعدادات، وصدّر النتائج إلى Excel.</p>
    </div>
    <div class="hero-stats">
      <div class="hero-stat"><strong>{catalog_ready}/{catalog_total}</strong><span>ملفات كتالوج جاهزة</span></div>
      <div class="hero-stat"><strong>WebP</strong><span>صور مضغوطة</span></div>
      <div class="hero-stat"><strong>Auto</strong><span>بجنيشن تلقائي</span></div>
      <div class="hero-stat"><strong>RTL</strong><span>واجهة عربية</span></div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

catalog_chips = []
for fname, label in CATALOG_FILES.items():
    ok = catalog_sources.get(fname, False)
    cls = "ok" if ok else "missing"
    icon = "✓" if ok else "!"
    catalog_chips.append(f'<span class="status-chip {cls}">{icon} {label}</span>')

st.markdown(
    f"""
<div class="quick-grid">
  <div class="quick-card"><strong>1. اختر المصدر</strong><span>موقع إلكتروني، خريطة، أو خيارات أخرى.</span></div>
  <div class="quick-card"><strong>2. حدّد الإعدادات</strong><span>تصنيفات، رابط، أو مدينة ومساحة تغطية.</span></div>
  <div class="quick-card"><strong>3. شغّل السحب</strong><span>منتجات مع صور أو محلات مع بيانات الاتصال.</span></div>
  <div class="quick-card"><strong>4. راجع النتيجة</strong><span>ملف Excel جاهز يظهر أسفل الصفحة.</span></div>
</div>
<div class="panel-card">
  <div class="section-kicker">جاهزية ملفات الكتالوج</div>
  <div class="catalog-strip">{''.join(catalog_chips)}</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_website, tab_maps, tab_other = st.tabs(
    ["🌐 من موقع", "🗺️ من خريطة", "📋 خيارات أخرى"]
)

with tab_website:
    col_cat, col_scrape = st.columns([1, 1], gap="large")

    with col_cat:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🏷️ الموديل والتصنيف</div>', unsafe_allow_html=True)

        modules = _modules_default_first(catalog.list_modules())
        if not modules:
            st.warning("لا توجد موديلات — تأكد من وجود `catalog/modules.xlsx`")
            st.stop()

        module_labels = {m.module_id: m.name_ar for m in modules}
        module_id = st.selectbox(
            "الموديل",
            options=[m.module_id for m in modules],
            index=0,
            format_func=lambda mid: f"{mid} — {module_labels[mid]}",
        )

        categories = catalog.list_categories(module_id)
        if not categories:
            st.warning(
                f"لا توجد تصنيفات للموديل {module_id} — أضف صفوفاً في "
                "`categories.xlsx` (عمود الوحدة = اسم الموديل) أو `subcategories.xlsx`"
            )
            st.stop()

        category_labels = {c.category_id: c.name_ar for c in categories}
        category_id = st.selectbox(
            "التصنيف الرئيسي",
            options=[c.category_id for c in categories],
            format_func=lambda cid: f"{cid} — {category_labels[cid]}",
        )

        subcategories = catalog.list_subcategories(module_id, category_id)
        if not subcategories:
            st.warning(
                f"لا توجد تصنيفات فرعية للتصنيف {category_id} — أضف صفاً في `subcategories.xlsx`"
            )
            st.stop()

        sub_labels = {s.sub_category_id: s.name_ar for s in subcategories}
        sub_category_id = st.selectbox(
            "التصنيف الفرعي",
            options=[s.sub_category_id for s in subcategories],
            format_func=lambda sid: f"{sid} — {sub_labels[sid]}",
        )

        sub = catalog.get_subcategory(module_id, category_id, sub_category_id)
        units = catalog.get_units(module_id)

        st.markdown("**المعرفات المُعبَّأة تلقائياً**")
        m3, m2, m1 = st.columns(3)
        m3.metric("ModuleId", module_id)
        m2.metric("CategoryId", category_id)
        m1.metric("SubCategoryId", sub_category_id)

        if units:
            with st.expander(f"📐 وحدات الموديل ({len(units)})", expanded=False):
                st.dataframe(
                    [
                        {"UnitId": u.unit_id, "الاسم": u.name_ar, "مرادفات": ", ".join(u.aliases)}
                        for u in units
                    ],
                    hide_index=True,
                    width="stretch",
                )
        else:
            st.error(
                f"لا توجد وحدات للموديل {module_id} — تأكد من وجود `catalog/units.xlsx` "
                f"(عمود ModuleId = {module_id})"
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_scrape:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">⚙️ إعدادات السحب</div>', unsafe_allow_html=True)

        source_url = st.text_input("🔗 رابط المصدر", value=sub.default_source_url)

        scrape_scope = st.radio(
            "نطاق الصفحات",
            options=["all", "single"],
            format_func=lambda v: (
                "كل المنتجات — يتابع البجنيشن تلقائياً"
                if v == "all"
                else "صفحة واحدة فقط"
            ),
            horizontal=True,
        )

        if scrape_scope == "single":
            page_number = st.number_input(
                "رقم الصفحة",
                min_value=1,
                value=_page_from_url(source_url),
                step=1,
                help="يُسحب منتجات هذه الصفحة فقط",
            )
            max_pages = 1
            start_page = int(page_number)
        else:
            max_pages = 0
            start_page = _page_from_url(source_url)
            if start_page > 1:
                st.caption(
                    f"يبدأ من صفحة {start_page} (من الرابط) ثم يتابع حتى آخر صفحة"
                )
            else:
                st.caption("يبدأ من الصفحة 1 ويجلب كل المنتجات عبر البجنيشن")

        c_right, c_left = st.columns(2)
        with c_right:
            output_dir = st.text_input("📂 مجلد الإخراج", value="output")
            excel_filename = st.text_input("📊 ملف Excel", value=sub.excel_filename)
        with c_left:
            images_folder = st.text_input("🖼️ مجلد الصور", value=sub.images_folder)

        rescrape = st.checkbox("🔄 إعادة سحب — استبدال نفس نطاق المعرفات", value=False)
        apply_category_rules = st.checkbox(
            "🔗 تفعيل قواعد ربط تصنيف الموقع",
            value=False,
            help="يستخدم catalog/category_mapping_rules.xlsx لمطابقة نص تصنيف الموقع مع SubCategoryId",
        )

        st.markdown(
            f'<p style="color:#5a7a65;font-size:0.85rem;margin:0.5rem 0;">'
            f'المسار: <code>{output_dir}/{sub.output_slug}/</code></p>',
            unsafe_allow_html=True,
        )

        st.info(WORKFLOW_TIP)
        with st.expander("📋 كيف تُملأ حقول Excel؟", expanded=False):
            summary = build_pre_scrape_summary(
                module_id,
                category_id,
                sub_category_id,
                category_labels[category_id],
                sub_labels[sub_category_id],
                len(units) if units else 0,
            )
            st.caption(summary["note"])
            if catalog.catalog_sources().get("category_mapping_rules.xlsx"):
                st.caption(
                    "يمكنك تفعيل «قواعد ربط تصنيف الموقع» أسفل الصفحة "
                    "لمطابقة نص تصنيف الموقع مع SubCategoryId."
                )
            st.dataframe(
                [
                    {
                        "الحقل": f"{row['icon']} {row['label_ar']}",
                        "المصدر": row["source_ar"],
                    }
                    for row in field_source_rows()
                ],
                hide_index=True,
                width="stretch",
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("CategoryId", category_id)
            c2.metric("SubCategoryId", sub_category_id)
            c3.metric("ModuleId", module_id)

        start_disabled = not units
        if st.button(
            "🚀 بدء السحب",
            type="primary",
            disabled=start_disabled,
            width="stretch",
            key="start_website_scrape",
        ):
            st.session_state.progress_log = []
            try:
                request = CategoryRunRequest(
                    module_id=module_id,
                    category_id=category_id,
                    sub_category_id=sub_category_id,
                    source_url=source_url,
                    output_dir=output_dir,
                    excel_filename=excel_filename,
                    images_folder=images_folder,
                    max_pages=max_pages,
                    start_page=start_page,
                    rescrape=rescrape,
                    apply_category_rules=apply_category_rules,
                )
                with st.spinner("⏳ جاري السحب وتحميل الصور..."):
                    result = run_category_job(request, on_progress=_progress_log)
                st.session_state.last_result = result
                st.session_state.last_maps_result = None
                st.balloons()
                st.success(
                    f"✅ اكتمل — {result.stats['products_total']} منتج | "
                    f"🖼️ {result.stats['images_ok']} صورة ناجحة"
                )
            except PipelineError as exc:
                st.error(f"❌ {exc.code}: {exc}")
            except Exception as exc:
                st.error(f"❌ {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_maps:
    col_map_settings, col_map_output = st.columns([1, 1], gap="large")

    with col_map_settings:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🗺️ إعدادات الخريطة</div>', unsafe_allow_html=True)

        map_city = st.text_input("🏙️ المدينة / المنطقة", placeholder="مثال: القاهرة، الإسكندرية، الرياض")
        map_district = st.text_input(
            "📍 حي أو منطقة فرعية (اختياري)",
            placeholder="مثال: مدينة نصر، المعادي",
        )
        map_radius = st.slider(
            "مساحة التغطية (كم)",
            min_value=1,
            max_value=50,
            value=10,
            help="كلما زادت المساحة زاد عدد المحلات المسحوبة والوقت المطلوب",
        )
        map_categories = st.multiselect(
            "التصنيفات المطلوبة",
            options=MAP_PLACE_CATEGORIES,
            default=["مطاعم"],
            help="يمكن اختيار أكثر من تصنيف — يُسحب كل تصنيف على حدة",
        )

        st.caption(
            "النتيجة: اسم المحل، العنوان، رقم الهاتف، التصنيف، المدينة، ورابط الخريطة."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_map_output:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">📊 إخراج المحلات</div>', unsafe_allow_html=True)

        map_output_dir = st.text_input("📂 مجلد الإخراج", value="output", key="map_output_dir")
        map_excel_filename = st.text_input("📊 ملف Excel", value="places.xlsx", key="map_excel")

        map_disabled = not map_city.strip() or not map_categories
        if st.button(
            "🚀 سحب من الخريطة",
            type="primary",
            disabled=map_disabled,
            width="stretch",
            key="start_maps_scrape",
        ):
            st.session_state.progress_log = []
            try:
                maps_request = MapsRunRequest(
                    city=map_city.strip(),
                    radius_km=float(map_radius),
                    categories=map_categories,
                    district=map_district.strip(),
                    output_dir=map_output_dir,
                    excel_filename=map_excel_filename,
                )
                with st.spinner("⏳ جاري سحب المحلات من Google Maps..."):
                    maps_result = run_maps_job(maps_request, on_progress=_progress_log)
                st.session_state.last_maps_result = maps_result
                st.session_state.last_result = None
                st.balloons()
                st.success(
                    f"✅ اكتمل — {maps_result.stats['places_total']} محل | "
                    f"📞 {maps_result.stats['with_phone']} برقم هاتف"
                )
            except PipelineError as exc:
                st.error(f"❌ {exc.code}: {exc}")
            except Exception as exc:
                st.error(f"❌ {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_other:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📋 خيارات أخرى</div>', unsafe_allow_html=True)
    st.info(
        "قريباً: سحب من Instagram، Facebook، دليل يدوي (CSV)، أو مصادر مخصصة. "
        "أخبرنا بالمصدر الذي تريده لنضيفه."
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ── السجل والنتائج ────────────────────────────────────────────
if st.session_state.progress_log:
    with st.expander("📜 سجل التقدم", expanded=False):
        log_html = "<br>".join(st.session_state.progress_log[-40:])
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

if st.session_state.last_maps_result:
    r = st.session_state.last_maps_result
    st.markdown(
        """
<div class="result-card">
  <div class="section-kicker">ملخص التنفيذ</div>
  <div class="panel-title">🗺️ آخر سحب من الخريطة</div>
</div>
""",
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("المحلات", r.stats.get("places_total", 0))
    m2.metric("بأرقام هاتف", r.stats.get("with_phone", 0))
    m3.metric("التصنيفات", r.stats.get("categories", 0))

    st.markdown("**ملف Excel**")
    st.code(r.excel_path, language=None)

    with st.expander("تفاصيل JSON", expanded=False):
        st.json({"status": r.status, "stats": r.stats})

if st.session_state.last_result:
    r = st.session_state.last_result
    st.markdown(
        """
<div class="result-card">
  <div class="section-kicker">ملخص التنفيذ</div>
  <div class="panel-title">📦 آخر عملية سحب</div>
</div>
""",
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("المنتجات", r.stats.get("products_total", 0))
    s2.metric("صور ناجحة", r.stats.get("images_ok", 0))
    s3.metric("صور فاشلة", r.stats.get("images_failed", 0))
    id_start = r.id_range.get("start", "—")
    id_end = r.id_range.get("end", "—")
    s4.metric("نطاق Id", f"{id_start} → {id_end}")

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**ملف Excel**")
        st.code(r.excel_path, language=None)
    with p2:
        st.markdown("**مجلد الصور**")
        st.code(r.images_dir, language=None)

    review = getattr(r, "review_report", None) or {}
    if review:
        st.markdown("#### 📋 تقرير المراجعة")
        if review.get("ready_for_import"):
            st.success("✅ الملف جاهز للاستيراد — لا توجد تحذيرات.")
        counts = review.get("counts", {})
        if counts:
            warn_cols = st.columns(min(len(counts), 4))
            labels = {
                "default_unit": "وحدة افتراضية",
                "ambiguous_unit": "وحدة غامضة",
                "missing_brand": "بدون علامة",
                "missing_price": "بدون سعر",
                "failed_image": "صورة فاشلة",
                "category_rule_applied": "تصنيف من قاعدة",
                "category_rule_conflict": "تعارض قواعد",
            }
            for idx, (key, value) in enumerate(counts.items()):
                warn_cols[idx % len(warn_cols)].metric(labels.get(key, key), value)
        items = review.get("items", [])
        if items:
            with st.expander(f"منتجات تحتاج مراجعة ({len(items)})", expanded=True):
                st.dataframe(
                    [
                        {
                            "Id": item.get("product_id"),
                            "الاسم": item.get("name", "")[:50],
                            "تحذيرات": ", ".join(item.get("warnings", [])),
                            "UnitId": item.get("unit_id"),
                            "BrandId": item.get("brand_id") or "—",
                        }
                        for item in items[:100]
                    ],
                    hide_index=True,
                    width="stretch",
                )
        stats = review.get("mapping_stats", {})
        if stats:
            m1, m2, m3 = st.columns(3)
            m1.metric("استنتاج وحدات %", stats.get("inferred_pct", 0))
            m2.metric("وحدة افتراضية %", stats.get("default_pct", 0))
            m3.metric("بدون علامة %", stats.get("missing_brand_pct", 0))

    with st.expander("تفاصيل JSON", expanded=False):
        st.json(
            {
                "run_key": r.run_key,
                "id_range": r.id_range,
                "stats": r.stats,
                "mapping_stats": getattr(r, "mapping_stats", {}),
                "review_counts": review.get("counts", {}),
            }
        )

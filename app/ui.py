"""واجهة Streamlit لاختيار الموديل والتصنيف وتشغيل السحب."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from pipeline import catalog
from pipeline.constants import CATALOG_FILES

importlib.reload(catalog)
from pipeline.errors import PipelineError
from pipeline.runner import CategoryRunRequest, run_category_job

# ── إعداد الصفحة ──────────────────────────────────────────────
st.set_page_config(
    page_title="تصدير المنتجات",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

    :root {
        --bg-white: #ffffff;
        --bg-soft: #f7f9f8;
        --text-dark: #0f1f17;
        --text-muted: #3d5247;
        --green: #0d5c3d;
        --green-light: #e8f5ee;
        --border: #d4e4da;
    }

    /* ── خلفية بيضاء وتباين عالٍ ── */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-white) !important;
        color: var(--text-dark) !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    .block-container {
        padding-top: 1.25rem;
        max-width: 1180px;
        background: var(--bg-white);
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

    /* ترتيب الأعمدة: يمين ← يسار */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row-reverse !important;
        gap: 1.5rem;
    }

    /* حقول إدخال بيضاء وحدود واضحة */
    input, textarea, [data-baseweb="select"] > div,
    div[data-testid="stNumberInput"] input {
        background: var(--bg-white) !important;
        color: var(--text-dark) !important;
        border-color: var(--border) !important;
        text-align: right !important;
        direction: rtl !important;
    }
    label, .stSelectbox label, .stTextInput label {
        color: var(--text-dark) !important;
        font-weight: 600 !important;
    }

    /* الترويسة — أخضر غامق ونص أبيض (تباين عالٍ) */
    .hero {
        background: linear-gradient(120deg, #064a2f 0%, #0d5c3d 50%, #127a50 100%);
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.25rem;
        color: #ffffff !important;
        box-shadow: 0 6px 20px rgba(6, 74, 47, 0.22);
        text-align: right !important;
        direction: rtl !important;
    }
    .hero h1 {
        margin: 0 0 0.3rem 0;
        font-size: 1.75rem;
        font-weight: 800;
        color: #ffffff !important;
    }
    .hero p {
        margin: 0;
        color: #f0fff7 !important;
        font-size: 0.98rem;
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
        background: var(--green) !important;
        color: #ffffff !important;
        border: 2px solid #064a2f !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
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

    /* إخفاء شريط streamlit العلوي الافتراضي إن أمكن */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

if "progress_log" not in st.session_state:
    st.session_state.progress_log = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

_DEFAULT_MODULE_ID = 3  # سوبر ماركت


def _modules_default_first(modules: list) -> list:
    preferred = [m for m in modules if m.module_id == _DEFAULT_MODULE_ID]
    others = sorted(
        (m for m in modules if m.module_id != _DEFAULT_MODULE_ID),
        key=lambda m: m.module_id,
    )
    return preferred + others


def _progress_log(phase: str, current: int, total: int, message: str):
    st.session_state.progress_log.append(f"[{phase}] {current}/{total}: {message}")


# ── الشريط الجانبي ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 خطوات العمل")
    st.markdown(
        """
1. **ارفع ملفات Excel** من الأسفل  
2. اختر **الموديل** والتصنيف (من الملفات المحلية)  
3. أدخل **رابط المصدر**  
4. اضغط **بدء السحب**
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

    if st.button("🔄 تحديث الكتالوج", use_container_width=True):
        catalog.clear_cache()
        st.rerun()
    st.divider()
    st.markdown("### 📁 المخرجات")
    st.caption("Excel + صور WebP في مجلد `output/`")
    st.caption("معرفات عالمية متصلة عبر التصنيفات")

# ── الترويسة ──────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <h1>🛒 نظام تصدير المنتجات</h1>
  <p>سحب تصنيفاً بتصنيف — Excel جاهز للاستيراد + صور WebP مضغوطة</p>
</div>
""",
    unsafe_allow_html=True,
)

# العمود الأول في الكود = يمين الشاشة (مع row-reverse)
col_cat, col_scrape = st.columns([1, 1], gap="large")

with col_cat:
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
                use_container_width=True,
            )
    else:
        st.error(
            f"لا توجد وحدات للموديل {module_id} — تأكد من وجود `catalog/units.xlsx` "
            f"(عمود ModuleId = {module_id})"
        )

with col_scrape:
    st.markdown('<div class="panel-title">⚙️ إعدادات السحب</div>', unsafe_allow_html=True)

    source_url = st.text_input("🔗 رابط المصدر", value=sub.default_source_url)
    c_right, c_left = st.columns(2)
    with c_right:
        output_dir = st.text_input("📂 مجلد الإخراج", value="output")
        excel_filename = st.text_input("📊 ملف Excel", value=sub.excel_filename)
    with c_left:
        images_folder = st.text_input("🖼️ مجلد الصور", value=sub.images_folder)
        max_pages = st.number_input("صفحات (0 = الكل)", min_value=0, value=0, step=1)

    rescrape = st.checkbox("🔄 إعادة سحب — استبدال نفس نطاق المعرفات", value=False)

    st.markdown(
        f'<p style="color:#5a7a65;font-size:0.85rem;margin:0.5rem 0;">'
        f'المسار: <code>{output_dir}/{sub.output_slug}/</code></p>',
        unsafe_allow_html=True,
    )

    start_disabled = not units
    if st.button("🚀 بدء السحب", type="primary", disabled=start_disabled, use_container_width=True):
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
                max_pages=int(max_pages),
                rescrape=rescrape,
            )
            with st.spinner("⏳ جاري السحب وتحميل الصور..."):
                result = run_category_job(request, on_progress=_progress_log)
            st.session_state.last_result = result
            st.balloons()
            st.success(
                f"✅ اكتمل — {result.stats['products_total']} منتج | "
                f"🖼️ {result.stats['images_ok']} صورة ناجحة"
            )
        except PipelineError as exc:
            st.error(f"❌ {exc.code}: {exc}")
        except Exception as exc:
            st.error(f"❌ {exc}")

# ── السجل والنتائج ────────────────────────────────────────────
if st.session_state.progress_log:
    with st.expander("📜 سجل التقدم", expanded=False):
        log_html = "<br>".join(st.session_state.progress_log[-40:])
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

if st.session_state.last_result:
    r = st.session_state.last_result
    st.markdown("---")
    st.markdown("### 📦 آخر عملية سحب")

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

    with st.expander("تفاصيل JSON", expanded=False):
        st.json(
            {
                "run_key": r.run_key,
                "id_range": r.id_range,
                "stats": r.stats,
            }
        )

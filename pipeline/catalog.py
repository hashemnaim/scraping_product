"""تحميل كتالوج الموديلات والتصنيفات والوحدات من ملفات Excel."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import openpyxl

from pipeline.constants import CATALOG_FILES
from pipeline.errors import CATALOG_INVALID, PipelineError, UNITS_MISSING

from pipeline.paths import catalog_dir, project_root


def _catalog_dir() -> Path:
    return catalog_dir()


def _modules_xlsx() -> Path:
    return _catalog_dir() / "modules.xlsx"


def _categories_xlsx() -> Path:
    return _catalog_dir() / "categories.xlsx"


def _subcategories_xlsx() -> Path:
    return _catalog_dir() / "subcategories.xlsx"


def _units_xlsx() -> Path:
    return _catalog_dir() / "units.xlsx"


@dataclass
class Module:
    module_id: int
    name_ar: str
    active: bool
    import_defaults: dict


@dataclass
class SubCategory:
    sub_category_id: int
    name_ar: str
    category_id: int
    module_id: int
    default_source_url: str
    output_slug: str
    excel_filename: str
    images_folder: str


@dataclass
class Category:
    category_id: int
    name_ar: str
    module_id: int
    subcategories: list[SubCategory]


@dataclass
class Unit:
    module_id: int
    unit_id: int
    name_ar: str
    aliases: list[str]


@dataclass
class CategoryMappingRule:
    module_id: int
    pattern: str
    sub_category_id: int
    priority: int = 0
    active: bool = True
    match_mode: str = "contains"


def _category_mapping_rules_xlsx() -> Path:
    return _catalog_dir() / "category_mapping_rules.xlsx"


def clear_cache() -> None:
    """إعادة تحميل ملفات Excel بعد تعديلها."""
    _load_modules.cache_clear()
    _load_split_catalog.cache_clear()
    _load_category_rows.cache_clear()
    _load_subcategory_rows.cache_clear()
    _load_all_units.cache_clear()
    _load_category_mapping_rules.cache_clear()


def save_catalog_file(filename: str, content: bytes) -> Path:
    """حفظ ملف كتالوج مرفوع من الواجهة إلى catalog/."""
    if filename not in CATALOG_FILES:
        raise ValueError(f"ملف غير مدعوم: {filename}")
    _catalog_dir().mkdir(parents=True, exist_ok=True)
    path = _catalog_dir() / filename
    path.write_bytes(content)
    clear_cache()
    return path


def read_catalog_file(filename: str) -> bytes | None:
    path = _catalog_dir() / filename
    if path.exists():
        return path.read_bytes()
    return None


def _cell_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _cell_bool(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) != 0
    return _cell_str(value).lower() in {"1", "true", "yes", "نعم", "نشط", "active"}


def _normalize_key(value) -> str:
    text = _cell_str(value).lower()
    for ch in (" ", "_", "-", "\u200f", "\u200e"):
        text = text.replace(ch, "")
    return text


def _safe_int(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = _cell_str(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _read_xlsx_all(path: Path) -> list[tuple]:
    if not path.exists():
        return []
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows = [row for row in sheet.iter_rows(values_only=True)]
    workbook.close()
    return rows


def _find_column_map(header_row: tuple, field_aliases: dict[str, tuple[str, ...]]) -> dict[str, int]:
    col_map: dict[str, int] = {}
    for field, aliases in field_aliases.items():
        normalized = {_normalize_key(alias) for alias in aliases}
        for idx, cell in enumerate(header_row):
            if _normalize_key(cell) in normalized:
                col_map[field] = idx
                break
    return col_map


def _extract_mapped_rows(
    path: Path,
    field_aliases: dict[str, tuple[str, ...]],
    required_fields: tuple[str, ...],
) -> list[dict[str, object]]:
    """قراءة Excel مع اكتشاف صف العناوين وتخطي صفوف التصفية/العناوين الوصفية."""
    all_rows = _read_xlsx_all(path)
    if not all_rows:
        return []

    for i, row in enumerate(all_rows):
        if not row:
            continue
        col_map = _find_column_map(row, field_aliases)
        if not all(field in col_map for field in required_fields):
            continue

        records: list[dict[str, object]] = []
        for data_row in all_rows[i + 1 :]:
            if not data_row or all(c is None or _cell_str(c) == "" for c in data_row):
                continue
            record = {
                field: data_row[idx] if idx < len(data_row) else None
                for field, idx in col_map.items()
            }
            records.append(record)
        return records

    return []


MODULE_FIELD_ALIASES = {
    "module_id": ("ModuleId", "Module id", "module id", "id"),
    "name_ar": ("NameAr", "الاسم", "name", "module_name"),
    "active": ("Active", "الحالة", "Status", "status"),
    "stock": ("Stock", "stock"),
    "status": ("Status", "status"),
    "is_default": ("IsDefaultProduct",),
    "is_basic": ("IsBasic",),
}

CATEGORY_FIELD_ALIASES = {
    "module_id": ("ModuleId", "Module id", "module id"),
    "module_name": ("الوحدة", "ModuleName", "module name", "Business Module type"),
    "category_id": ("CategoryId", "Category id", "category id", "معرف التصنيف"),
    "name_ar": ("NameAr", "الاسم", "name", "اسم التصنيف"),
}

FLAT_CATEGORY_FIELD_ALIASES = {
    "item_id": ("id", "معرف التصنيف", "categoryid"),
    "name_ar": ("name", "NameAr", "الاسم", "اسم التصنيف"),
    "parent_id": ("parent_id", "ParentId", "parent id"),
    "module_id": ("module_id", "ModuleId", "Module id"),
    "module_name": ("الوحدة", "ModuleName", "module name"),
    "slug": ("slug", "Slug", "OutputSlug"),
}

SUBCATEGORY_FIELD_ALIASES = {
    "module_id": ("ModuleId", "Module id", "module id"),
    "category_id": ("CategoryId", "Category id", "category id", "parent_id", "ParentId"),
    "sub_category_id": ("SubCategoryId", "Sub Category id", "sub category id", "id"),
    "name_ar": ("NameAr", "الاسم", "name"),
    "default_source_url": ("DefaultSourceUrl", "Default Source Url"),
    "output_slug": ("OutputSlug", "Output Slug", "slug", "Slug"),
    "excel_filename": ("ExcelFilename", "Excel Filename"),
    "images_folder": ("ImagesFolder", "Images Folder"),
}

UNIT_FIELD_ALIASES = {
    "module_id": ("ModuleId", "Module id", "module id"),
    "unit_id": ("UnitId", "Unit id", "unit id", "المعرف", "id"),
    "name_ar": ("NameAr", "الاسم", "name", "الوحدة", "unit"),
    "aliases": ("Aliases", "aliases"),
}

CATEGORY_RULE_FIELD_ALIASES = {
    "module_id": ("ModuleId", "Module id", "module id"),
    "pattern": ("Pattern", "pattern", "النمط", "نص"),
    "sub_category_id": ("SubCategoryId", "Sub Category id", "sub_category_id"),
    "priority": ("Priority", "priority", "الأولوية"),
    "active": ("Active", "active", "نشط"),
    "match_mode": ("MatchMode", "match_mode", "وضع المطابقة"),
}


def _module_name_to_id_map() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for module in _load_modules():
        if module.name_ar:
            mapping[module.name_ar.strip()] = module.module_id
    return mapping


def _slug_or_default(slug: str, item_id: int) -> str:
    text = slug.strip()
    if text and text.lower() not in {"null", "none"}:
        return text
    return f"sub-{item_id}"


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _record_to_subcategory(record: dict[str, object]) -> SubCategory | None:
    module_id = _safe_int(record.get("module_id"))
    category_id = _safe_int(record.get("category_id"))
    sub_category_id = _safe_int(record.get("sub_category_id"))
    if module_id is None or category_id is None or sub_category_id is None:
        return None
    slug = _slug_or_default(_cell_str(record.get("output_slug")), sub_category_id)
    excel_name = _cell_str(record.get("excel_filename")) or f"{slug}.xlsx"
    return SubCategory(
        sub_category_id,
        _cell_str(record.get("name_ar")),
        category_id,
        module_id,
        _cell_str(record.get("default_source_url")),
        slug,
        excel_name,
        _cell_str(record.get("images_folder")) or "product_images",
    )


def _seed_category_meta() -> dict[int, dict]:
    seed_path = _catalog_dir() / "seeds" / "admin_catalog.json"
    if not seed_path.exists():
        return {}
    data = _load_json(seed_path)
    meta: dict[int, dict] = {}
    for item in data.get("categories", []):
        item_id = int(item["id"])
        meta[item_id] = {
            "parent_id": 0,
            "module_id": int(item.get("module_id") or 0),
            "slug": item.get("slug") or "",
            "name_ar": item.get("name", ""),
        }
    for item in data.get("subcategories", []):
        item_id = int(item["id"])
        meta[item_id] = {
            "parent_id": int(item.get("parent_id") or 0),
            "module_id": int(item.get("module_id") or 0),
            "slug": item.get("slug") or "",
            "name_ar": item.get("name", ""),
        }
    return meta


def _resolve_row_module_id(
    record: dict[str, object],
    parent_id: int,
    parent_module_map: dict[int, int],
    module_name_map: dict[str, int],
) -> int | None:
    module_id = _safe_int(record.get("module_id"))
    if module_id not in (None, 0):
        return module_id
    if parent_id > 0:
        parent_module = parent_module_map.get(parent_id)
        if parent_module not in (None, 0):
            return parent_module
    seed = _seed_category_meta().get(_safe_int(record.get("item_id")) or -1, {})
    seed_module = seed.get("module_id")
    if seed_module not in (None, 0):
        return int(seed_module)
    module_name = _cell_str(record.get("module_name"))
    if module_name:
        return module_name_map.get(module_name)
    return None


def _records_to_split_catalog(
    records: list[dict[str, object]],
    parent_module_map: dict[int, int] | None = None,
) -> tuple[list[tuple[int, int, str]], list[SubCategory]]:
    module_name_map = _module_name_to_id_map()
    seed_meta = _seed_category_meta()
    parent_module_map = dict(parent_module_map or {})

    normalized: list[dict[str, object]] = []
    for record in records:
        item_id = _safe_int(record.get("item_id"))
        if item_id is None:
            continue
        parent_id = _safe_int(record.get("parent_id"))
        if parent_id is None:
            parent_id = seed_meta.get(item_id, {}).get("parent_id", 0)
        name_ar = _cell_str(record.get("name_ar")) or seed_meta.get(item_id, {}).get("name_ar", "")
        slug = _cell_str(record.get("slug")) or _cell_str(seed_meta.get(item_id, {}).get("slug", ""))
        normalized.append(
            {
                "item_id": item_id,
                "parent_id": parent_id,
                "name_ar": name_ar,
                "slug": slug,
                "module_id": record.get("module_id"),
                "module_name": record.get("module_name"),
            }
        )

    for record in normalized:
        if int(record["parent_id"]) != 0:
            continue
        module_id = _resolve_row_module_id(record, 0, parent_module_map, module_name_map)
        if module_id not in (None, 0):
            parent_module_map[int(record["item_id"])] = module_id

    main_rows: list[tuple[int, int, str]] = []
    subs: list[SubCategory] = []
    for record in normalized:
        item_id = int(record["item_id"])
        parent_id = int(record["parent_id"])
        module_id = _resolve_row_module_id(record, parent_id, parent_module_map, module_name_map)
        if module_id is None or module_id == 0:
            continue
        name_ar = _cell_str(record.get("name_ar"))
        if parent_id == 0:
            parent_module_map[item_id] = module_id
            main_rows.append((module_id, item_id, name_ar))
        else:
            slug = _slug_or_default(_cell_str(record.get("slug")), item_id)
            subs.append(
                SubCategory(
                    item_id,
                    name_ar,
                    parent_id,
                    module_id,
                    "",
                    slug,
                    f"{slug}.xlsx",
                    "product_images",
                )
            )
    return main_rows, subs


def _extract_flat_records(path: Path, file_role: str) -> list[dict[str, object]]:
    """file_role: categories = رئيسي فقط | subcategories = فرعي فقط."""
    if not path.exists():
        return []

    records = _extract_mapped_rows(path, FLAT_CATEGORY_FIELD_ALIASES, ("item_id",))
    if records and any(_safe_int(r.get("parent_id")) is not None for r in records):
        flat_records: list[dict[str, object]] = []
        for record in records:
            parent_id = _safe_int(record.get("parent_id")) or 0
            if file_role == "categories" and parent_id != 0:
                continue
            if file_role == "subcategories" and parent_id == 0:
                continue
            flat_records.append(record)
        return flat_records

    admin_records = _extract_mapped_rows(path, CATEGORY_FIELD_ALIASES, ("category_id",))
    if not admin_records:
        return []

    seed_meta = _seed_category_meta()
    flat_records = []
    for record in admin_records:
        item_id = _safe_int(record.get("category_id"))
        if item_id is None:
            continue
        seed = seed_meta.get(item_id, {})
        parent_id = int(seed.get("parent_id") or 0)

        if file_role == "categories":
            if parent_id != 0:
                continue
            parent_id = 0
        else:
            if parent_id == 0:
                continue

        flat_records.append(
            {
                "item_id": item_id,
                "name_ar": _cell_str(record.get("name_ar")) or seed.get("name_ar", ""),
                "parent_id": parent_id,
                "module_id": seed.get("module_id") or None,
                "module_name": record.get("module_name"),
                "slug": seed.get("slug", ""),
            }
        )
    return flat_records


def _load_internal_category_rows() -> list[tuple[int, int, str]]:
    records = _extract_mapped_rows(_categories_xlsx(), CATEGORY_FIELD_ALIASES, ("category_id",))
    if not records:
        return []
    module_name_map = _module_name_to_id_map()
    result = []
    for record in records:
        category_id = _safe_int(record.get("category_id"))
        if category_id is None:
            continue
        module_id = _safe_int(record.get("module_id"))
        if module_id in (None, 0):
            module_name = _cell_str(record.get("module_name"))
            module_id = module_name_map.get(module_name)
        if module_id is None:
            continue
        result.append((module_id, category_id, _cell_str(record.get("name_ar"))))
    return result


def _load_internal_subcategory_rows() -> list[SubCategory]:
    records = _extract_mapped_rows(
        _subcategories_xlsx(),
        SUBCATEGORY_FIELD_ALIASES,
        ("module_id", "category_id", "sub_category_id"),
    )
    subs: list[SubCategory] = []
    for record in records:
        sub = _record_to_subcategory(record)
        if sub:
            subs.append(sub)
    return subs


def _ensure_parent_mains(
    main_rows: list[tuple[int, int, str]],
    subs: list[SubCategory],
) -> list[tuple[int, int, str]]:
    """أضف التصنيفات الرئيسية الناقصة التي يُشار إليها من الفرعية."""
    main_ids = {cat_id for _, cat_id, _ in main_rows}
    seed_meta = _seed_category_meta()
    extras: list[tuple[int, int, str]] = []
    for sub in subs:
        if sub.category_id in main_ids:
            continue
        parent = seed_meta.get(sub.category_id)
        if not parent or parent.get("parent_id", 0) != 0:
            continue
        module_id = parent.get("module_id") or sub.module_id
        if module_id in (None, 0):
            continue
        extras.append((int(module_id), sub.category_id, parent.get("name_ar", "")))
        main_ids.add(sub.category_id)
    if extras:
        main_rows = main_rows + extras
    return main_rows


def _merge_catalog_from_excel() -> tuple[list[tuple[int, int, str]], list[SubCategory]] | None:
    main_rows: list[tuple[int, int, str]] = []
    subs: list[SubCategory] = []

    if _categories_xlsx().exists():
        internal = _load_internal_category_rows()
        if internal and not _extract_flat_records(_categories_xlsx(), "categories"):
            main_rows.extend(internal)
        else:
            cat_records = _extract_flat_records(_categories_xlsx(), "categories")
            if cat_records:
                rows, _ = _records_to_split_catalog(cat_records)
                main_rows.extend(rows)

    if _subcategories_xlsx().exists():
        internal_subs = _load_internal_subcategory_rows()
        flat_subs = _extract_flat_records(_subcategories_xlsx(), "subcategories")
        if internal_subs and not flat_subs:
            subs.extend(internal_subs)
        elif flat_subs:
            parent_map = {cat_id: mod_id for mod_id, cat_id, _ in main_rows}
            _, sub_rows = _records_to_split_catalog(flat_subs, parent_map)
            subs.extend(sub_rows)

    if not main_rows and not subs:
        return None

    main_rows = _ensure_parent_mains(main_rows, subs)
    return main_rows, subs


def _split_flat_categories(path: Path) -> tuple[list[tuple[int, int, str]], list[SubCategory]] | None:
    records = _extract_flat_records(path, "categories")
    if not records:
        return None
    main_rows, subs = _records_to_split_catalog(records)
    if main_rows or subs:
        return main_rows, subs
    return None


@lru_cache(maxsize=1)
def _load_modules() -> list[Module]:
    records = _extract_mapped_rows(_modules_xlsx(), MODULE_FIELD_ALIASES, ("module_id",))
    modules: list[Module] = []

    if records:
        for record in records:
            module_id = _safe_int(record.get("module_id"))
            if module_id is None:
                continue
            name_ar = _cell_str(record.get("name_ar"))
            active = _cell_bool(record.get("active")) if record.get("active") is not None else True
            stock = _safe_int(record.get("stock")) or 100
            status = _safe_int(record.get("status")) or 1
            is_default = _safe_int(record.get("is_default")) or 1
            is_basic = _safe_int(record.get("is_basic")) or 1
            modules.append(
                Module(
                    module_id,
                    name_ar,
                    active,
                    {
                        "Stock": stock,
                        "Status": status,
                        "IsDefaultProduct": is_default,
                        "IsBasic": is_basic,
                        "ModuleId": module_id,
                    },
                )
            )
        return modules

    if _modules_xlsx().exists():
        return modules

    json_path = _catalog_dir() / "modules.json"
    if not json_path.exists():
        return modules

    # fallback JSON
    for item in _load_json(json_path).get("modules", []):
        modules.append(
            Module(
                int(item["module_id"]),
                item.get("name_ar", ""),
                bool(item.get("active", False)),
                dict(item.get("import_defaults", {"ModuleId": item["module_id"]})),
            )
        )
    return modules


@lru_cache(maxsize=1)
def _load_split_catalog() -> tuple[list[tuple[int, int, str]], list[SubCategory]]:
    merged = _merge_catalog_from_excel()
    if merged:
        return merged
    return [], []


@lru_cache(maxsize=1)
def _load_category_rows() -> list[tuple[int, int, str]]:
    merged_main, _ = _load_split_catalog()
    if merged_main:
        return merged_main

    if _categories_xlsx().exists():
        flat = _split_flat_categories(_categories_xlsx())
        if flat and flat[0]:
            return flat[0]

    records = _extract_mapped_rows(
        _categories_xlsx(), CATEGORY_FIELD_ALIASES, ("category_id",)
    )
    if records:
        module_name_map = _module_name_to_id_map()
        result = []
        for record in records:
            category_id = _safe_int(record.get("category_id"))
            if category_id is None:
                continue
            module_id = _safe_int(record.get("module_id"))
            if module_id in (None, 0):
                module_name = _cell_str(record.get("module_name"))
                module_id = module_name_map.get(module_name)
            if module_id is None:
                continue
            result.append((module_id, category_id, _cell_str(record.get("name_ar"))))
        if result:
            return result

    if _categories_xlsx().exists():
        return []

    json_path = _catalog_dir() / "categories.json"
    if not json_path.exists():
        return []

    result = []
    for item in _load_json(json_path).get("categories", []):
        result.append((int(item["module_id"]), int(item["category_id"]), item.get("name_ar", "")))
    return result


@lru_cache(maxsize=1)
def _load_subcategory_rows() -> list[SubCategory]:
    _, merged_subs = _load_split_catalog()
    if merged_subs:
        return merged_subs

    if _subcategories_xlsx().exists():
        flat_subs = _extract_flat_records(_subcategories_xlsx(), "subcategories")
        if flat_subs:
            _, sub_rows = _records_to_split_catalog(flat_subs)
            return sub_rows

        records = _extract_mapped_rows(
            _subcategories_xlsx(),
            SUBCATEGORY_FIELD_ALIASES,
            ("module_id", "category_id", "sub_category_id"),
        )
        if records:
            subs = []
            for record in records:
                sub = _record_to_subcategory(record)
                if sub:
                    subs.append(sub)
            return subs

    if _subcategories_xlsx().exists():
        return []

    json_path = _catalog_dir() / "categories.json"
    if not json_path.exists():
        return []

    subs: list[SubCategory] = []
    for item in _load_json(json_path).get("categories", []):
        module_id = int(item["module_id"])
        category_id = int(item["category_id"])
        for sub in item.get("subcategories", []):
            subs.append(
                SubCategory(
                    int(sub["sub_category_id"]),
                    sub.get("name_ar", ""),
                    category_id,
                    module_id,
                    sub.get("default_source_url", ""),
                    sub.get("output_slug", ""),
                    sub.get("excel_filename", "products.xlsx"),
                    sub.get("images_folder", "product_images"),
                )
            )
    return subs


@lru_cache(maxsize=1)
def _load_all_units() -> list[Unit]:
    records = _extract_mapped_rows(_units_xlsx(), UNIT_FIELD_ALIASES, ("unit_id",))
    if records:
        units: list[Unit] = []
        for record in records:
            unit_id = _safe_int(record.get("unit_id"))
            if unit_id is None:
                continue
            name_ar = _cell_str(record.get("name_ar"))
            aliases_raw = _cell_str(record.get("aliases"))
            aliases = [part.strip() for part in aliases_raw.split(",") if part.strip()]
            module_id = _safe_int(record.get("module_id"))
            target_modules = [module_id] if module_id is not None else []
            if not target_modules:
                continue
            for mid in target_modules:
                units.append(Unit(mid, unit_id, name_ar, aliases))
        return units

    if _units_xlsx().exists():
        return []

    path = _catalog_dir() / "units.seed.json"
    if path.exists():
        data = _load_json(path).get("units", [])
        return [
            Unit(
                int(item["module_id"]),
                int(item["unit_id"]),
                item.get("name_ar", ""),
                list(item.get("aliases", [])),
            )
            for item in data
        ]
    return []


@lru_cache(maxsize=8)
def _load_category_mapping_rules(module_id: int | None = None) -> list[CategoryMappingRule]:
    records = _extract_mapped_rows(
        _category_mapping_rules_xlsx(),
        CATEGORY_RULE_FIELD_ALIASES,
        ("pattern", "sub_category_id"),
    )
    rules: list[CategoryMappingRule] = []
    for record in records:
        pattern = _cell_str(record.get("pattern"))
        sub_id = _safe_int(record.get("sub_category_id"))
        if not pattern or sub_id is None:
            continue
        row_module = _safe_int(record.get("module_id"))
        if module_id is not None and row_module is not None and row_module != module_id:
            continue
        if module_id is not None and row_module is None:
            continue
        active_raw = record.get("active")
        active = True
        if active_raw is not None:
            text = _cell_str(active_raw).lower()
            if text in ("0", "false", "no", "لا"):
                active = False
        priority = _safe_int(record.get("priority")) or 0
        match_mode = _cell_str(record.get("match_mode")).lower() or "contains"
        if match_mode not in ("contains", "equals"):
            match_mode = "contains"
        rules.append(
            CategoryMappingRule(
                module_id=row_module or (module_id or 0),
                pattern=pattern,
                sub_category_id=sub_id,
                priority=priority,
                active=active,
                match_mode=match_mode,
            )
        )
    rules.sort(key=lambda rule: (rule.priority, len(rule.pattern)), reverse=True)
    return rules


def load_category_mapping_rules(module_id: int) -> list[CategoryMappingRule]:
    return _load_category_mapping_rules(module_id)


def catalog_sources() -> dict[str, bool]:
    """أي ملفات Excel موجودة."""
    return {
        "modules.xlsx": _modules_xlsx().exists(),
        "categories.xlsx": _categories_xlsx().exists(),
        "subcategories.xlsx": _subcategories_xlsx().exists(),
        "units.xlsx": _units_xlsx().exists(),
        "category_mapping_rules.xlsx": _category_mapping_rules_xlsx().exists(),
    }


def list_modules() -> list[Module]:
    return [m for m in _load_modules() if m.active]


def get_module(module_id: int) -> Module:
    for module in list_modules():
        if module.module_id == module_id:
            return module
    raise PipelineError(CATALOG_INVALID, f"الموديل {module_id} غير موجود أو غير نشط")


def list_categories(module_id: int) -> list[Category]:
    sub_by_key: dict[tuple[int, int], list[SubCategory]] = {}
    for sub in _load_subcategory_rows():
        if sub.module_id != module_id:
            continue
        sub_by_key.setdefault((sub.module_id, sub.category_id), []).append(sub)

    categories = []
    seen: set[int] = set()
    for mod_id, cat_id, name_ar in _load_category_rows():
        if mod_id != module_id:
            continue
        seen.add(cat_id)
        categories.append(
            Category(cat_id, name_ar, module_id, sub_by_key.get((module_id, cat_id), []))
        )

    for (mod_id, cat_id), subs in sub_by_key.items():
        if mod_id != module_id or cat_id in seen:
            continue
        label = subs[0].name_ar if subs else f"تصنيف {cat_id}"
        categories.append(Category(cat_id, label, module_id, subs))

    categories.sort(key=lambda c: c.category_id)
    return categories


def list_subcategories(module_id: int, category_id: int) -> list[SubCategory]:
    for category in list_categories(module_id):
        if category.category_id == category_id:
            return category.subcategories
    return []


def get_category(module_id: int, category_id: int) -> Category:
    for category in list_categories(module_id):
        if category.category_id == category_id:
            return category
    raise PipelineError(
        CATALOG_INVALID,
        f"التصنيف {category_id} غير موجود للموديل {module_id}",
    )


def module_uses_flat_categories(module_id: int) -> bool:
    """موديل بدون تصنيفات فرعية — التصنيف الرئيسي يكفي للسحب."""
    categories = list_categories(module_id)
    return bool(categories) and all(not cat.subcategories for cat in categories)


def category_as_run_target(category: Category) -> SubCategory:
    """حوّل تصنيفاً رئيسياً (بدون فرعي) إلى هدف سحب."""
    seed = _seed_category_meta().get(category.category_id, {})
    slug = _slug_or_default(_cell_str(seed.get("slug", "")), category.category_id)
    return SubCategory(
        category.category_id,
        category.name_ar,
        category.category_id,
        category.module_id,
        "",
        slug,
        f"{slug}.xlsx",
        "product_images",
    )


def resolve_run_target(
    module_id: int,
    category_id: int,
    sub_category_id: int | None = None,
) -> SubCategory:
    """يُرجع هدف السحب — فرعي إن وُجد، وإلا التصنيف الرئيسي."""
    subs = list_subcategories(module_id, category_id)
    if subs:
        if sub_category_id is None:
            raise PipelineError(
                CATALOG_INVALID,
                f"اختر تصنيفاً فرعياً للموديل {module_id}",
            )
        return get_subcategory(module_id, category_id, sub_category_id)
    return category_as_run_target(get_category(module_id, category_id))


def get_subcategory(module_id: int, category_id: int, sub_category_id: int) -> SubCategory:
    for sub in list_subcategories(module_id, category_id):
        if sub.sub_category_id == sub_category_id:
            return sub
    raise PipelineError(
        CATALOG_INVALID,
        f"التصنيف الفرعي {sub_category_id} غير موجود للموديل {module_id}",
    )


def get_units(module_id: int) -> list[Unit]:
    return [unit for unit in _load_all_units() if unit.module_id == module_id]


def require_units(module_id: int) -> list[Unit]:
    units = get_units(module_id)
    if not units:
        raise PipelineError(
            UNITS_MISSING,
            f"لا توجد وحدات للموديل {module_id} في catalog/units.xlsx",
        )
    return units


def make_run_key(module_id: int, category_id: int, sub_category_id: int) -> str:
    return f"{module_id}/{category_id}/{sub_category_id}"

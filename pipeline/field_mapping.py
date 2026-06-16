"""توثيق مصادر حقول Excel وملخص ما قبل السحب."""

from __future__ import annotations

from pipeline.match_types import FieldSource

FIELD_SOURCES: dict[str, dict[str, str]] = {
    "CategoryId": {
        "label_ar": "التصنيف الرئيسي",
        "source": FieldSource.USER_SELECTION.value,
        "source_ar": "اختيارك في الواجهة",
        "icon": "🏷️",
    },
    "SubCategoryId": {
        "label_ar": "التصنيف الفرعي",
        "source": FieldSource.USER_SELECTION.value,
        "source_ar": "اختيارك في الواجهة",
        "icon": "📂",
    },
    "UnitId": {
        "label_ar": "الوحدة",
        "source": FieldSource.INFERRED_NAME.value,
        "source_ar": "مستنتج من اسم المنتج + كتالوج الوحدات",
        "icon": "⚖️",
    },
    "QuantityUnit": {
        "label_ar": "كمية الوحدة",
        "source": FieldSource.INFERRED_NAME.value,
        "source_ar": "مستنتج من اسم المنتج (مثل 250، 1)",
        "icon": "🔢",
    },
    "BrandId": {
        "label_ar": "العلامة التجارية",
        "source": FieldSource.INFERRED_NAME.value,
        "source_ar": "مستنتج من اسم المنتج + brands.csv",
        "icon": "™️",
    },
    "Name": {
        "label_ar": "الاسم",
        "source": FieldSource.SCRAPED.value,
        "source_ar": "من الموقع مباشرة",
        "icon": "🌐",
    },
    "Price": {
        "label_ar": "السعر",
        "source": FieldSource.SCRAPED.value,
        "source_ar": "من الموقع مباشرة",
        "icon": "💰",
    },
    "Image": {
        "label_ar": "الصورة",
        "source": FieldSource.SCRAPED.value,
        "source_ar": "من الموقع (تُحفظ WebP)",
        "icon": "🖼️",
    },
}

CRITICAL_FIELDS = ("CategoryId", "SubCategoryId", "UnitId", "QuantityUnit", "BrandId")

WORKFLOW_TIP = "رابط واحد = تصنيف فرعي واحد — اختر التصنيف في الواجهة قبل السحب."


def field_source_rows() -> list[dict[str, str]]:
    rows = []
    for field in CRITICAL_FIELDS + ("Name", "Price", "Image"):
        meta = FIELD_SOURCES[field]
        rows.append(
            {
                "field": field,
                "label_ar": meta["label_ar"],
                "source_ar": meta["source_ar"],
                "icon": meta["icon"],
            }
        )
    return rows


def build_pre_scrape_summary(
    module_id: int,
    category_id: int,
    sub_category_id: int,
    category_name: str,
    sub_name: str,
    unit_count: int,
) -> dict:
    return {
        "module_id": module_id,
        "category_id": category_id,
        "sub_category_id": sub_category_id,
        "category_name": category_name,
        "sub_name": sub_name,
        "unit_count": unit_count,
        "workflow_tip": WORKFLOW_TIP,
        "note": (
            "معرفات الموقع المصدر لا تُستخدم في Excel. "
            "التصنيف من اختيارك؛ الوحدة والعلامة من اسم المنتج."
        ),
        "fields": field_source_rows(),
    }

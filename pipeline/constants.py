"""ثوابت التصدير والسحب المشتركة."""

import os

CATALOG_FILES = {
    "modules.xlsx": "الموديلات",
    "categories.xlsx": "التصنيفات الرئيسية (parent_id = 0)",
    "subcategories.xlsx": "التصنيفات الفرعية (parent_id > 0)",
    "units.xlsx": "الوحدات",
}

IMPORT_DEFAULTS = {
    "CategoryId": "",
    "SubCategoryId": "",
    "BrandId": "",
    "UnitId": "",
    "Stock": 100,
    "Discount": 0,
    "DiscountType": "percent",
    "AvailableTimeStarts": "",
    "AvailableTimeEnds": "",
    "Variations": "",
    "ChoiceOptions": "",
    "AddOns": "",
    "Attributes": "",
    "Tags": "",
    "StoreId": "",
    "ModuleId": "1",
    "Status": 1,
    "Veg": 0,
    "Recommended": 0,
    "IsDefaultProduct": 1,
    "IsPrescriptionReq": 0,
    "CommonConditions": "",
    "IsBasic": 1,
    "QuantityUnit": "",
}

EXCEL_COLUMNS = [
    "Id",
    "Name",
    "Description",
    "Image",
    "CategoryId",
    "SubCategoryId",
    "BrandId",
    "UnitId",
    "Stock",
    "Price",
    "Discount",
    "DiscountType",
    "AvailableTimeStarts",
    "AvailableTimeEnds",
    "Variations",
    "ChoiceOptions",
    "AddOns",
    "Attributes",
    "Tags",
    "StoreId",
    "ModuleId",
    "Status",
    "Veg",
    "Recommended",
    "IsDefaultProduct",
    "IsPrescriptionReq",
    "CommonConditions",
    "IsBasic",
    "QuantityUnit",
]

def _instashop_headless() -> bool:
    flag = os.environ.get("INSTASHOP_HEADLESS", "").lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False
    # Streamlit Community Cloud user + servers without display
    return os.getenv("USER") == "appuser" or not os.environ.get("DISPLAY")


SCRAPE_SETTINGS = {
    "delay_between_requests": 1.5,
    "graphql_endpoint": "https://mcprod.seoudisupermarket.com/graphql",
    "graphql_page_size": 20,
    "fetch_descriptions": False,
    "download_full_image": True,
    "webp_quality": 85,
    "instashop_headless": _instashop_headless(),
    "instashop_scroll_pause": 1.5,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

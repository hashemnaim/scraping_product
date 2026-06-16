"""تنسيق سحب المحلات من الخريطة."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pipeline.errors import SCRAPE_FAILED, PipelineError
from pipeline.paths import project_root
from pipeline.places_exporter import write_places_excel
from pipeline.scrape.maps import scrape_maps_places

ProgressCallback = Callable[[str, int, int, str], None]


@dataclass
class MapsRunRequest:
    city: str
    radius_km: float
    categories: list[str]
    district: str = ""
    output_dir: str = "output"
    excel_filename: str = "places.xlsx"


@dataclass
class MapsRunResult:
    status: str
    excel_path: str
    stats: dict = field(default_factory=dict)


def _default_progress(phase: str, current: int, total: int, message: str):
    pass


def run_maps_job(
    request: MapsRunRequest,
    on_progress: ProgressCallback | None = None,
) -> MapsRunResult:
    progress = on_progress or _default_progress
    progress("maps", 0, 1, "جاري سحب المحلات من الخريطة...")

    try:
        places = scrape_maps_places(
            city=request.city,
            radius_km=request.radius_km,
            categories=request.categories,
            district=request.district,
            on_progress=progress,
        )
    except Exception as exc:
        raise PipelineError(SCRAPE_FAILED, str(exc)) from exc

    if not places:
        raise PipelineError(SCRAPE_FAILED, "لم يُعثر على محلات في المنطقة المحددة")

    slug = "-".join(request.city.split())[:40] or "places"
    output_base = project_root() / request.output_dir / f"maps-{slug}"
    output_base.mkdir(parents=True, exist_ok=True)
    excel_path = output_base / request.excel_filename

    rows = []
    for index, place in enumerate(places, start=1):
        rows.append(
            {
                "Id": index,
                "Name": place.get("name", ""),
                "Address": place.get("address", ""),
                "Phone": place.get("phone", ""),
                "Category": place.get("category", ""),
                "City": place.get("city", ""),
                "CoverageKm": place.get("coverage_km", request.radius_km),
                "MapsUrl": place.get("maps_url", ""),
            }
        )

    write_places_excel(rows, excel_path)
    with_phone = sum(1 for row in rows if row.get("Phone"))

    return MapsRunResult(
        status="completed",
        excel_path=str(excel_path),
        stats={
            "places_total": len(rows),
            "with_phone": with_phone,
            "categories": len(request.categories),
        },
    )

import hashlib
import json
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from .config import KrishaDetailsConfig

try:
    from krisha.time_utils import utc_now_iso
except ModuleNotFoundError as error:
    if error.name != "krisha":
        raise

    from ..krisha.time_utils import utc_now_iso


class KrishaDetailsExtractor:
    def __init__(self, config: KrishaDetailsConfig) -> None:
        self.config = config

    def parse_detail_page(
        self,
        html: str,
        detail_url: str,
        source_url: str | None,
        run_id: str,
    ) -> dict[str, Any]:
        window_data = extract_window_data(html)
        return self.normalize_window_data(
            window_data=window_data,
            detail_url=detail_url,
            source_url=source_url,
            run_id=run_id,
        )

    def normalize_window_data(
        self,
        window_data: dict[str, Any],
        detail_url: str,
        source_url: str | None,
        run_id: str,
    ) -> dict[str, Any]:
        advert = window_data.get("advert") or {}

        adverts = window_data.get("adverts") or []
        advert_card = adverts[0] if adverts and isinstance(adverts[0], dict) else {}

        owner = advert_card.get("owner") or {}
        category = advert_card.get("category") or {}
        photo = advert_card.get("photo") or {}
        map_data = advert.get("map") or {}

        title = advert.get("title") or advert_card.get("title")
        description = advert_card.get("description")
        floor, total_floors = parse_floor_from_title(title)
        now = utc_now_iso()

        record = {
            "ad_id": advert.get("id") or advert_card.get("id"),
            "uuid": advert_card.get("uuid"),
            "detail_url": detail_url,
            "source_url": source_url,
            "title": title,
            "description": description,
            "price_kzt": advert.get("price"),
            "price_m2": advert_card.get("priceM2"),
            "status": advert.get("status"),
            "rooms": advert.get("rooms"),
            "area_m2": advert.get("square"),
            "floor": floor,
            "total_floors": total_floors,
            "building_type": parse_building_type(description),
            "building_year": parse_building_year(description),
            "ceiling_height": parse_ceiling_height(description),
            "bathroom": parse_bathroom(description),
            "city": advert_card.get("city"),
            "address": advert_card.get("address"),
            "full_address": advert_card.get("fullAddress"),
            "latitude": map_data.get("lat"),
            "longitude": map_data.get("lon"),
            "owner_name": advert.get("ownerName"),
            "user_type": advert.get("userType"),
            "owner_is_owner": owner.get("isOwner"),
            "owner_is_pro": owner.get("isPro"),
            "owner_is_complex": owner.get("isComplex"),
            "owner_is_builder": owner.get("isBuilder"),
            "category_alias": advert.get("categoryAlias"),
            "category_label": category.get("label"),
            "complex_id": advert.get("complexId"),
            "complex_name": advert.get("complexName"),
            "is_layout": advert_card.get("isLayout"),
            "photo_count": len(advert.get("photos") or []),
            "main_photo_url": photo.get("1x") or photo.get("2x") or photo.get("3x"),
            "created_at_krisha": parse_date(advert_card.get("createdAt")),
            "added_at_krisha": parse_date(advert_card.get("addedAt")),
            "days_in_live": advert_card.get("daysInLive"),
            "run_id": run_id,
            "parser_version": self.config.parser_version,
            "content_hash": "",
            "first_seen_at": now,
            "last_seen_at": now,
            "parsed_at": now,
            "updated_at": now,
            "advert_json": advert,
            "advert_card_json": advert_card,
            "photos_json": advert.get("photos") or [],
        }

        if record["ad_id"] is None:
            raise ValueError("ad_id is missing after normalization")

        record["content_hash"] = make_content_hash(record)
        return record


def extract_window_data(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    script = soup.select_one("script#jsdata")

    if script is None:
        raise ValueError("script#jsdata not found")

    script_text = script.get_text(" ", strip=True)

    match = re.search(
        r"window\.data\s*=\s*(\{.*?\});",
        script_text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError("window.data JSON not found")

    return json.loads(match.group(1))


def parse_date(value: Any) -> str | None:
    if not value or not isinstance(value, str):
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def parse_floor_from_title(title: str | None) -> tuple[int | None, int | None]:
    if not title:
        return None, None

    match = re.search(r"(\d+)\s*/\s*(\d+)\s*этаж", title)

    if not match:
        return None, None

    return int(match.group(1)), int(match.group(2))


def parse_building_year(description: str | None) -> int | None:
    if not description:
        return None

    match = re.search(r"(\d{4})\s*г\.п\.", description)
    return int(match.group(1)) if match else None


def parse_ceiling_height(description: str | None) -> float | None:
    if not description:
        return None

    match = re.search(
        r"потолки\s*([\d.,]+)\s*м",
        description,
        flags=re.IGNORECASE,
    )

    return float(match.group(1).replace(",", ".")) if match else None


def parse_bathroom(description: str | None) -> str | None:
    if not description:
        return None

    match = re.search(
        r"санузел\s+([^,]+)",
        description,
        flags=re.IGNORECASE,
    )

    return match.group(1).strip() if match else None


def parse_building_type(description: str | None) -> str | None:
    if not description:
        return None

    lower_description = description.lower()

    for building_type in ["кирпичный дом", "панельный дом", "монолитный дом"]:
        if building_type in lower_description:
            return building_type

    return None


def make_content_hash(record: dict[str, Any]) -> str:
    important_payload = {
        "title": record.get("title"),
        "description": record.get("description"),
        "price_kzt": record.get("price_kzt"),
        "price_m2": record.get("price_m2"),
        "rooms": record.get("rooms"),
        "area_m2": record.get("area_m2"),
        "floor": record.get("floor"),
        "total_floors": record.get("total_floors"),
        "address": record.get("address"),
        "status": record.get("status"),
    }

    raw = json.dumps(important_payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

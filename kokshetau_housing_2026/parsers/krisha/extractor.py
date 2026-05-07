import hashlib
import json
import re
from typing import Any, Optional

from bs4 import BeautifulSoup, Tag

from .config import KrishaCityConfig
from .time_utils import utc_now_iso


class KrishaCardExtractor:
    def __init__(self, config: KrishaCityConfig) -> None:
        self.config = config

    def parse_listing_page(
        self,
        html: str,
        source_url: str,
        page_number: int,
        run_id: str,
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        listing_section = soup.select_one("section.a-list.a-search-list.a-list-with-favs")

        if listing_section is None:
            return []

        cards = listing_section.select("div.a-card")
        records = []
        position = 0

        for card in cards:
            if not card.get("data-id"):
                continue

            position += 1
            records.append(
                self.parse_card_to_raw_head(
                    card=card,
                    source_url=source_url,
                    page_number=page_number,
                    position_on_page=position,
                    run_id=run_id,
                )
            )

        return records

    def parse_card_to_raw_head(
        self,
        card: Tag,
        source_url: str,
        page_number: int,
        position_on_page: int,
        run_id: str,
    ) -> dict[str, Any]:
        title_tag = card.select_one("a.a-card__title")
        href = title_tag.get("href") if title_tag else None

        title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else None
        price_text = get_text(card, "div.a-card__price")
        address = get_text(card, "div.a-card__subtitle")
        description = get_text(card, "div.a-card__text-preview")

        raw_classes = " ".join(card.get("class", []))
        all_text = get_all_text(card)

        title_parts = extract_title_parts(title)
        description_parts = extract_description_parts(description)
        labels = extract_labels(all_text)
        promotion_flags = extract_promotion_flags(all_text)
        published_date_text = extract_published_date_text(all_text)
        image_data = self.extract_main_image(card)

        now = utc_now_iso()

        record = {
            "ad_id": card.get("data-id"),
            "product_id": card.get("data-product-id"),
            "uuid": card.get("data-uuid"),
            "html_id": card.get("id"),
            "title": title,
            "price_text": price_text,
            "price_kzt": parse_price(price_text),
            "address": address,
            "description": description,
            "url": self.full_url(href),
            "rooms": title_parts["rooms"],
            "area_m2": title_parts["area_m2"],
            "floor": title_parts["floor"],
            "total_floors": title_parts["total_floors"],
            "building_type": description_parts["building_type"],
            "building_year": description_parts["building_year"],
            "ceiling_height": description_parts["ceiling_height"],
            "bathroom": description_parts["bathroom"],
            "residential_complex": description_parts["residential_complex"],
            "labels": labels["labels"],
            "is_specialist": labels["is_specialist"],
            "is_owner": labels["is_owner"],
            "is_new_building": labels["is_new_building"],
            "has_mortgage": labels["has_mortgage"],
            "has_installment": labels["has_installment"],
            "is_urgent": labels["is_urgent"],
            "has_bargain": labels["has_bargain"],
            "is_pledged": labels["is_pledged"],
            "is_visible": "is-visible" in card.get("class", []),
            "is_highlighted": card.find_parent("section", class_="highlighted-section") is not None,
            "is_colored": "not-colored" not in card.get("class", []),
            "has_top_promotion": promotion_flags["has_top_promotion"],
            "has_hot_promotion": promotion_flags["has_hot_promotion"],
            "has_month_promotion": promotion_flags["has_month_promotion"],
            "has_week_promotion": promotion_flags["has_week_promotion"],
            "city": self.config.city_name,
            "published_date_text": published_date_text,
            "main_image_url": image_data["main_image_url"],
            "image_alt": image_data["image_alt"],
            "image_title": image_data["image_title"],
            "photo_count": extract_photo_count(card),
            "complex_url": self.extract_complex_url(card),
            "raw_classes": raw_classes,
            "all_text": all_text,
            "source_url": source_url,
            "page_number": page_number,
            "position_on_page": position_on_page,
            "run_id": run_id,
            "content_hash": "",
            "first_seen_at": now,
            "last_seen_at": now,
            "parsed_at": now,
            "updated_at": now,
        }

        record["content_hash"] = make_content_hash(record)
        return record

    def extract_main_image(self, card: Tag) -> dict[str, Optional[str]]:
        image = card.select_one("img.a-image__img") or card.select_one("img")

        if image is None:
            return {
                "main_image_url": None,
                "image_alt": None,
                "image_title": None,
            }

        src = (
            image.get("src")
            or image.get("data-src")
            or image.get("data-lazy-src")
            or image.get("data-original")
        )

        return {
            "main_image_url": self.full_url(src),
            "image_alt": clean_text(image.get("alt")),
            "image_title": clean_text(image.get("title")),
        }

    def extract_complex_url(self, card: Tag) -> Optional[str]:
        for link in card.select("a[href]"):
            href = link.get("href")
            if href and "/complex/show/" in href:
                return self.full_url(href)

        return None

    def full_url(self, href: Optional[str]) -> Optional[str]:
        if not href:
            return None

        if href.startswith("http"):
            return href

        if href.startswith("//"):
            return "https:" + href

        return self.config.base_url + href


def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def parse_price(price_text: Optional[str]) -> Optional[int]:
    if not price_text:
        return None

    digits = re.sub(r"\D", "", price_text)
    return int(digits) if digits else None


def get_text(card: Tag, selector: str) -> Optional[str]:
    tag = card.select_one(selector)
    return clean_text(tag.get_text(" ", strip=True)) if tag else None


def get_all_text(card: Tag) -> str:
    return clean_text(card.get_text(" ", strip=True)) or ""


def extract_title_parts(title: Optional[str]) -> dict[str, Any]:
    result = {
        "rooms": None,
        "area_m2": None,
        "floor": None,
        "total_floors": None,
    }

    if not title:
        return result

    rooms_match = re.search(r"(\d+)-комнат", title)
    if rooms_match:
        result["rooms"] = int(rooms_match.group(1))

    area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*м²", title)
    if area_match:
        result["area_m2"] = float(area_match.group(1).replace(",", "."))

    floor_match = re.search(r"(\d+)\s*/\s*(\d+)\s*этаж", title)
    if floor_match:
        result["floor"] = int(floor_match.group(1))
        result["total_floors"] = int(floor_match.group(2))

    return result


def extract_description_parts(description: Optional[str]) -> dict[str, Any]:
    result = {
        "building_type": None,
        "building_year": None,
        "ceiling_height": None,
        "bathroom": None,
        "residential_complex": None,
    }

    if not description:
        return result

    desc_lower = description.lower()

    for building_type in ["кирпичный", "монолитный", "панельный"]:
        if building_type in desc_lower:
            result["building_type"] = building_type
            break

    year_match = re.search(r"(\d{4})\s*г\.п\.", description)
    if year_match:
        result["building_year"] = int(year_match.group(1))

    ceiling_match = re.search(
        r"потолки\s*(\d+(?:[.,]\d+)?)\s*м",
        description,
        flags=re.IGNORECASE,
    )
    if ceiling_match:
        result["ceiling_height"] = float(ceiling_match.group(1).replace(",", "."))

    bathroom_match = re.search(
        r"санузел\s*([^,]+)",
        description,
        flags=re.IGNORECASE,
    )
    if bathroom_match:
        result["bathroom"] = clean_text(bathroom_match.group(1))

    complex_match = re.search(
        r"жил\.\s*комплекс\s*([^,]+)",
        description,
        flags=re.IGNORECASE,
    )
    if complex_match:
        result["residential_complex"] = clean_text(complex_match.group(1))

    return result


def extract_labels(all_text: str) -> dict[str, Any]:
    text = all_text.lower()
    labels = []

    checks = {
        "Специалист": "специалист",
        "Хозяин недвижимости": "хозяин недвижимости",
        "Новостройка": "новостройка",
        "Ипотека": "ипотека",
        "Рассрочка": "рассрочка",
        "Срочно": "срочно",
        "Торг": "торг",
        "В залоге": "в залоге",
    }

    for label, keyword in checks.items():
        if keyword in text:
            labels.append(label)

    return {
        "labels": labels,
        "is_specialist": "специалист" in text,
        "is_owner": "хозяин недвижимости" in text,
        "is_new_building": "новостройка" in text,
        "has_mortgage": "ипотека" in text,
        "has_installment": "рассрочка" in text,
        "is_urgent": "срочно" in text,
        "has_bargain": "торг" in text,
        "is_pledged": "в залоге" in text,
    }


def extract_promotion_flags(all_text: str) -> dict[str, bool]:
    text = all_text.lower()

    return {
        "has_top_promotion": "топ объявление" in text,
        "has_hot_promotion": "в горячих" in text,
        "has_month_promotion": "просмотров на месяц" in text,
        "has_week_promotion": "просмотров на неделю" in text,
    }


def extract_published_date_text(all_text: str) -> Optional[str]:
    date_match = re.search(
        r"\b(\d{1,2}\s+"
        r"(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))\b",
        all_text,
        flags=re.IGNORECASE,
    )

    return date_match.group(1) if date_match else None


def extract_photo_count(card: Tag) -> Optional[int]:
    image_block = card.select_one(".a-card__image, .a-card__image-wrapper")

    if image_block:
        numbers = re.findall(r"\b\d{1,2}\b", image_block.get_text(" ", strip=True))
        if numbers:
            return int(numbers[-1])

    return None


def make_content_hash(record: dict[str, Any]) -> str:
    hash_data = {
        "title": record.get("title"),
        "price_kzt": record.get("price_kzt"),
        "address": record.get("address"),
        "description": record.get("description"),
        "labels": record.get("labels"),
        "all_text": record.get("all_text"),
    }

    raw = json.dumps(hash_data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

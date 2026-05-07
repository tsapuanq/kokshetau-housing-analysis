from dataclasses import dataclass


@dataclass(frozen=True)
class KrishaCityConfig:
    city_name: str
    city_slug: str
    source_name: str
    max_pages: int = 1
    base_url: str = "https://krisha.kz"
    min_delay: float = 2.0
    max_delay: float = 5.0
    request_timeout: int = 15

    @property
    def start_url(self) -> str:
        return f"{self.base_url}/prodazha/kvartiry/{self.city_slug}/"


KOKSHETAU_CONFIG = KrishaCityConfig(
    city_name="Кокшетау",
    city_slug="kokshetau",
    source_name="krisha_kokshetau_head",
    max_pages=200,
    min_delay=4.0,
    max_delay=9.0,
)


DDL_COLUMNS = [
    "ad_id",
    "product_id",
    "uuid",
    "html_id",
    "title",
    "price_text",
    "price_kzt",
    "address",
    "description",
    "url",
    "rooms",
    "area_m2",
    "floor",
    "total_floors",
    "building_type",
    "building_year",
    "ceiling_height",
    "bathroom",
    "residential_complex",
    "labels",
    "is_specialist",
    "is_owner",
    "is_new_building",
    "has_mortgage",
    "has_installment",
    "is_urgent",
    "has_bargain",
    "is_pledged",
    "is_visible",
    "is_highlighted",
    "is_colored",
    "has_top_promotion",
    "has_hot_promotion",
    "has_month_promotion",
    "has_week_promotion",
    "city",
    "published_date_text",
    "main_image_url",
    "image_alt",
    "image_title",
    "photo_count",
    "complex_url",
    "raw_classes",
    "all_text",
    "source_url",
    "page_number",
    "position_on_page",
    "run_id",
    "content_hash",
    "first_seen_at",
    "last_seen_at",
    "parsed_at",
    "updated_at",
]

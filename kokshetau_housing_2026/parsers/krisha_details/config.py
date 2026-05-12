from dataclasses import dataclass, field


@dataclass(frozen=True)
class KrishaDetailsConfig:
    source_name: str = "krisha_kokshetau_details"
    source_url: str = "raw_head_krisha"
    detail_urls: tuple[str, ...] = field(default_factory=tuple)
    max_urls: int | None = None
    request_timeout: int = 20
    min_delay: float = 4.0
    max_delay: float = 9.0
    parser_version: str = "v1"
    url_batch_size: int = 500
    existing_ads_batch_size: int = 200
    insert_batch_size: int = 200
    save_batch_size: int = 100


KOKSHETAU_DETAILS_CONFIG = KrishaDetailsConfig()


DETAIL_COLUMNS = [
    "ad_id",
    "uuid",
    "detail_url",
    "source_url",
    "title",
    "description",
    "price_kzt",
    "price_m2",
    "status",
    "rooms",
    "area_m2",
    "floor",
    "total_floors",
    "building_type",
    "building_year",
    "ceiling_height",
    "bathroom",
    "city",
    "address",
    "full_address",
    "latitude",
    "longitude",
    "owner_name",
    "user_type",
    "owner_is_owner",
    "owner_is_pro",
    "owner_is_complex",
    "owner_is_builder",
    "category_alias",
    "category_label",
    "complex_id",
    "complex_name",
    "is_layout",
    "photo_count",
    "main_photo_url",
    "created_at_krisha",
    "added_at_krisha",
    "days_in_live",
    "run_id",
    "parser_version",
    "content_hash",
    "first_seen_at",
    "last_seen_at",
    "parsed_at",
    "updated_at",
    "advert_json",
    "advert_card_json",
    "photos_json",
]

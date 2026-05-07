from typing import Any

from .config import DDL_COLUMNS


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    required_fields = [
        "ad_id",
        "title",
        "price_kzt",
        "url",
        "source_url",
        "page_number",
        "position_on_page",
        "content_hash",
    ]

    seen_ad_ids = set()
    duplicate_ad_ids = []

    for index, record in enumerate(records, start=1):
        for field in required_fields:
            if record.get(field) in (None, "", []):
                issues.append({
                    "row": index,
                    "ad_id": record.get("ad_id"),
                    "field": field,
                    "issue": "missing_required_value",
                })

        ad_id = record.get("ad_id")
        if ad_id in seen_ad_ids:
            duplicate_ad_ids.append(ad_id)
        else:
            seen_ad_ids.add(ad_id)

        if record.get("price_kzt") is not None and record["price_kzt"] <= 0:
            issues.append({
                "row": index,
                "ad_id": ad_id,
                "field": "price_kzt",
                "issue": "price_is_not_positive",
            })

        if record.get("area_m2") is not None and record["area_m2"] <= 0:
            issues.append({
                "row": index,
                "ad_id": ad_id,
                "field": "area_m2",
                "issue": "area_is_not_positive",
            })

        missing_columns = sorted(set(DDL_COLUMNS) - set(record.keys()))
        extra_columns = sorted(set(record.keys()) - set(DDL_COLUMNS))

        if missing_columns or extra_columns:
            issues.append({
                "row": index,
                "ad_id": ad_id,
                "field": "columns",
                "issue": "columns_do_not_match_ddl",
                "missing_columns": missing_columns,
                "extra_columns": extra_columns,
            })

    return {
        "records_count": len(records),
        "unique_ad_ids": len(seen_ad_ids),
        "duplicate_ad_ids": duplicate_ad_ids,
        "issues_count": len(issues),
        "issues": issues,
    }

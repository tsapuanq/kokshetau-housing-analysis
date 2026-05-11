from typing import Any

from .config import DETAIL_COLUMNS


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    required_fields = [
        "ad_id",
        "detail_url",
        "run_id",
        "parser_version",
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

        missing_columns = sorted(set(DETAIL_COLUMNS) - set(record.keys()))
        extra_columns = sorted(set(record.keys()) - set(DETAIL_COLUMNS))

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


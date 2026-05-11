from typing import Any

from supabase import Client

from .config import DETAIL_COLUMNS, KrishaDetailsConfig

try:
    from krisha.storage import get_supabase_client
    from krisha.time_utils import utc_now_iso
except ModuleNotFoundError as error:
    if error.name != "krisha":
        raise

    from ..krisha.storage import get_supabase_client
    from ..krisha.time_utils import utc_now_iso


class KrishaDetailsStorage:
    def __init__(self, supabase: Client, config: KrishaDetailsConfig) -> None:
        self.supabase = supabase
        self.config = config

    def create_parse_run(self, run_id: str, pages_requested: int) -> None:
        payload = {
            "run_id": run_id,
            "source_name": self.config.source_name,
            "source_url": self.config.source_url,
            "started_at": utc_now_iso(),
            "status": "running",
            "pages_requested": pages_requested,
        }

        self.supabase.table("raw_parse_runs").insert(payload).execute()

    def finish_parse_run(
        self,
        run_id: str,
        status: str,
        pages_parsed: int,
        records_found: int,
        records_inserted: int,
        records_updated: int,
        records_failed: int,
        error_message: str | None = None,
    ) -> None:
        payload = {
            "finished_at": utc_now_iso(),
            "status": status,
            "pages_parsed": pages_parsed,
            "records_found": records_found,
            "records_inserted": records_inserted,
            "records_updated": records_updated,
            "records_failed": records_failed,
            "error_message": error_message,
        }

        self.supabase.table("raw_parse_runs").update(payload).eq("run_id", run_id).execute()

    def get_detail_urls(self) -> list[str]:
        if self.config.detail_urls:
            return list(self.config.detail_urls[:self.config.max_urls])

        urls = []
        offset = 0

        while self.config.max_urls is None or len(urls) < self.config.max_urls:
            remaining = None if self.config.max_urls is None else self.config.max_urls - len(urls)
            batch_size = self.config.url_batch_size if remaining is None else min(
                self.config.url_batch_size,
                remaining,
            )
            end = offset + batch_size - 1

            response = (
                self.supabase
                .table("raw_head_krisha")
                .select("url")
                .range(offset, end)
                .execute()
            )
            rows = response.data or []

            if not rows:
                break

            urls.extend(row["url"] for row in rows if row.get("url"))
            offset += batch_size

        return deduplicate_urls(urls)

    def save_records(self, records: list[dict[str, Any]]) -> tuple[int, int]:
        if not records:
            return 0, 0

        unique_records = deduplicate_records_by_ad_id(records)
        ad_ids = [record["ad_id"] for record in unique_records if record.get("ad_id")]
        existing_ads = self.get_existing_ads(ad_ids)
        insert_records, update_records = split_insert_update_records(unique_records, existing_ads)

        inserted = 0
        updated = 0

        for batch in chunked(insert_records, self.config.insert_batch_size):
            self.supabase.table("raw_krisha_details").insert(batch).execute()
            inserted += len(batch)

        for record in update_records:
            ad_id = record["ad_id"]
            self.supabase.table("raw_krisha_details").update(record).eq("ad_id", ad_id).execute()
            updated += 1

        return inserted, updated

    def get_existing_ads(self, ad_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not ad_ids:
            return {}

        existing_ads = {}

        for batch in chunked(ad_ids, self.config.existing_ads_batch_size):
            response = (
                self.supabase
                .table("raw_krisha_details")
                .select("ad_id, first_seen_at")
                .in_("ad_id", batch)
                .execute()
            )

            existing_ads.update({
                row["ad_id"]: row
                for row in response.data
            })

        return existing_ads


def build_details_storage(config: KrishaDetailsConfig) -> KrishaDetailsStorage:
    return KrishaDetailsStorage(
        supabase=get_supabase_client(),
        config=config,
    )


def chunked(items: list[Any], batch_size: int) -> list[list[Any]]:
    return [
        items[index:index + batch_size]
        for index in range(0, len(items), batch_size)
    ]


def deduplicate_urls(urls: list[str]) -> list[str]:
    return list(dict.fromkeys(urls))


def deduplicate_records_by_ad_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_records = {}

    for record in records:
        ad_id = record.get("ad_id")
        if ad_id is None:
            continue

        unique_records[ad_id] = record

    return [
        {column: record.get(column) for column in DETAIL_COLUMNS}
        for record in unique_records.values()
    ]


def split_insert_update_records(
    records: list[dict[str, Any]],
    existing_ads: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    insert_records = []
    update_records = []

    for record in records:
        ad_id = record["ad_id"]

        if ad_id in existing_ads:
            record.pop("first_seen_at", None)
            update_records.append(record)
        else:
            insert_records.append(record)

    return insert_records, update_records

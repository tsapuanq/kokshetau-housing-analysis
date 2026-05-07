import os
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from supabase import Client, create_client

from .config import KrishaCityConfig
from .time_utils import utc_now_iso


def load_environment() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        load_env_file_without_dependency()
        return

    load_dotenv()


def load_env_file_without_dependency() -> None:
    for directory in env_search_directories():
        env_path = directory / ".env"
        if env_path.exists():
            read_env_file(env_path)
            return


def env_search_directories() -> list[Path]:
    directories: list[Path] = []

    cwd = Path.cwd().resolve()
    directories.extend([cwd, *cwd.parents])

    module_dir = Path(__file__).resolve().parent
    directories.extend([module_dir, *module_dir.parents])

    seen = set()
    unique_directories = []

    for directory in directories:
        if directory in seen:
            continue
        seen.add(directory)
        unique_directories.append(directory)

    return unique_directories


def read_env_file(env_path: Path) -> None:
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        if key and key not in os.environ:
            os.environ[key] = value


def get_supabase_client() -> Client:
    load_environment()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing in .env")

    validate_supabase_api_url(url)

    return create_client(url, key)


def validate_supabase_api_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme in ("postgres", "postgresql"):
        raise ValueError(
            "SUPABASE_URL must be the Supabase API URL, not the Postgres connection string. "
            "Use https://<project-ref>.supabase.co for SUPABASE_URL."
        )

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            "SUPABASE_URL must be a valid URL like https://<project-ref>.supabase.co"
        )


class KrishaStorage:
    def __init__(self, supabase: Client, config: KrishaCityConfig) -> None:
        self.supabase = supabase
        self.config = config

    def create_parse_run(self, run_id: str) -> None:
        payload = {
            "run_id": run_id,
            "source_name": self.config.source_name,
            "source_url": self.config.start_url,
            "started_at": utc_now_iso(),
            "status": "running",
            "pages_requested": self.config.max_pages,
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
        error_message: Optional[str] = None,
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

    def save_records(self, records: list[dict[str, Any]]) -> tuple[int, int]:
        if not records:
            return 0, 0

        ad_ids = [record["ad_id"] for record in records if record.get("ad_id")]
        existing_ads = self.get_existing_ads(ad_ids)

        insert_records, update_records = split_insert_update_records(records, existing_ads)

        inserted = 0
        updated = 0

        if insert_records:
            self.supabase.table("raw_head_krisha").insert(insert_records).execute()
            inserted = len(insert_records)

        for record in update_records:
            ad_id = record["ad_id"]
            self.supabase.table("raw_head_krisha").update(record).eq("ad_id", ad_id).execute()
            updated += 1

        return inserted, updated

    def get_existing_ads(self, ad_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not ad_ids:
            return {}

        response = (
            self.supabase
            .table("raw_head_krisha")
            .select("ad_id, first_seen_at")
            .in_("ad_id", ad_ids)
            .execute()
        )

        return {
            row["ad_id"]: row
            for row in response.data
        }


def split_insert_update_records(
    records: list[dict[str, Any]],
    existing_ads: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    insert_records = []
    update_records = []

    for record in records:
        ad_id = record["ad_id"]

        if ad_id in existing_ads:
            # Важно: first_seen_at не перезаписываем.
            record.pop("first_seen_at", None)
            update_records.append(record)
        else:
            insert_records.append(record)

    return insert_records, update_records

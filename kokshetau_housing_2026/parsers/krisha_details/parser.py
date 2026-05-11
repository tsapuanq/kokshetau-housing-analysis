import json
import logging
from typing import Any
from uuid import uuid4

from .config import KrishaDetailsConfig
from .extractor import KrishaDetailsExtractor
from .http import KrishaDetailsHttpClient
from .storage import KrishaDetailsStorage
from .validation import validate_records

logger = logging.getLogger(__name__)


class KrishaDetailsParser:
    def __init__(
        self,
        config: KrishaDetailsConfig,
        http_client: KrishaDetailsHttpClient,
        extractor: KrishaDetailsExtractor,
        storage: KrishaDetailsStorage,
    ) -> None:
        self.config = config
        self.http_client = http_client
        self.extractor = extractor
        self.storage = storage

    def run(self) -> None:
        run_id = str(uuid4())
        detail_urls = self.storage.get_detail_urls()
        self.storage.create_parse_run(run_id, pages_requested=len(detail_urls))

        records: list[dict[str, Any]] = []
        pages_parsed = 0
        records_failed = 0

        try:
            for detail_url in detail_urls:
                try:
                    html = self.http_client.fetch_html(detail_url)

                    if html is None:
                        records_failed += 1
                        logger.warning("No HTML for detail_url=%s", detail_url)
                        continue

                    record = self.extractor.parse_detail_page(
                        html=html,
                        detail_url=detail_url,
                        source_url=detail_url,
                        run_id=run_id,
                    )
                    records.append(record)
                    pages_parsed += 1

                except Exception:
                    records_failed += 1
                    logger.exception("Detail page failed url=%s. Continuing.", detail_url)

            quality_report = validate_records(records)
            logger.info("Quality report: %s", json.dumps(quality_report, ensure_ascii=False))

            if quality_report["issues_count"] > 0:
                logger.warning("Validation issues found: %s", quality_report["issues_count"])

            inserted, updated = self.storage.save_records(records)
            status = "success" if records_failed == 0 else "partial_success"

            self.storage.finish_parse_run(
                run_id=run_id,
                status=status,
                pages_parsed=pages_parsed,
                records_found=len(records),
                records_inserted=inserted,
                records_updated=updated,
                records_failed=records_failed,
            )

            logger.info(
                "Done. run_id=%s status=%s urls=%s records=%s inserted=%s updated=%s failed=%s",
                run_id,
                status,
                len(detail_urls),
                len(records),
                inserted,
                updated,
                records_failed,
            )

        except Exception as error:
            logger.exception("Details pipeline failed")

            self.storage.finish_parse_run(
                run_id=run_id,
                status="failed",
                pages_parsed=pages_parsed,
                records_found=len(records),
                records_inserted=0,
                records_updated=0,
                records_failed=records_failed,
                error_message=str(error),
            )

            raise


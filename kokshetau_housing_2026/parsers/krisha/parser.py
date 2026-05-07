import json
import logging
from typing import Any
from uuid import uuid4

from .config import KrishaCityConfig
from .extractor import KrishaCardExtractor
from .http import KrishaHttpClient
from .storage import KrishaStorage
from .validation import validate_records

logger = logging.getLogger(__name__)


class KrishaHeadParser:
    def __init__(
        self,
        config: KrishaCityConfig,
        http_client: KrishaHttpClient,
        extractor: KrishaCardExtractor,
        storage: KrishaStorage,
    ) -> None:
        self.config = config
        self.http_client = http_client
        self.extractor = extractor
        self.storage = storage

    def run(self) -> None:
        run_id = str(uuid4())
        self.storage.create_parse_run(run_id)

        all_records: list[dict[str, Any]] = []
        pages_parsed = 0
        records_failed = 0

        try:
            for page_number in range(1, self.config.max_pages + 1):
                page_url = self.http_client.build_page_url(page_number)
                html = self.http_client.fetch_html(page_url)

                if html is None:
                    logger.warning("No HTML for page=%s", page_number)
                    records_failed += 1
                    continue

                records = self.extractor.parse_listing_page(
                    html=html,
                    source_url=page_url,
                    page_number=page_number,
                    run_id=run_id,
                )

                if not records:
                    logger.info("No records found on page=%s. Stopping.", page_number)
                    break

                all_records.extend(records)
                pages_parsed += 1

            quality_report = validate_records(all_records)

            logger.info("Quality report: %s", json.dumps(quality_report, ensure_ascii=False))

            if quality_report["issues_count"] > 0:
                # Для production можно падать. Для discovery можно только логировать.
                logger.warning("Validation issues found: %s", quality_report["issues_count"])

            inserted, updated = self.storage.save_records(all_records)

            self.storage.finish_parse_run(
                run_id=run_id,
                status="success",
                pages_parsed=pages_parsed,
                records_found=len(all_records),
                records_inserted=inserted,
                records_updated=updated,
                records_failed=records_failed,
            )

            logger.info(
                "Done. run_id=%s records=%s inserted=%s updated=%s",
                run_id,
                len(all_records),
                inserted,
                updated,
            )

        except Exception as error:
            logger.exception("Pipeline failed")

            self.storage.finish_parse_run(
                run_id=run_id,
                status="failed",
                pages_parsed=pages_parsed,
                records_found=len(all_records),
                records_inserted=0,
                records_updated=0,
                records_failed=records_failed,
                error_message=str(error),
            )

            raise

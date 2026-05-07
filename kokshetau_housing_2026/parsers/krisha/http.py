import logging
import random
import time
from typing import Optional

import requests
from requests import Session
from requests.exceptions import RequestException, Timeout

from .config import KrishaCityConfig

logger = logging.getLogger(__name__)


class KrishaHttpClient:
    def __init__(self, config: KrishaCityConfig) -> None:
        self.config = config
        self.session = self._create_session()

    def build_page_url(self, page_number: int) -> str:
        if page_number == 1:
            return self.config.start_url

        return f"{self.config.start_url}?page={page_number}"

    def fetch_html(self, url: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Fetching url=%s attempt=%s", url, attempt)

                response = self.session.get(url, timeout=self.config.request_timeout)

                if response.status_code == 200:
                    self._polite_sleep()
                    return response.text

                if response.status_code == 429:
                    wait_seconds = 60 * attempt
                    logger.warning("Rate limited 429. Sleeping %s seconds", wait_seconds)
                    time.sleep(wait_seconds)
                    continue

                if response.status_code in (500, 502, 503, 504):
                    wait_seconds = 10 * attempt
                    logger.warning(
                        "Server error %s. Sleeping %s seconds",
                        response.status_code,
                        wait_seconds,
                    )
                    time.sleep(wait_seconds)
                    continue

                if response.status_code in (401, 403):
                    logger.error("Access forbidden status=%s url=%s", response.status_code, url)
                    return None

                logger.warning("Unexpected status=%s url=%s", response.status_code, url)
                return None

            except Timeout:
                logger.warning("Timeout url=%s attempt=%s", url, attempt)
                time.sleep(10 * attempt)

            except RequestException as error:
                logger.exception("Request failed url=%s error=%s", url, error)
                time.sleep(10 * attempt)

        logger.error("Failed after retries url=%s", url)
        return None

    def _create_session(self) -> Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        return session

    def _polite_sleep(self) -> None:
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        logger.info("Sleeping %.2f seconds", delay)
        time.sleep(delay)

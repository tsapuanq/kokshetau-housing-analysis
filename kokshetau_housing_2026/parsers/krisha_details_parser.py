import logging

try:
    from krisha_details.config import KOKSHETAU_DETAILS_CONFIG, KrishaDetailsConfig
    from krisha_details.extractor import KrishaDetailsExtractor
    from krisha_details.http import KrishaDetailsHttpClient
    from krisha_details.parser import KrishaDetailsParser
    from krisha_details.storage import build_details_storage
except ModuleNotFoundError as error:
    if error.name != "krisha_details":
        raise

    from .krisha_details.config import KOKSHETAU_DETAILS_CONFIG, KrishaDetailsConfig
    from .krisha_details.extractor import KrishaDetailsExtractor
    from .krisha_details.http import KrishaDetailsHttpClient
    from .krisha_details.parser import KrishaDetailsParser
    from .krisha_details.storage import build_details_storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def build_parser(config: KrishaDetailsConfig = KOKSHETAU_DETAILS_CONFIG) -> KrishaDetailsParser:
    return KrishaDetailsParser(
        config=config,
        http_client=KrishaDetailsHttpClient(config),
        extractor=KrishaDetailsExtractor(config),
        storage=build_details_storage(config),
    )


def main() -> None:
    parser = build_parser()
    parser.run()


if __name__ == "__main__":
    main()

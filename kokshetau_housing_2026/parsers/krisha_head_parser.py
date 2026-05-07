import logging

try:
    from krisha.config import KOKSHETAU_CONFIG, KrishaCityConfig
    from krisha.extractor import KrishaCardExtractor
    from krisha.http import KrishaHttpClient
    from krisha.parser import KrishaHeadParser
    from krisha.storage import KrishaStorage, get_supabase_client
except ModuleNotFoundError as error:
    if error.name != "krisha":
        raise

    from .krisha.config import KOKSHETAU_CONFIG, KrishaCityConfig
    from .krisha.extractor import KrishaCardExtractor
    from .krisha.http import KrishaHttpClient
    from .krisha.parser import KrishaHeadParser
    from .krisha.storage import KrishaStorage, get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def build_parser(config: KrishaCityConfig = KOKSHETAU_CONFIG) -> KrishaHeadParser:
    supabase = get_supabase_client()

    return KrishaHeadParser(
        config=config,
        http_client=KrishaHttpClient(config),
        extractor=KrishaCardExtractor(config),
        storage=KrishaStorage(supabase, config),
    )


def main() -> None:
    parser = build_parser()
    parser.run()


if __name__ == "__main__":
    main()

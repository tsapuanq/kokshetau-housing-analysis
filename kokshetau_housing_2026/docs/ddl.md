---for head
create table if not exists raw_parse_runs (
    run_id uuid primary key,

    source_name text not null,
    source_url text not null,

    started_at timestamptz not null default now(),
    finished_at timestamptz,
    status text not null,

    pages_requested int,
    pages_parsed int default 0,
    records_found int default 0,
    records_inserted int default 0,
    records_updated int default 0,
    records_failed int default 0,

    error_message text,

    created_at timestamptz not null default now()
);


create table if not exists raw_head_krisha (
    -- ids
    ad_id text primary key,
    product_id text,
    uuid text,
    html_id text,

    -- main listing data
    title text,
    price_text text,
    price_kzt bigint,
    address text,
    description text,
    url text,

    -- parsed apartment attributes from head
    rooms int,
    area_m2 numeric,
    floor int,
    total_floors int,
    building_type text,
    building_year int,
    ceiling_height numeric,
    bathroom text,
    residential_complex text,

    -- listing labels / seller flags
    labels jsonb,
    is_specialist boolean,
    is_owner boolean,
    is_new_building boolean,
    has_mortgage boolean,
    has_installment boolean,
    is_urgent boolean,
    has_bargain boolean,
    is_pledged boolean,

    -- promotion / visibility flags
    is_visible boolean,
    is_highlighted boolean,
    is_colored boolean,
    has_top_promotion boolean,
    has_hot_promotion boolean,
    has_month_promotion boolean,
    has_week_promotion boolean,

    -- location / publication
    city text,
    published_date_text text,

    -- media
    main_image_url text,
    image_alt text,
    image_title text,
    photo_count int,

    -- useful extra links
    complex_url text,

    -- raw/debug
    raw_classes text,
    all_text text,

    -- reproducibility
    source_url text not null,
    page_number int not null,
    position_on_page int,
    run_id uuid,

    content_hash text not null,

    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    parsed_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);





CREATE TABLE IF NOT EXISTS raw_krisha_details (
    ad_id BIGINT PRIMARY KEY,
    uuid TEXT,

    detail_url TEXT NOT NULL,
    source_url TEXT,

    title TEXT,
    description TEXT,
    price_kzt BIGINT,
    price_m2 BIGINT,
    status TEXT,

    rooms INTEGER,
    area_m2 NUMERIC(10, 2),
    floor INTEGER,
    total_floors INTEGER,
    building_type TEXT,
    building_year INTEGER,
    ceiling_height NUMERIC(5, 2),
    bathroom TEXT,

    city TEXT,
    address TEXT,
    full_address TEXT,
    latitude NUMERIC(12, 8),
    longitude NUMERIC(12, 8),

    owner_name TEXT,
    user_type TEXT,
    owner_is_owner BOOLEAN,
    owner_is_pro BOOLEAN,
    owner_is_complex BOOLEAN,
    owner_is_builder BOOLEAN,

    category_alias TEXT,
    category_label TEXT,
    complex_id BIGINT,
    complex_name TEXT,
    is_layout BOOLEAN,

    photo_count INTEGER,
    main_photo_url TEXT,

    created_at_krisha DATE,
    added_at_krisha DATE,
    days_in_live INTEGER,

    run_id TEXT,
    parser_version TEXT DEFAULT 'v1',
    content_hash TEXT,

    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parsed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    advert_json JSONB,
    advert_card_json JSONB,
    photos_json JSONB
);
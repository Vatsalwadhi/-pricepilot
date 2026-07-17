CREATE TABLE api_platform (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    slug VARCHAR(80) NOT NULL UNIQUE,
    provider_key VARCHAR(80) NOT NULL UNIQUE,
    base_url VARCHAR(200) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE api_product (
    id BIGSERIAL PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    quantity VARCHAR(80) NOT NULL DEFAULT '',
    brand VARCHAR(120) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT unique_normalized_product_variant UNIQUE (normalized_name, quantity, brand)
);

CREATE INDEX api_product_normalized_quantity_idx
    ON api_product (normalized_name, quantity);

CREATE TABLE api_searchhistory (
    id BIGSERIAL PRIMARY KEY,
    query VARCHAR(255) NOT NULL,
    normalized_query VARCHAR(255) NOT NULL,
    cheapest_platform_id BIGINT REFERENCES api_platform(id) ON DELETE SET NULL,
    cheapest_total_price NUMERIC(10, 2),
    highest_total_price NUMERIC(10, 2),
    savings NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX api_searchhistory_normalized_query_idx
    ON api_searchhistory (normalized_query);

CREATE TABLE api_comparisonresult (
    id BIGSERIAL PRIMARY KEY,
    search_id BIGINT NOT NULL REFERENCES api_searchhistory(id) ON DELETE CASCADE,
    platform_id BIGINT REFERENCES api_platform(id) ON DELETE SET NULL,
    product_id BIGINT REFERENCES api_product(id) ON DELETE SET NULL,
    product_name VARCHAR(255) NOT NULL DEFAULT '',
    normalized_product_name VARCHAR(255) NOT NULL DEFAULT '',
    quantity VARCHAR(80) NOT NULL DEFAULT '',
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    price NUMERIC(10, 2),
    delivery_charge NUMERIC(10, 2),
    total_price NUMERIC(10, 2),
    product_url VARCHAR(200) NOT NULL DEFAULT '',
    is_cheapest BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT NOT NULL DEFAULT '',
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX api_comparisonresult_search_total_idx
    ON api_comparisonresult (search_id, total_price);

CREATE INDEX api_comparisonresult_normalized_product_idx
    ON api_comparisonresult (normalized_product_name);

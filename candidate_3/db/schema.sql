-- schema.sql
-- Four tables mirroring products, stores, sales, warranty — with keys and constraints.

DROP TABLE IF EXISTS warranty CASCADE;
DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS stores CASCADE;

CREATE TABLE products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category_id     TEXT NOT NULL,
    launch_date     DATE,
    price           NUMERIC(10, 2) NOT NULL CHECK (price > 0)
);

CREATE TABLE stores (
    store_id        TEXT PRIMARY KEY,
    store_name      TEXT,
    city            TEXT,
    country         TEXT
);

CREATE TABLE sales (
    sale_id         TEXT PRIMARY KEY,
    sale_date       DATE NOT NULL,
    store_id        TEXT NOT NULL REFERENCES stores(store_id),
    product_id      TEXT NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE TABLE warranty (
    claim_id        TEXT PRIMARY KEY,
    sale_id         TEXT NOT NULL REFERENCES sales(sale_id),
    claim_date      DATE,
    repair_status   TEXT
);

-- indexes to speed up the joins in Task 8's queries
CREATE INDEX idx_sales_product_id ON sales(product_id);
CREATE INDEX idx_sales_store_id ON sales(store_id);
CREATE INDEX idx_warranty_sale_id ON warranty(sale_id);
CREATE TABLE IF NOT EXISTS sales (
    sale_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) REFERENCES stores(store_id),
    product_id VARCHAR(50) REFERENCES products(product_id),
    sale_date TIMESTAMP NOT NULL,
    quantity INT NOT NULL
);
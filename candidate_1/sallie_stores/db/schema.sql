------------------------------------------
-- SCHEMA FOR SALLIE STORES DATABASE
------------------------------------------

CREATE TABLE IF NOT EXISTS Categories (
    category_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category_id VARCHAR(50) REFERENCES categories(category_id),
    launch_date DATE,
    price NUMERIC(10, 2) NOT NULL CHECK (price > 0)
);

CREATE TABLE IF NOT EXISTS Stores (
    store_id VARCHAR(50) PRIMARY KEY,
    store_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Sales (
    sale_id VARCHAR(50) PRIMARY KEY,
    sale_date TIMESTAMP NOT NULL,
    store_id VARCHAR(50) NOT NULL REFERENCES stores(store_id),
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS Warranty (
    claim_id VARCHAR(50) PRIMARY KEY,
    claim_date DATE NOT NULL,
    sale_id VARCHAR(50) NOT NULL REFERENCES sales(sale_id),
    repair_status VARCHAR(50) NOT NULL
);
-- Adding an index to optimize sales date lookups
CREATE INDEX IF NOT EXISTS idx_sales_sale_date ON sales(sale_date);
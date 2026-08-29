# Gamma Deck Prompt

Use this prompt in Gamma to create a polished stakeholder-facing presentation for the Sallie Stores Apple Retail Sales ETL project.

Prompt:

Create a concise but professional slide deck for a business and technical stakeholder audience.

Project: Sallie Stores Apple Retail Sales ETL and Postgres Pipeline

Objective:
Present how we transformed raw Apple retail data into a clean, reusable data pipeline and business analytics layer. The deck should communicate the business value, data-cleaning decisions, key metrics, database design, and benchmarking insights clearly and visually.

Audience:

- business stakeholders
- project sponsors
- technical reviewers
- leadership team

Tone:

- executive-friendly
- polished
- concise
- confident
- data-driven

Presentation goals:

- explain the problem and why this dataset matters
- show the end-to-end ETL flow
- highlight the quality checks and cleaning decisions
- present the most important business results
- explain the database design and repository layer
- summarize the Pandas vs Polars performance comparison
- close with next steps and recommendations

Suggested structure:

Slide 1: Title slide

- Title: Sallie Stores: Apple Retail Sales Analytics Pipeline
- subtitle: ETL, analytics, benchmarking, and PostgreSQL readiness
- include a clean Apple retail or dashboard-style visual

Slide 2: Business context and objective

- What problem we are solving
- Why Apple retail sales data is valuable for operational analytics
- What questions we are answering

Slide 3: Data pipeline overview

- show raw files -> extract -> clean -> transform -> processed Parquet -> Postgres
- keep it visually simple and easy to scan

Slide 4: Data quality and cleaning decisions

- explain issues addressed: missing values, duplicates, invalid dates, bad quantities/prices
- mention that the processed layer is reusable for future analysis

Slide 5: Key business metrics

- revenue by month
- revenue by category
- top products by revenue
- top stores by revenue
- warranty claim rate by category
- month-over-month growth

Slide 6: Product and store insights

- highlight the top-performing products and stores
- call out the strongest revenue trends and which segments are leading

Slide 7: Database and repository layer

- show categories -> products -> stores -> sales -> warranty
- explain why the schema supports relational queries and reporting
- show the business value of the Postgres-ready model

Slide 8: Performance benchmark

- show Pandas vs Polars comparison table
- include average time and memory footprint
- explain that Polars may be faster for large-scale transforms, while Pandas remains useful for familiar workflows

Slide 9: Outcome and next steps

- summarize the result: clean data pipeline, reusable processed data, Postgres-ready analytics
- recommend next actions: dashboarding, forecasting, executive reporting, deeper segmentation

Design requirements:

- modern, minimal, professional layout
- use blue, white, and neutral tones with subtle accent colors
- strong data visualization, not too much text
- each slide should have one core takeaway
- include charts or simple metric cards where appropriate

Data points to reference:

- revenue by month trend
- category revenue ranking
- top products by revenue
- top stores by revenue
- claim-rate analysis by category
- Pandas vs Polars comparison metrics from the benchmark script

Use concise script notes in the speaker notes for each slide.

Include a closing slide with a brief summary statement:
"We converted raw retail data into a clean, reusable analytics pipeline that supports operational insight, relational reporting, and scalable data processing."

Make the final deck look like a polished technical case study and executive update.

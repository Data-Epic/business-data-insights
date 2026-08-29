from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import logging

logger = logging.getLogger(__name__)


CATEGORY_NAMES = {
    "CAT-1": "Laptop",
    "CAT-2": "Audio",
    "CAT-3": "Tablet",
    "CAT-4": "Smartphone",
    "CAT-5": "Wearable",
    "CAT-6": "Streaming Device",
    "CAT-7": "Desktop",
    "CAT-8": "Subscription Service",
    "CAT-9": "Smart Speaker",
    "CAT-10": "Accessories",
}


def get_category_mapping(processed_dir: Path = None) -> dict:  # type: ignore
    """Get category mapping from parquet or use predefined mapping."""

    if processed_dir:
        try:
            categories_df = pd.read_parquet(
                processed_dir / "categories.parquet"
            )

            mapping = dict(
                zip(
                    categories_df["category_id"],
                    categories_df["category_name"]
                )
            )

            return mapping

        except Exception:
            pass

    return CATEGORY_NAMES


def revenue_by_month(
    sales_df: pd.DataFrame,
    product_df: pd.DataFrame | None = None
) -> pd.DataFrame:

    working = sales_df.copy()

    if product_df is not None:
        working = working.merge(
            product_df[["product_id", "price", "category_id"]],
            on="product_id",
            how="left"
        )

    if "price" not in working.columns:
        raise KeyError("Price column is required for revenue aggregation.")

    working["revenue"] = working["quantity"] * working["price"]
    working["month"] = working["sale_date"].dt.to_period("M").astype(str)

    return (
        working.groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")  # type: ignore
        .reset_index(drop=True)
    )


def revenue_by_category(
    sales_df: pd.DataFrame,
    product_df: pd.DataFrame
) -> pd.DataFrame:

    merged = sales_df.merge(
        product_df[["product_id", "category_id", "price"]],
        on="product_id",
        how="left"
    )

    merged["revenue"] = merged["quantity"] * merged["price"]

    return (
        merged.groupby("category_id", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)    #type: ignore
        .reset_index(drop=True)
    )


def top_products_by_revenue(
    sales_df: pd.DataFrame,
    product_df: pd.DataFrame,
    n: int = 10
) -> pd.DataFrame:

    merged = sales_df.merge(
        product_df[["product_id", "product_name", "price"]],
        on="product_id",
        how="left"
    )

    merged["revenue"] = merged["quantity"] * merged["price"]

    return (
        merged.groupby(["product_id", "product_name"], as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)  # type: ignore
        .head(n)
        .reset_index(drop=True)
    )


def top_stores_by_revenue(
    sales_df: pd.DataFrame,
    store_df: pd.DataFrame,
    product_df: pd.DataFrame,
    n: int = 10
) -> pd.DataFrame:

    merged = sales_df.merge(
        product_df[["product_id", "price"]],
        on="product_id",
        how="left"
    )

    merged = merged.merge(
        store_df[["store_id", "store_name"]],
        on="store_id",
        how="left"
    )

    merged["revenue"] = merged["quantity"] * merged["price"]

    return (
        merged.groupby(
            ["store_id", "store_name"],
            as_index=False
        )["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)    #type: ignore
        .head(n)
        .reset_index(drop=True)
    )


def warranty_claim_rate_by_category(
    sales_df: pd.DataFrame,
    products_df: pd.DataFrame,
    warranty_df: pd.DataFrame
) -> pd.DataFrame:

    sales_merged = sales_df.merge(
        products_df[["product_id", "category_id"]],
        on="product_id",
        how="left"
    )

    total_by_category = (
        sales_merged
        .groupby("category_id")
        .size()
        .rename("total_sales")
        .reset_index()
    )

    claimed_sales = sales_merged[
        sales_merged["sale_id"].isin(warranty_df["sale_id"])
    ]

    claims_by_category = (
        claimed_sales
        .groupby("category_id")["sale_id"]
        .nunique()
        .rename("total_claims")
        .reset_index()
    )

    result = total_by_category.merge(
        claims_by_category,
        on="category_id",
        how="left"
    )

    result["total_claims"] = (
        result["total_claims"]
        .fillna(0)
        .astype(int)
    )

    result["claim_rate"] = (
        result["total_claims"] / result["total_sales"]
    )

    return (
        result
        .sort_values("claim_rate", ascending=False)
        .reset_index(drop=True)
    )


def month_over_month_growth(
    revenue_monthly: pd.DataFrame
) -> pd.DataFrame:

    result = (
        revenue_monthly
        .copy()
        .sort_values("month")
        .reset_index(drop=True)
    )

    result["prev_revenue"] = result["revenue"].shift(1)

    result["mom_growth_pct"] = (
        (result["revenue"] - result["prev_revenue"])
        / result["prev_revenue"].replace(0, pd.NA)
    )

    return result


def compute_summary_metrics(
    sales_df: pd.DataFrame,
    products_df: pd.DataFrame,
    stores_df: pd.DataFrame,
    warranty_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:

    monthly_revenue = revenue_by_month(
        sales_df,
        products_df
    )

    return {
        "revenue_by_month": monthly_revenue,
        "revenue_by_category": revenue_by_category(
            sales_df,
            products_df
        ),
        "top_products_by_revenue": top_products_by_revenue(
            sales_df,
            products_df,
            n=10
        ),
        "top_stores_by_revenue": top_stores_by_revenue(
            sales_df,
            stores_df,
            products_df,
            n=10
        ),
        "warranty_claim_rate_by_category":
            warranty_claim_rate_by_category(
                sales_df,
                products_df,
                warranty_df
            ),
        "monthly_growth": month_over_month_growth(
            monthly_revenue
        ),
    }


def generate_visualizations(
    summary: dict[str, pd.DataFrame],
    output_dir: str = "reports/figures"
):

    Path(output_dir).mkdir(
        parents=True,
        exist_ok=True
    )

    plt.style.use("seaborn-v0_8-darkgrid")
    sns.set_palette("Blues_d")

    # Revenue by month

    fig, ax = plt.subplots(figsize=(12, 6))

    df = summary["revenue_by_month"].copy()

    df["month_dt"] = pd.to_datetime(
        df["month"] + "-01",
        errors="coerce"
    )

    df = (
        df.dropna(subset=["month_dt"])
        .sort_values("month_dt")
    )

    ax.plot(
        df["month_dt"],
        df["revenue"],
        marker="o",
        linewidth=2,
        markersize=6,
        color="#007AFF"
    )

    ax.set_title(
        "Bi-Annual Revenue Trend",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue ($)")

    ax.xaxis.set_major_formatter(
        plt.matplotlib.dates.DateFormatter("%Y-%m")  # type: ignore
    )

    ax.xaxis.set_major_locator(
        plt.matplotlib.dates.MonthLocator(interval=6)   #type: ignore
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    for i in range(0, len(df), 6):

        revenue = df["revenue"].iloc[i]

        ax.text(
            df["month_dt"].iloc[i],
            revenue + 2e6,
            f"${revenue / 1e6:.1f}M",
            ha="center",
            fontsize=8
        )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/revenue_by_month.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Revenue by category

    fig, ax = plt.subplots(figsize=(12, 6))

    df = summary["revenue_by_category"].copy()

    if "category_name" in df.columns:
        labels = df["category_name"]
    else:
        labels = (
            df["category_id"]
            .map(CATEGORY_NAMES)
            .fillna(df["category_id"])
        )

    bars = ax.bar(
        labels,
        df["revenue"] / 1e6,
        color=sns.color_palette(
            "Blues_d",
            len(df)
        )
    )

    ax.set_title(
        "Revenue by Product Category",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel("Category")
    ax.set_ylabel("Revenue (Millions $)")

    ax.tick_params(
        axis="x",
        rotation=45
    )

    plt.setp(
        ax.get_xticklabels(),
        ha="right"
    )

    for bar, value in zip(
        bars,
        df["revenue"] / 1e6
    ):

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"${value:.0f}M",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    total_revenue = df["revenue"].sum()

    ax.text(
        0.98,
        0.98,
        f"Total: ${total_revenue / 1e6:.0f}M",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=11,
        fontweight="bold",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.8
        )
    )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/revenue_by_category.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Top products

    fig, ax = plt.subplots(figsize=(12, 8))

    df = summary["top_products_by_revenue"].head(10).copy()

    bars = ax.barh(
        df["product_name"],
        df["revenue"] / 1e6,
        color=sns.color_palette(
            "Blues_d",
            len(df)
        )
    )

    ax.set_title(
        "Top 10 Products by Revenue",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel("Revenue (Millions $)")
    ax.set_ylabel("Product")

    for bar, value in zip(
        bars,
        df["revenue"] / 1e6
    ):

        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"${value:.1f}M",
            ha="left",
            va="center",
            fontsize=9
        )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/top_products.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Top stores

    fig, ax = plt.subplots(figsize=(12, 8))

    df = summary["top_stores_by_revenue"].head(10).copy()

    bars = ax.barh(
        df["store_name"],
        df["revenue"] / 1e6,
        color=sns.color_palette(
            "Greens_d",
            len(df)
        )
    )

    ax.set_title(
        "Top 10 Stores by Revenue",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel("Revenue (Millions $)")
    ax.set_ylabel("Store")

    for bar, value in zip(
        bars,
        df["revenue"] / 1e6
    ):

        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"${value:.1f}M",
            ha="left",
            va="center",
            fontsize=9
        )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/top_stores.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Warranty claim rate

    fig, ax = plt.subplots(figsize=(12, 6))

    df = summary[
        "warranty_claim_rate_by_category"
    ].copy()

    if "category_name" in df.columns:
        labels = df["category_name"]
    else:
        labels = (
            df["category_id"]
            .map(CATEGORY_NAMES)
            .fillna(df["category_id"])
        )

    bars = ax.bar(
        labels,
        df["claim_rate"] * 100,
        color=sns.color_palette(
            "Reds_d",
            len(df)
        )
    )

    ax.set_title(
        "Warranty Claim Rate by Category",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel("Category")
    ax.set_ylabel("Claim Rate (%)")

    ax.tick_params(
        axis="x",
        rotation=45
    )

    plt.setp(
        ax.get_xticklabels(),
        ha="right"
    )

    ax.set_ylim(0, 110)

    for bar, value in zip(
        bars,
        df["claim_rate"] * 100
    ):

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{value:.0f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold"
        )

    ax.text(
        0.5,
        -0.15,
        "Synthetic data: claim rates should be investigated if unusually high.",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=9,
        color="gray",
        style="italic"
    )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/warranty_claim_rate.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Monthly growth

    fig, ax = plt.subplots(figsize=(14, 6))

    df = summary["monthly_growth"].copy()

    df["month_dt"] = pd.to_datetime(
        df["month"] + "-01",
        errors="coerce"
    )

    df = (
        df.dropna(subset=["month_dt"])
        .sort_values("month_dt")
    )

    colors = [
        "green" if pd.notna(value) and value >= 0 else "red"
        for value in df["mom_growth_pct"]
    ]

    bars = ax.bar(
        df["month_dt"],
        df["mom_growth_pct"] * 100,
        color=colors,
        alpha=0.7
    )

    ax.axhline(
        y=0,
        color="black",
        linestyle="-",
        linewidth=0.5
    )

    ax.set_title(
        "Monthly Revenue Growth Rate",
        fontsize=16,
        fontweight="bold"
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Growth Rate (%)")

    ax.xaxis.set_major_formatter(
        plt.matplotlib.dates.DateFormatter("%Y-%m") #type: ignore
    )

    ax.xaxis.set_major_locator(
        plt.matplotlib.dates.MonthLocator(interval=6)  # type: ignore
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    for bar, value in zip(
        bars,
        df["mom_growth_pct"]
    ):

        if pd.notna(value) and abs(value) > 0.05:

            y_position = (
                value * 100
                + (2 if value >= 0 else -2)
            )

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_position,
                f"{value:.1%}",
                ha="center",
                va="center",
                fontsize=7
            )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/monthly_growth.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # Dashboard summary

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(14, 10)
    )

    df = summary["revenue_by_month"].copy()

    df["month_dt"] = pd.to_datetime(
        df["month"] + "-01",
        errors="coerce"
    )

    df = (
        df.dropna(subset=["month_dt"])
        .sort_values("month_dt")
    )

    axes[0, 0].plot(
        df["month_dt"],
        df["revenue"] / 1e6,
        marker="o",
        color="blue",
        linewidth=2
    )

    axes[0, 0].set_title(
        "Monthly Revenue",
        fontsize=12,
        fontweight="bold"
    )

    axes[0, 0].set_ylabel(
        "Revenue (Millions $)"
    )

    axes[0, 0].xaxis.set_major_formatter(
        plt.matplotlib.dates.DateFormatter("%Y-%m") #type: ignore
    )

    axes[0, 0].xaxis.set_major_locator(
        plt.matplotlib.dates.MonthLocator(interval=12)  #type: ignore
    )

    axes[0, 0].tick_params(
        axis="x",
        rotation=45,
        labelsize=8
    )

    df = summary["revenue_by_category"].head(6).copy()

    if "category_name" in df.columns:
        labels = df["category_name"]
    else:
        labels = (
            df["category_id"]
            .map(CATEGORY_NAMES)
            .fillna(df["category_id"])
        )

    axes[0, 1].bar(
        labels,
        df["revenue"] / 1e6,
        color="steelblue"
    )

    axes[0, 1].set_title(
        "Top Categories",
        fontsize=12,
        fontweight="bold"
    )

    axes[0, 1].set_ylabel(
        "Revenue (Millions $)"
    )

    axes[0, 1].tick_params(
        axis="x",
        rotation=45,
        labelsize=8
    )

    plt.setp(
        axes[0, 1].get_xticklabels(),
        ha="right"
    )

    df = summary[
        "top_products_by_revenue"
    ].head(5).copy()

    axes[1, 0].barh(
        df["product_name"],
        df["revenue"] / 1e6,
        color="darkblue"
    )

    axes[1, 0].set_title(
        "Top Products",
        fontsize=12,
        fontweight="bold"
    )

    axes[1, 0].set_xlabel(
        "Revenue (Millions $)"
    )

    axes[1, 0].tick_params(
        labelsize=8
    )

    df = summary[
        "top_stores_by_revenue"
    ].head(5).copy()

    axes[1, 1].barh(
        df["store_name"],
        df["revenue"] / 1e6,
        color="darkgreen"
    )

    axes[1, 1].set_title(
        "Top Stores",
        fontsize=12,
        fontweight="bold"
    )

    axes[1, 1].set_xlabel(
        "Revenue (Millions $)"
    )

    axes[1, 1].tick_params(
        labelsize=8
    )

    plt.suptitle(
        "Sallie Stores: Key Metrics Dashboard",
        fontsize=18,
        fontweight="bold"
    )

    plt.tight_layout()

    plt.savefig(
        f"{output_dir}/dashboard_summary.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"All visualizations saved to {output_dir}/"
    )

    return output_dir


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    project_root = Path(__file__).resolve().parents[1]
    processed_dir = project_root / "data" / "processed"

    sales_df = pd.read_parquet(
        processed_dir / "sales.parquet"
    )

    products_df = pd.read_parquet(
        processed_dir / "products.parquet"
    )

    stores_df = pd.read_parquet(
        processed_dir / "stores.parquet"
    )

    warranty_df = pd.read_parquet(
        processed_dir / "warranty.parquet"
    )

    summary = compute_summary_metrics(
        sales_df,
        products_df,
        stores_df,
        warranty_df
    )

    for name, df in summary.items():
        logger.info(f"\n--- {name} ---")
        logger.info(df.head())

    generate_visualizations(
        summary,
        "reports/figures"
    )

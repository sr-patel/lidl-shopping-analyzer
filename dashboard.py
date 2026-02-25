import streamlit as st
import pandas as pd
import json
import os

DATA_FILE = "lidl_receipts.json"

st.set_page_config(layout="wide", page_title="Lidl Receipts Dashboard", page_icon="🛒")

st.markdown(
    """
<style>
.main .block-container {
    padding-top: 2rem;
}
</style>
""",
    unsafe_allow_html=True,
)


def load_data(filename):
    if not os.path.exists(filename):
        st.error(
            f"Error: File '{filename}' not found. "
            "Please run the data extraction script first."
        )
        return None

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        st.error(f"Error: '{filename}' is not valid JSON. Please check the file format.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


def to_float(x):
    if x is None or x == "" or str(x).strip() == "":
        return 0.0
    return float(str(x).replace(",", "."))


data = load_data(DATA_FILE)

if data:
    df = pd.DataFrame(data)

    df["purchase_date"] = pd.to_datetime(df["purchase_date"], format="%Y.%m.%d")
    df["total_price"] = df["total_price"].apply(to_float)
    df["saved_amount"] = df["saved_amount"].apply(to_float)
    df["lidlplus_saved_amount"] = (
        df["lidlplus_saved_amount"].apply(to_float)
        if "lidlplus_saved_amount" in df.columns
        else 0.0
    )
    df["total_price_no_saving"] = (
        df["total_price_no_saving"].apply(to_float)
        if "total_price_no_saving" in df.columns
        else 0.0
    )
    if "store" not in df.columns:
        df["store"] = "Unknown"
    df["store"] = df["store"].fillna("Unknown")

    initial_count = len(df)
    df = df[df["items"].notna()]
    df = df[df["items"].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    filtered_out = initial_count - len(df)

    if filtered_out > 0:
        st.info(
            f"{filtered_out} receipt(s) were filtered out because they had no items."
        )

    st.title("Lidl+ Dashboard")

    # ── Sidebar ────────────────────────────────────────────────────────────────
    st.sidebar.header("Filters")

    min_date = df["purchase_date"].min().date()
    max_date = df["purchase_date"].max().date()

    start_date = st.sidebar.date_input(
        "Start date", min_date, min_value=min_date, max_value=max_date
    )
    end_date = st.sidebar.date_input(
        "End date", max_date, min_value=min_date, max_value=max_date
    )

    all_stores = sorted(df["store"].unique().tolist())
    selected_stores = st.sidebar.multiselect(
        "Stores", options=all_stores, default=all_stores
    )

    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

    filtered_df = df[
        (df["purchase_date"] >= start_datetime)
        & (df["purchase_date"] < end_datetime)
        & (df["store"].isin(selected_stores if selected_stores else all_stores))
    ]

    # ── Helper: build flat items dataframe ─────────────────────────────────────
    DEPOSIT_PATTERN = "|".join(["pfand", "deposit return", "bottle return"])

    def build_items_df(source_df):
        rows = []
        for _, row in source_df.iterrows():
            if row.get("items") and isinstance(row["items"], list):
                for item in row["items"]:
                    try:
                        quantity = float(str(item.get("quantity", 1)).replace(",", "."))
                        price = to_float(item.get("price", 0))
                        unit = item.get("unit", "each")
                    except (ValueError, TypeError):
                        quantity, price, unit = 1.0, 0.0, "each"
                    rows.append(
                        {
                            "name": item.get("name", ""),
                            "quantity": quantity,
                            "price": price,
                            "unit": unit,
                            "total_value": quantity * price,
                            "purchase_date": row["purchase_date"],
                            "store": row["store"],
                        }
                    )
        return pd.DataFrame(rows)

    items_df_full = build_items_df(filtered_df)
    if not items_df_full.empty:
        items_df_clean = items_df_full[
            ~items_df_full["name"].str.contains(DEPOSIT_PATTERN, case=False, na=False)
        ]
    else:
        items_df_clean = items_df_full

    # ── Key metrics ────────────────────────────────────────────────────────────
    st.header("Key metrics")

    total_receipts = len(filtered_df)
    total_spent = filtered_df["total_price"].sum()
    total_saved_regular = filtered_df["saved_amount"].sum()
    lidlplus_saved = (
        filtered_df["lidlplus_saved_amount"].sum()
        if "lidlplus_saved_amount" in filtered_df.columns
        else 0.0
    )
    total_saved = total_saved_regular + lidlplus_saved
    avg_per_trip = total_spent / total_receipts if total_receipts > 0 else 0.0

    # Use total_price_no_saving for an accurate gross saving rate where available
    gross_total = filtered_df["total_price_no_saving"].sum()
    if gross_total > 0:
        gross_saving_rate = (gross_total - total_spent) / gross_total * 100
    else:
        gross_saving_rate = (
            total_saved / (total_spent + total_saved) * 100
        ) if (total_spent + total_saved) > 0 else 0.0

    avg_basket_size = 0.0
    unique_products = 0
    if not items_df_clean.empty:
        avg_basket_size = (
            items_df_clean.groupby(items_df_clean["purchase_date"])["quantity"]
            .sum()
            .mean()
            if total_receipts > 0
            else 0.0
        )
        unique_products = items_df_clean["name"].nunique()

    st.markdown("##### Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total spent", f"£{total_spent:,.2f}")
    col2.metric("Total receipts", f"{total_receipts}")
    col3.metric("Avg spend per trip", f"£{avg_per_trip:,.2f}")
    col4.metric("Unique products", f"{unique_products}")

    st.markdown("##### Savings")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total saved", f"£{total_saved:,.2f}")
    col2.metric("Overall saving rate", f"{gross_saving_rate:.1f}%")
    col3.metric("Lidl Plus saved", f"£{lidlplus_saved:,.2f}")
    col4.metric("Regular discounts saved", f"£{total_saved_regular:,.2f}")

    st.markdown("##### Basket")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Avg items per trip",
        f"{avg_basket_size:.1f}" if avg_basket_size else "—",
    )
    unique_stores_visited = filtered_df["store"].nunique()
    col2.metric("Stores visited", f"{unique_stores_visited}")

    # Avg days between shops
    if total_receipts > 1:
        sorted_dates = filtered_df["purchase_date"].sort_values()
        avg_gap_days = (
            sorted_dates.diff().dropna().dt.days.mean()
        )
        col3.metric("Avg days between shops", f"{avg_gap_days:.0f}")
    else:
        col3.metric("Avg days between shops", "—")

    st.markdown("---")

    # ── Spending over time ─────────────────────────────────────────────────────
    st.header("Spending over time")

    if not filtered_df.empty:
        spending_df = filtered_df.copy()

        granularity = st.radio(
            "Group by:", ["Daily", "Weekly", "Monthly"], horizontal=True, key="granularity"
        )

        if granularity == "Daily":
            spending_df["period"] = spending_df["purchase_date"].dt.date
        elif granularity == "Weekly":
            spending_df["period"] = spending_df["purchase_date"].dt.to_period("W").apply(
                lambda p: p.start_time.date()
            )
        else:
            spending_df["period"] = spending_df["purchase_date"].dt.to_period("M").apply(
                lambda p: p.start_time.date()
            )

        period_spending = (
            spending_df.groupby("period")["total_price"].sum().reset_index()
        )
        period_spending.columns = ["Period", "Spending (£)"]
        period_spending["Cumulative (£)"] = period_spending["Spending (£)"].cumsum()

        spending_view = st.radio(
            "View:", ["Period", "Cumulative"], horizontal=True, key="spending_view"
        )

        if spending_view == "Period":
            st.bar_chart(period_spending.set_index("Period")["Spending (£)"])

            col1, col2, col3 = st.columns(3)
            col1.metric(
                f"Avg {granularity.lower()} spend",
                f"£{period_spending['Spending (£)'].mean():.2f}",
            )
            col2.metric(
                "Highest period",
                f"£{period_spending['Spending (£)'].max():.2f}",
            )
            col3.metric(
                "Lowest period",
                f"£{period_spending['Spending (£)'].min():.2f}",
            )
        else:
            st.bar_chart(period_spending.set_index("Period")["Cumulative (£)"])

            total_periods = len(period_spending)
            avg_growth = (
                period_spending["Cumulative (£)"].iloc[-1] / total_periods
                if total_periods > 0
                else 0
            )
            col1, col2 = st.columns(2)
            col1.metric(f"Total {granularity.lower()} periods", total_periods)
            col2.metric(f"Avg {granularity.lower()} growth", f"£{avg_growth:.2f}")
    else:
        st.write("No spending data available for the selected date range.")

    st.markdown("---")

    # ── Basket value distribution ──────────────────────────────────────────────
    st.header("Basket value distribution")

    if not filtered_df.empty:
        bins = [0, 10, 20, 30, 40, 50, 75, 100, float("inf")]
        labels = ["<£10", "£10–20", "£20–30", "£30–40", "£40–50", "£50–75", "£75–100", "£100+"]
        bucket_series = pd.cut(
            filtered_df["total_price"], bins=bins, labels=labels, right=False
        )
        bucket_counts = bucket_series.value_counts().reindex(labels, fill_value=0)
        bucket_df = bucket_counts.reset_index()
        bucket_df.columns = ["Basket size", "Number of trips"]

        col_chart, col_stats = st.columns([2, 1])
        with col_chart:
            st.bar_chart(bucket_df.set_index("Basket size"))
        with col_stats:
            st.markdown("**Distribution stats**")
            median_basket = filtered_df["total_price"].median()
            p25 = filtered_df["total_price"].quantile(0.25)
            p75 = filtered_df["total_price"].quantile(0.75)
            st.metric("Median basket", f"£{median_basket:.2f}")
            st.metric("Lower quartile (25th)", f"£{p25:.2f}")
            st.metric("Upper quartile (75th)", f"£{p75:.2f}")
            most_common_bucket = bucket_counts.idxmax()
            st.metric("Most common range", most_common_bucket)
    else:
        st.write("No data available for the selected date range.")

    st.markdown("---")

    # ── Store breakdown ────────────────────────────────────────────────────────
    st.header("Store breakdown")

    if not filtered_df.empty and filtered_df["store"].nunique() > 0:
        store_stats = (
            filtered_df.groupby("store")
            .agg(
                visits=("total_price", "count"),
                total_spent=("total_price", "sum"),
            )
            .reset_index()
        )
        store_stats["avg_per_visit"] = store_stats["total_spent"] / store_stats["visits"]
        store_stats = store_stats.sort_values("total_spent", ascending=False)

        store_view = st.radio(
            "Show by:", ["Total spent", "Number of visits"], horizontal=True, key="store_view"
        )

        if store_view == "Total spent":
            chart_data = store_stats.set_index("store")[["total_spent"]]
            chart_data.columns = ["Total spent (£)"]
            st.bar_chart(chart_data)
        else:
            chart_data = store_stats.set_index("store")[["visits"]]
            chart_data.columns = ["Number of visits"]
            st.bar_chart(chart_data)

        display_store = store_stats.copy()
        display_store.columns = ["Store", "Visits", "Total spent (£)", "Avg per visit (£)"]
        display_store["Total spent (£)"] = display_store["Total spent (£)"].round(2)
        display_store["Avg per visit (£)"] = display_store["Avg per visit (£)"].round(2)
        st.dataframe(display_store, hide_index=True, use_container_width=True)
    else:
        st.write("No store data available for the selected date range.")

    st.markdown("---")

    # ── Shopping habits ────────────────────────────────────────────────────────
    st.header("Shopping habits")

    if not filtered_df.empty:
        habits_df = filtered_df.copy()
        habits_df["day_of_week"] = habits_df["purchase_date"].dt.day_name()
        habits_df["is_weekend"] = habits_df["purchase_date"].dt.dayofweek >= 5

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Trips by day of week**")
            dow_counts = (
                habits_df["day_of_week"]
                .value_counts()
                .reindex(day_order, fill_value=0)
                .reset_index()
            )
            dow_counts.columns = ["Day", "Trips"]
            st.bar_chart(dow_counts.set_index("Day"))

        with col2:
            st.markdown("**Avg spend by day of week**")
            dow_spend = (
                habits_df.groupby("day_of_week")["total_price"]
                .mean()
                .reindex(day_order)
                .dropna()
                .reset_index()
            )
            dow_spend.columns = ["Day", "Avg spend (£)"]
            st.bar_chart(dow_spend.set_index("Day"))

        date_range_days = (end_datetime - start_datetime).days
        trips_per_week = (total_receipts / date_range_days * 7) if date_range_days > 0 else 0
        busiest_day = habits_df["day_of_week"].value_counts().idxmax() if total_receipts > 0 else "—"

        weekend_trips = habits_df["is_weekend"].sum()
        weekday_trips = total_receipts - weekend_trips
        weekend_spend = habits_df.loc[habits_df["is_weekend"], "total_price"].sum()
        weekday_spend = habits_df.loc[~habits_df["is_weekend"], "total_price"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg trips per week", f"{trips_per_week:.1f}")
        col2.metric("Most common shopping day", busiest_day)
        col3.metric(
            "Weekend vs weekday trips",
            f"{weekend_trips} / {weekday_trips}",
            help="Weekend (Sat–Sun) trips vs weekday (Mon–Fri) trips",
        )
        col4.metric(
            "Weekend vs weekday spend",
            f"£{weekend_spend:.0f} / £{weekday_spend:.0f}",
        )
    else:
        st.write("No data available for the selected date range.")

    st.markdown("---")

    # ── Top items ──────────────────────────────────────────────────────────────
    st.header("Top 10 most purchased items")

    if not filtered_df.empty and not items_df_clean.empty:
        view_mode = st.radio(
            "View by:", ["Quantity", "Total value"], horizontal=True, key="items_view"
        )

        if view_mode == "Quantity":
            grouped = (
                items_df_clean.groupby("name")
                .agg({"quantity": "sum", "unit": "first"})
                .reset_index()
            )
            grouped = grouped.sort_values("quantity", ascending=False).head(10)
            grouped["Total quantity"] = grouped.apply(
                lambda row: (
                    f"{row['quantity']:.3f} {row['unit']}"
                    if row["unit"] == "kg"
                    else f"{int(row['quantity'])} {row['unit']}"
                ),
                axis=1,
            )
            display_df = grouped[["name", "Total quantity"]].copy()
            display_df.columns = ["Item", "Total quantity"]
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            grouped = (
                items_df_clean.groupby("name")["total_value"].sum().reset_index()
            )
            grouped = grouped.sort_values("total_value", ascending=False).head(10)
            grouped.columns = ["Item", "Total spent (£)"]
            grouped["Total spent (£)"] = grouped["Total spent (£)"].round(2)
            st.dataframe(grouped, hide_index=True, use_container_width=True)
    else:
        st.write("No items found in the selected date range.")

    st.markdown("---")

    # ── Item price tracker ─────────────────────────────────────────────────────
    st.header("Item price tracker")
    st.caption("Track how the unit price of a specific product has changed over time.")

    # Build items df from ALL dates (not just filtered) so price history is full
    items_df_all = build_items_df(df)
    if not items_df_all.empty:
        items_df_all_clean = items_df_all[
            ~items_df_all["name"].str.contains(DEPOSIT_PATTERN, case=False, na=False)
        ]
    else:
        items_df_all_clean = items_df_all

    if not items_df_all_clean.empty:
        # Only offer items bought more than once (price trend is meaningless for a single data point)
        repeat_items = (
            items_df_all_clean.groupby("name")["purchase_date"]
            .nunique()
            .loc[lambda s: s > 1]
            .index.tolist()
        )
        repeat_items_sorted = sorted(repeat_items)

        if repeat_items_sorted:
            selected_item = st.selectbox(
                "Select a product", options=repeat_items_sorted, key="price_tracker_item"
            )

            item_history = (
                items_df_all_clean[items_df_all_clean["name"] == selected_item]
                .groupby("purchase_date")["price"]
                .mean()
                .reset_index()
                .sort_values("purchase_date")
            )
            item_history.columns = ["Date", "Unit price (£)"]

            st.line_chart(item_history.set_index("Date"))

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Times purchased", len(item_history))
            col2.metric("Min price", f"£{item_history['Unit price (£)'].min():.2f}")
            col3.metric("Max price", f"£{item_history['Unit price (£)'].max():.2f}")
            first_price = item_history["Unit price (£)"].iloc[0]
            last_price = item_history["Unit price (£)"].iloc[-1]
            price_change_pct = (last_price - first_price) / first_price * 100 if first_price > 0 else 0
            col4.metric(
                "Price change (first → last)",
                f"£{last_price:.2f}",
                delta=f"{price_change_pct:+.1f}%",
                delta_color="inverse",
            )
        else:
            st.write("No items have been bought more than once — price trends require repeat purchases.")
    else:
        st.write("No item data available.")

    st.markdown("---")

    # ── Item purchase frequency ────────────────────────────────────────────────
    st.header("Item purchase frequency")
    st.caption("Staples you buy regularly vs products you only buy occasionally.")

    if not items_df_clean.empty and total_receipts > 0:
        freq_df = (
            items_df_clean.groupby("name")
            .agg(
                times_bought=("purchase_date", "nunique"),
                first_seen=("purchase_date", "min"),
                last_seen=("purchase_date", "max"),
                avg_unit_price=("price", "mean"),
                total_spent=("total_value", "sum"),
            )
            .reset_index()
        )

        # Avg interval: days between first and last purchase divided by (times - 1)
        freq_df["span_days"] = (freq_df["last_seen"] - freq_df["first_seen"]).dt.days
        freq_df["avg_interval_days"] = freq_df.apply(
            lambda r: r["span_days"] / (r["times_bought"] - 1)
            if r["times_bought"] > 1
            else None,
            axis=1,
        )
        # Regularity: what fraction of all trips included this item
        freq_df["trip_frequency_%"] = (freq_df["times_bought"] / total_receipts * 100).round(1)

        freq_view = st.radio(
            "Sort by:",
            ["Most purchased", "Most regular (% of trips)", "Highest total spend"],
            horizontal=True,
            key="freq_view",
        )

        sort_col = {
            "Most purchased": "times_bought",
            "Most regular (% of trips)": "trip_frequency_%",
            "Highest total spend": "total_spent",
        }[freq_view]

        top_freq = freq_df.sort_values(sort_col, ascending=False).head(20).copy()
        top_freq["first_seen"] = top_freq["first_seen"].dt.date
        top_freq["last_seen"] = top_freq["last_seen"].dt.date
        top_freq["avg_interval_days"] = top_freq["avg_interval_days"].apply(
            lambda x: f"{x:.0f} days" if pd.notna(x) else "—"
        )
        top_freq["avg_unit_price"] = top_freq["avg_unit_price"].apply(lambda x: f"£{x:.2f}")
        top_freq["total_spent"] = top_freq["total_spent"].apply(lambda x: f"£{x:.2f}")

        display_freq = top_freq[
            [
                "name",
                "times_bought",
                "trip_frequency_%",
                "avg_interval_days",
                "avg_unit_price",
                "total_spent",
                "first_seen",
                "last_seen",
            ]
        ].copy()
        display_freq.columns = [
            "Item",
            "Times bought",
            "% of trips",
            "Avg interval",
            "Avg unit price",
            "Total spent",
            "First seen",
            "Last seen",
        ]
        st.dataframe(display_freq, hide_index=True, use_container_width=True)
    else:
        st.write("No item data available for the selected date range.")

    st.markdown("---")

    # ── Receipt explorer ───────────────────────────────────────────────────────
    st.header("Receipt explorer")
    st.caption("Browse and inspect individual receipts.")

    if not filtered_df.empty:
        receipt_summary = filtered_df[["purchase_date", "store", "total_price"]].copy()
        receipt_summary["purchase_date_str"] = receipt_summary["purchase_date"].dt.strftime(
            "%Y-%m-%d"
        )

        # Item count per receipt
        item_counts = filtered_df["items"].apply(
            lambda items: sum(
                float(str(i.get("quantity", 1)).replace(",", "."))
                for i in items
                if not str(i.get("name", "")).lower().strip() in ["pfand", "deposit return", "bottle return"]
            )
            if isinstance(items, list)
            else 0
        )
        receipt_summary["items"] = item_counts.values

        receipt_summary = receipt_summary.sort_values("purchase_date", ascending=False)
        receipt_summary["total_price"] = receipt_summary["total_price"].round(2)

        display_receipts = receipt_summary[
            ["purchase_date_str", "store", "total_price", "items"]
        ].copy()
        display_receipts.columns = ["Date", "Store", "Total (£)", "Items"]

        st.dataframe(display_receipts, hide_index=True, use_container_width=True)

        st.markdown("**Inspect a receipt**")
        receipt_options = receipt_summary["purchase_date_str"].tolist()
        # Ensure uniqueness (same date different stores)
        receipt_labels = [
            f"{row['purchase_date_str']} — {row['store']} — £{row['total_price']:.2f}"
            for _, row in receipt_summary.iterrows()
        ]
        selected_label = st.selectbox(
            "Select receipt", options=receipt_labels, key="receipt_select"
        )

        selected_idx = receipt_labels.index(selected_label)
        selected_receipt_date = receipt_summary.iloc[selected_idx]["purchase_date"]
        selected_store = receipt_summary.iloc[selected_idx]["store"]

        match = filtered_df[
            (filtered_df["purchase_date"] == selected_receipt_date)
            & (filtered_df["store"] == selected_store)
        ]

        if not match.empty:
            receipt_row = match.iloc[0]
            items_list = receipt_row.get("items", [])

            if isinstance(items_list, list) and items_list:
                item_rows = []
                for item in items_list:
                    try:
                        qty = float(str(item.get("quantity", 1)).replace(",", "."))
                        unit_price = to_float(item.get("price", 0))
                        unit = item.get("unit", "each")
                        line_total = qty * unit_price
                    except (ValueError, TypeError):
                        qty, unit_price, unit, line_total = 1.0, 0.0, "each", 0.0

                    qty_str = (
                        f"{qty:.3f} {unit}" if unit == "kg" else f"{int(qty)} {unit}"
                    )
                    item_rows.append(
                        {
                            "Item": item.get("name", ""),
                            "Qty": qty_str,
                            "Unit price (£)": f"£{unit_price:.2f}",
                            "Line total (£)": f"£{line_total:.2f}",
                        }
                    )

                items_detail_df = pd.DataFrame(item_rows)
                st.dataframe(items_detail_df, hide_index=True, use_container_width=True)

                col1, col2, col3 = st.columns(3)
                col1.metric("Items on receipt", len(item_rows))
                col2.metric("Total paid", f"£{to_float(receipt_row.get('total_price', 0)):.2f}")
                saved_r = to_float(receipt_row.get("saved_amount", 0))
                saved_lp = to_float(receipt_row.get("lidlplus_saved_amount", 0))
                col3.metric("Saved on this trip", f"£{saved_r + saved_lp:.2f}")
    else:
        st.write("No receipts available for the selected date range.")

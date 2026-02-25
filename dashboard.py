import streamlit as st
import pandas as pd
import json
import os

DATA_FILE = "lidl_receipts.json"


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


data = load_data(DATA_FILE)

if data:
    df = pd.DataFrame(data)

    def to_float(x):
        if x is None or x == "" or str(x).strip() == "":
            return 0.0
        return float(str(x).replace(",", "."))

    df["purchase_date"] = pd.to_datetime(df["purchase_date"], format="%Y.%m.%d")
    df["total_price"] = df["total_price"].apply(to_float)
    df["saved_amount"] = df["saved_amount"].apply(to_float)
    df["lidlplus_saved_amount"] = (
        df["lidlplus_saved_amount"].apply(to_float)
        if "lidlplus_saved_amount" in df.columns
        else 0.0
    )

    initial_count = len(df)
    df = df[df["items"].notna()]
    df = df[df["items"].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    filtered_out = initial_count - len(df)

    if filtered_out > 0:
        st.info(
            f"{filtered_out} receipt(s) were filtered out because they had no total "
            "price or no items."
        )

    st.set_page_config(
        layout="wide", page_title="Lidl Receipts Dashboard", page_icon="🛒"
    )

    st.markdown(
        """
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Lidl+ Dashboard")

    st.sidebar.header("Filter by date")
    min_date = df["purchase_date"].min().date()
    max_date = df["purchase_date"].max().date()

    start_date = st.sidebar.date_input(
        "Start date", min_date, min_value=min_date, max_value=max_date
    )
    end_date = st.sidebar.date_input(
        "End date", max_date, min_value=min_date, max_value=max_date
    )

    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)

    filtered_df = df[
        (df["purchase_date"] >= start_datetime) & (df["purchase_date"] < end_datetime)
    ]

    st.header("Key metrics")

    total_receipts = len(filtered_df)
    total_spent = filtered_df["total_price"].sum()
    total_saved = filtered_df["saved_amount"].sum()

    if "lidlplus_saved_amount" in filtered_df.columns:
        lidlplus_saved = filtered_df["lidlplus_saved_amount"].sum()
    else:
        lidlplus_saved = 0

    st.markdown("##### Overview")
    col1, col2 = st.columns(2)
    col1.metric("Total spent", f"£{total_spent:,.2f}")
    col2.metric("Total receipts", f"{total_receipts}")

    st.markdown("##### Lidl Plus savings")
    col1, col2 = st.columns(2)
    lidlplus_percentage = (lidlplus_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric("Lidl Plus saved", f"£{lidlplus_saved:,.2f}")
    col2.metric("Lidl Plus saving rate", f"{lidlplus_percentage:.1f}%")

    st.markdown("##### Regular discounts")
    col1, col2 = st.columns(2)
    regular_percentage = (total_saved / total_spent * 100) if total_spent > 0 else 0
    col1.metric("Regular discounts saved", f"£{total_saved:,.2f}")
    col2.metric("Regular saving rate", f"{regular_percentage:.1f}%")

    st.markdown("---")

    st.header("Spending over time")

    if not filtered_df.empty:
        spending_over_time = filtered_df.copy()
        spending_over_time["date"] = spending_over_time["purchase_date"].dt.date
        daily_spending = (
            spending_over_time.groupby("date")["total_price"].sum().reset_index()
        )
        daily_spending.columns = ["Date", "Daily spending (£)"]
        daily_spending["Cumulative spending (£)"] = daily_spending[
            "Daily spending (£)"
        ].cumsum()

        spending_view = st.radio(
            "View:", ["Daily", "Cumulative"], horizontal=True, key="spending_view"
        )

        if spending_view == "Daily":
            st.bar_chart(daily_spending.set_index("Date")["Daily spending (£)"])

            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Average daily spend",
                f"£{daily_spending['Daily spending (£)'].mean():.2f}",
            )
            col2.metric(
                "Highest single-day spend",
                f"£{daily_spending['Daily spending (£)'].max():.2f}",
            )
            col3.metric(
                "Lowest single-day spend",
                f"£{daily_spending['Daily spending (£)'].min():.2f}",
            )

        else:
            st.bar_chart(
                daily_spending.set_index("Date")["Cumulative spending (£)"]
            )

            total_days = len(daily_spending)
            avg_daily_growth = (
                daily_spending["Cumulative spending (£)"].iloc[-1] / total_days
                if total_days > 0
                else 0
            )

            col1, col2 = st.columns(2)
            col1.metric("Total days", total_days)
            col2.metric("Average daily growth", f"£{avg_daily_growth:.2f}")
    else:
        st.write("No spending data available for the selected date range.")

    st.markdown("---")

    st.header("Top 10 most purchased items")

    if not filtered_df.empty:
        view_mode = st.radio(
            "View by:", ["Quantity", "Total value"], horizontal=True
        )

        items_data = []
        for _, row in filtered_df.iterrows():
            if row.get("items") and isinstance(row["items"], list):
                for item in row["items"]:
                    try:
                        quantity_str = str(item.get("quantity", 1))
                        quantity = float(quantity_str.replace(",", "."))
                        price = to_float(item.get("price", 0))
                        unit = item.get("unit", "each")
                    except (ValueError, TypeError):
                        quantity = 1.0
                        price = 0
                        unit = "each"

                    items_data.append(
                        {
                            "name": item["name"],
                            "quantity": quantity,
                            "price": price,
                            "unit": unit,
                            "total_value": quantity * price,
                        }
                    )

        if items_data:
            items_df = pd.DataFrame(items_data)

            # Filter out deposit return lines
            deposit_keywords = ["pfand", "deposit return", "bottle return"]
            pattern = "|".join(deposit_keywords)
            items_df = items_df[
                ~items_df["name"].str.contains(pattern, case=False, na=False)
            ]

            if view_mode == "Quantity":
                grouped = (
                    items_df.groupby("name")
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
                st.dataframe(display_df, width="stretch", hide_index=True)

            else:
                grouped = (
                    items_df.groupby("name")["total_value"].sum().reset_index()
                )
                grouped = grouped.sort_values("total_value", ascending=False).head(10)
                grouped.columns = ["Item", "Total spent (£)"]
                grouped["Total spent (£)"] = grouped["Total spent (£)"].round(2)
                st.dataframe(grouped, width="stretch", hide_index=True)
        else:
            st.write("No items found in the selected date range.")

    else:
        st.write("No data available for the selected date range.")

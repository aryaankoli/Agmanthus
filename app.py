import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="CloudSCOUT | Cloud Cost Dashboard",
    page_icon="☁️",
    layout="wide"
)

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("data/cloud_billing.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# Dashboard title
st.title("☁️ Agmanthus")
st.subheader("Multi-Cloud Cost Management Dashboard")
st.caption("Monitor and analyze Clouds spending.")

# Sidebar filters
st.sidebar.header("Filters")

# Date filter
start_date = st.sidebar.date_input(
    "Start Date",
    value=df["date"].min().date(),
    min_value=df["date"].min().date(),
    max_value=df["date"].max().date()
)

end_date = st.sidebar.date_input(
    "End Date",
    value=df["date"].max().date(),
    min_value=df["date"].min().date(),
    max_value=df["date"].max().date()
)

providers = st.sidebar.multiselect(
    "Cloud Provider",
    options=sorted(df["provider"].unique()),
    default=sorted(df["provider"].unique())
)

services = st.sidebar.multiselect(
    "Service",
    options=sorted(df["service"].unique()),
    default=sorted(df["service"].unique())
)


filtered_df = df[
    df["provider"].isin(providers)
    & df["service"].isin(services)
    & (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
].copy()

# KPI calculations
if filtered_df.empty:
    st.warning("No billing records found. Please select at least one cloud provider and service.")
    st.stop()
total_cost = filtered_df["cost"].sum()
provider_cost = filtered_df.groupby("provider")["cost"].sum()
service_cost = filtered_df.groupby("service")["cost"].sum()

most_expensive_provider = (
    provider_cost.idxmax() if not provider_cost.empty else "N/A"
)
most_expensive_service = (
    service_cost.idxmax() if not service_cost.empty else "N/A"
)
daily_average = (
    filtered_df.groupby("date")["cost"].sum().mean()
    if not filtered_df.empty else 0
)

# Daily cost comparison
daily_cost = (
    filtered_df.groupby("date")["cost"].sum().sort_index()
)

if len(daily_cost) >= 2:
    previous_day_cost = daily_cost.iloc[-2]
    latest_day_cost = daily_cost.iloc[-1]

    if previous_day_cost != 0:
        daily_change = (
            (latest_day_cost - previous_day_cost)
            / previous_day_cost
        ) * 100
    else:
        daily_change = None
else:
    daily_change = None


# KPI cards
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Cloud Cost", f"₹{total_cost:,.0f}")
c2.metric("Highest-Cost Provider", most_expensive_provider)
c3.metric("Highest-Cost Service", most_expensive_service)
c4.metric(
    "Average Daily Cost",
    f"₹{daily_average:,.0f}",
    delta=(
        f"{daily_change:+.1f}% vs previous day"
        if daily_change is not None
        else None
    ),
    delta_color="inverse"
)

st.divider()

# Provider-wise cost

left, right = st.columns(2)

with left:
    st.subheader("Cost by Cloud Provider")

    # Step 1: Create the dataframe
    provider_chart = (
        filtered_df.groupby("provider", as_index=False)["cost"].sum()
    )

    # Step 2: Create the chart
    fig = px.bar(
        provider_chart,
        x="provider",
        y="cost",
        color="provider",
        title="Total Spending by Provider",
        labels={
            "provider": "Cloud Provider",
            "cost": "Total Cost (₹)"
        },
        template="plotly_white"
    )

    # Step 3: Display values above bars
    fig.update_traces(
        texttemplate="₹%{y:,.0f}",
        textposition="outside"
    )

    # Step 4: Improve layout
    fig.update_layout(
        showlegend=False,
        yaxis_title="Cost (₹)",
        xaxis_title="Cloud Provider"
    )

    st.plotly_chart(fig, use_container_width=True)

# Service-wise cost
with right:
    st.subheader("Cost by Service")

    service_chart = (
        filtered_df.groupby("service", as_index=False)["cost"].sum()
    )

    fig = px.pie(
        service_chart,
        names="service",
        values="cost",
        title="Spending Distribution by Service",
        hole=0.4,
        template="plotly_white"
    )

    fig.update_traces(
        textinfo="label+percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Cost: ₹%{value:,.0f}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# Daily cost trend
st.subheader("Daily Cloud Spending Trend")

daily_cost = (
    filtered_df.groupby("date", as_index=False)["cost"].sum()
)

fig = px.line(
    daily_cost,
    x="date",
    y="cost",
    markers=True,
    title="Daily Total Cloud Cost",
    labels={
        "date": "Date",
        "cost": "Total Cost (₹)"
    },
    template="plotly_white"
)

fig.update_traces(
    line=dict(width=3),
    marker=dict(size=9),
    hovertemplate=(
        "Date: %{x|%d %b %Y}<br>"
        "Total Cost: ₹%{y:,.0f}"
        "<extra></extra>"
    )
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Cost (₹)",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)


# Cloud Cost Breakdown
st.subheader("Cloud Cost Breakdown")

granularity = st.selectbox(
    "Group spending by",
    ["Auto", "Daily", "Monthly", "Quarterly"],
    index=0
)

# Automatically choose granularity based on selected date range
selected_days = (end_date - start_date).days + 1

if granularity == "Auto":
    if selected_days <= 31:
        selected_granularity = "Daily"
    elif selected_days <= 365:
        selected_granularity = "Monthly"
    else:
        selected_granularity = "Quarterly"
else:
    selected_granularity = granularity

# Group records by the chosen time period
if selected_granularity == "Daily":
    periods = filtered_df["date"].dt.to_period("D")
elif selected_granularity == "Monthly":
    periods = filtered_df["date"].dt.to_period("M")
else:
    periods = filtered_df["date"].dt.to_period("Q")

daily_breakdown = (
    filtered_df.assign(Period=periods.astype(str))
    .groupby("Period", as_index=False)
    .agg(
        Total_Cost=("cost", "sum"),
        Services_Used=("service", "nunique"),
        Providers_Used=("provider", "nunique")
    )
    .sort_values("Period")
    .reset_index(drop=True)
)

# Format costs in INR
daily_breakdown["Total_Cost"] = daily_breakdown["Total_Cost"].map(
    lambda cost: f"₹{cost:,.0f}"
)

st.caption(f"Showing {selected_granularity.lower()} spending.")

st.dataframe(
    daily_breakdown,
    use_container_width=True,
    hide_index=True
)

# Top 5 Most Expensive Resources
st.subheader("Top 5 Most Expensive Resources")

resource_cost = (
    filtered_df.groupby(
        ["resource_id", "provider", "service"],
        as_index=False
    )["cost"]
    .sum()
    .sort_values("cost", ascending=False)
    .head(5)
)

resource_cost["cost"] = resource_cost["cost"].map(
    lambda cost: f"₹{cost:,.0f}"
)

st.dataframe(
    resource_cost,
    use_container_width=True,
    hide_index=True
)

# Export filtered billing data
st.subheader("Export Data")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Billing Records (CSV)",
    data=csv_data,
    file_name="agmanthus_billing_records.csv",
    mime="text/csv"
)
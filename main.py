import helper
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide", page_title="Aadhaar Analytics Dashboard")

MODES = {
    "New Enrollment": {
        "path": helper.ENROLLMENT_DIR,
        "col_map": {
            "age_0_5": "age_0_5", 
            "age_5_17": "age_5_17", 
            "age_18_greater": "age_18_greater"
        },
        "description": "Analysis of new Aadhaar generations."
    },
    "Biometric Updates": {
        "path": helper.BIOMETRIC_DIR,
        "col_map": {
            "bio_age_5_17": "age_5_17", 
            "bio_age_17_": "age_18_greater"
        },
        "description": "Updates to Iris, Fingerprints, and Photos."
    },
    "Demographic Updates": {
        "path": helper.DEMOGRAPHIC_DIR,
        "col_map": {
            "demo_age_5_17": "age_5_17", 
            "demo_age_17_": "age_18_greater"
        },
        "description": "Updates to Name, Address, DOB, Mobile, etc."
    }
}

st.sidebar.title("Dashboard Controls")
selected_mode = st.sidebar.radio("Select Analysis Mode", list(MODES.keys()))
current_config = MODES[selected_mode]

st.sidebar.markdown("---")
st.sidebar.info(current_config["description"])

@st.cache_data
def load_and_clean_data(mode_name):
    config = MODES[mode_name]
    
    df = helper.load_csv(config["path"])
    
    # Standardize column names
    df = df.rename(columns=config["col_map"])
    
    # Fill missing standard columns
    expected_cols = ["age_0_5", "age_5_17", "age_18_greater"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0
            
    df = helper.filter_state_data(df)
    df = helper.filter_district_data(df)
    helper.bad_state_labels(df)
    
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["month"] = df["date"].dt.strftime("%B") # type: ignore
    
    df["total"] = df["age_0_5"] + df["age_5_17"] + df["age_18_greater"]
    
    return df

try:
    df = load_and_clean_data(selected_mode)
except Exception as e:
    st.error(f"Error loading data for {selected_mode}: {e}")
    st.stop()

st.title(f"Aadhaar Data: {selected_mode}")
st.markdown(f"**Total Processed:** {df['total'].sum():,}")

st.subheader("1. Age Group Distribution by State")
chart_data = df.groupby("state")[["age_0_5", "age_5_17", "age_18_greater"]].sum().reset_index()
chart_data.columns = ["State", "Age (0-5)", "Age (5-17)", "Age (>18)"]
chart_melt = chart_data.melt(id_vars="State", var_name="Age Group", value_name="Count")

fig_age = px.bar(
    chart_melt, x="State", y="Count", color="Age Group",
    title=f"{selected_mode} by State & Age", height=600
)
st.plotly_chart(fig_age, width="stretch")

# states with low enrollment
st.subheader(f"States with low {selected_mode.lower()} (< 20%)")
required_stats = df.groupby("state")["total"].sum().reset_index()
state_total = df["total"].sum()
required_stats["percentage"] = (required_stats["total"] / state_total) * 100

low_state_rates = required_stats[required_stats["percentage"] < 20].sort_values("percentage", ascending=True)

if not low_state_rates.empty:
    st.warning(f"States with < 20% {selected_mode.lower()}")
    display_table = low_state_rates[["state", "total", "percentage"]].copy()
    display_table.columns = ["State", "Total", "Percentage (%)"]
    display_table["Percentage (%)"] = display_table["Percentage (%)"].map("{:.2f}%".format)
    display_table["Total"] = display_table["Total"].map("{:,}".format)

    st.dataframe(display_table, width="stretch", hide_index=True)

else:
    st.success(f"States with < 20% {selected_mode.lower()}")

# states with low youth enrollment
st.subheader(f"States with Low youth {selected_mode.lower()} (< 20%)")

# group by state
state_stats = df.groupby("state")[["age_0_5", "age_5_17", "total"]].sum().reset_index()
state_stats["youth_total"] = state_stats["age_0_5"] + state_stats["age_5_17"]
state_stats["youth_percentage"] = (state_stats["youth_total"] / state_stats["total"]) * 100

# filter states with < 20% youth enrollment/update
low_youth_rates = state_stats[state_stats["youth_percentage"] < 20].sort_values("youth_percentage", ascending=True)

if not low_youth_rates.empty:
    st.warning(f"States with < 20% youth {selected_mode.lower()}")
    display_table = low_youth_rates[["state", "total", "youth_percentage"]].copy()
    display_table.columns = ["State", "Total", "Youth % (0-17)"]
    display_table["Youth % (0-17)"] = display_table["Youth % (0-17)"].map("{:.2f}%".format)
    display_table["Total"] = display_table["Total"].map("{:,}".format)

    st.dataframe(display_table, width="stretch", hide_index=True)

else:
    st.success(f"States with < 20% youth {selected_mode.lower()}")

# districts with low youth enrollment/update
st.subheader(f"Districts with Low youth {selected_mode.lower()} (< 20%)")

# group by both State and district so we don't lose the State name
district_stats = df.groupby(["state", "district"])[["age_0_5", "age_5_17", "total"]].sum().reset_index()

district_stats["youth_total"] = district_stats["age_0_5"] + district_stats["age_5_17"]
district_stats["youth_percentage"] = (district_stats["youth_total"] / district_stats["total"]) * 100

low_youth_rates_district = district_stats[district_stats["youth_percentage"] < 20].sort_values("youth_percentage", ascending=True)

if not low_youth_rates_district.empty:
    st.warning(f"Districts with < 20% {selected_mode.lower()}")
    display_table = low_youth_rates_district[["state", "district", "total", "youth_percentage"]].copy()
    
    # format for clean display
    display_table.columns = ["State", "District", "Total", "Youth % (0-17)"]
    display_table["Youth % (0-17)"] = display_table["Youth % (0-17)"].map("{:.2f}%".format)
    display_table["Total"] = display_table["Total"].map("{:,}".format)

    st.dataframe(display_table, width="stretch", hide_index=True)

else:
    st.success(f"No districts with youth < 20% {selected_mode.lower()}")


st.subheader("2. Trends Over Time")
trend_data = df.groupby("date")[["age_0_5", "age_5_17", "age_18_greater", "total"]].sum().reset_index()
trend_data.columns = ["Date", "Age (0-5)", "Age (5-17)", "Age (>18)", "Total"]
trend_melt = trend_data.melt(id_vars="Date", var_name="Category", value_name="Count")

fig_trend = px.line(
    trend_melt, x="Date", y="Count", color="Category",
    title=f"National {selected_mode} Trends", height=500
)
st.plotly_chart(fig_trend, width="stretch")

st.divider()
st.subheader("3. State-Level Analysis")
states = df["state"].unique()
state_choice = st.selectbox("Select State", states)

state_data = df[df["state"] == state_choice]
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**District-wise {selected_mode}**")
    dist_data = state_data.groupby("district")["total"].sum().reset_index()
    fig_dist = px.pie(
        dist_data, 
        names="district", 
        values="total", 
        title=f"District Distribution in {state_choice}",
        height=600,
        hole=0.4
    )
    fig_dist.update_traces(textposition='inside', textinfo='percent+label')
    
    st.plotly_chart(fig_dist, width="stretch")

with col2:
    st.markdown(f"**{state_choice} Timeline**")
    st_trend = state_data.groupby("date")[["age_0_5", "age_5_17", "age_18_greater"]].sum().reset_index()
    st_trend.columns = ["Date", "Age (0-5)", "Age (5-17)", "Age (>18)"]
    st_melt = st_trend.melt(id_vars="Date", var_name="Age Group", value_name="Count")
    fig_st_line = px.line(st_melt, x="Date", y="Count", color="Age Group", height=600)
    st.plotly_chart(fig_st_line, width="stretch")

st.subheader("4. Intensity Heatmaps")
st.write("#### By Month (Seasonality)")

heatmap_time = df.pivot_table(index="state", columns="month", values="total", aggfunc="sum")

months_order = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
existing_months = [m for m in months_order if m in heatmap_time.columns]
heatmap_time = heatmap_time[existing_months]

fig_heat = px.imshow(
    heatmap_time,
    labels=dict(x="Month", y="State", color="Count"),
    color_continuous_scale="RdBu_r",
    aspect="auto", height=800
)
st.plotly_chart(fig_heat, width="stretch")

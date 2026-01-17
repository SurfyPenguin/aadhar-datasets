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
chart_melt = chart_data.melt(id_vars="state", var_name="Age Group", value_name="Count")

fig_age = px.bar(
    chart_melt, x="state", y="Count", color="Age Group",
    title=f"{selected_mode} by State & Age", height=600
)
st.plotly_chart(fig_age, width="stretch")

st.subheader("2. Trends Over Time")
trend_data = df.groupby("date")[["age_0_5", "age_5_17", "age_18_greater", "total"]].sum().reset_index()
trend_melt = trend_data.melt(id_vars="date", var_name="Category", value_name="Count")

fig_trend = px.line(
    trend_melt, x="date", y="Count", color="Category",
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
    st_melt = st_trend.melt(id_vars="date", var_name="Age Group", value_name="Count")
    fig_st_line = px.line(st_melt, x="date", y="Count", color="Age Group", height=600)
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
import pandas as pd
import streamlit as st

# access data
df = pd.read_csv("./api_data_aadhar_enrolment/api_data_aadhar_enrolment_1000000_1006029.csv")

state_list = df.state.unique()

st.title("Aadhar Trends Dashboard")
st.subheader("Enrollments")

selected_state = st.selectbox("Select a State", state_list)
filter_state = df[df["state"] == selected_state]

total_enrollments = filter_state["age_0_5"].sum()
st.metric("Total Enrollments", total_enrollments)

st.write("District Wise")
dist_wise = filter_state.groupby("district")["age_0_5"].sum()
st.bar_chart(dist_wise)
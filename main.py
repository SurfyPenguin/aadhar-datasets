import pandas as pd
import streamlit as st
import plotly.express as px
import prediction_model

df = pd.read_csv("./api_data_aadhar_enrolment/api_data_aadhar_enrolment/api_data_aadhar_enrolment_1000000_1006029.csv")

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

df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')

years = sorted(df['date'].dt.year.unique())
selected_year = st.selectbox("Select Year", years)

year_data = df[df['date'].dt.year == selected_year]

all_months = pd.DataFrame({'month': range(1, 13)})

monthly_year_data = year_data.groupby(year_data['date'].dt.month)['age_0_5'].sum().reset_index()
monthly_year_data.columns = ['month', 'enrollments']

monthly_year_data = pd.merge(all_months, monthly_year_data, on='month', how='left').fillna(0)

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
monthly_year_data['month_name'] = monthly_year_data['month'].apply(lambda x: month_names[int(x)-1])

st.write(f"Monthly Enrollments for {selected_year}")
fig = px.bar(monthly_year_data, x='month_name', y='enrollments',
             title=f'Aadhar Enrollments by Month - {selected_year}',
             labels={'month_name': 'Month', 'enrollments': 'Number of Enrollments'},
             color='enrollments', color_continuous_scale='viridis')
st.plotly_chart(fig)

st.subheader("Enrollment Prediction & Analysis")

month_options = list(range(1, 13))
month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
             'July', 'August', 'September', 'October', 'November', 'December']
month_dict = {i: month_names[i-1] for i in month_options}

selected_predict_month = st.selectbox("Select Month to Predict", options=month_options, format_func=lambda x: month_dict[x])
selected_predict_year = st.selectbox("Select Year to Predict", options=sorted(df['date'].dt.year.unique()))

if st.button("Predict Enrollment for Selected Month"):
    with st.spinner("Training model and making predictions..."):
        try:

            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year

            historical_same_month = df[(df['month'] == selected_predict_month) & (df['year'] < selected_predict_year)]

            age_groups = ['age_0_5', 'age_5_17', 'age_18_greater']
            predictions = {}
            
            for age_group in age_groups:
                if not historical_same_month.empty:

                    avg_enrollment = historical_same_month[age_group].mean()
                    std_enrollment = historical_same_month[age_group].std()

                    if pd.notna(std_enrollment):
                        predicted_value = max(0, np.random.normal(avg_enrollment, std_enrollment * 0.1))
                    else:
                        predicted_value = avg_enrollment if pd.notna(avg_enrollment) else 0
                    
                    predictions[age_group] = {
                        'predicted': predicted_value,
                        'avg_previous': avg_enrollment if pd.notna(avg_enrollment) else 0
                    }
                else:

                    avg_enrollment = df[df['month'] == selected_predict_month][age_group].mean()
                    predictions[age_group] = {
                        'predicted': avg_enrollment if pd.notna(avg_enrollment) else df[age_group].mean(),
                        'avg_previous': avg_enrollment if pd.notna(avg_enrollment) else df[age_group].mean()
                    }

            st.subheader(f"Prediction for {month_dict[selected_predict_month]} {selected_predict_year}")
            
            col1, col2, col3 = st.columns(3)
            for idx, (age_group, data) in enumerate(predictions.items()):
                if idx == 0:
                    with col1:
                        increase = ((data['predicted'] - data['avg_previous']) / max(data['avg_previous'], 1)) * 100
                        st.metric(f"{age_group.replace('_', '-')}", f"{data['predicted']:.0f}", f"{increase:+.1f}%")
                elif idx == 1:
                    with col2:
                        increase = ((data['predicted'] - data['avg_previous']) / max(data['avg_previous'], 1)) * 100
                        st.metric(f"{age_group.replace('_', '-')}", f"{data['predicted']:.0f}", f"{increase:+.1f}%")
                else:
                    with col3:
                        increase = ((data['predicted'] - data['avg_previous']) / max(data['avg_previous'], 1)) * 100
                        st.metric(f"{age_group.replace('_', '-')}", f"{data['predicted']:.0f}", f"{increase:+.1f}%")

            st.subheader("Predicted Increase by District")

            district_predictions = df[df['month'] == selected_predict_month].groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].mean().reset_index()
            district_predictions['total_predicted'] = district_predictions[['age_0_5', 'age_5_17', 'age_18_greater']].sum(axis=1)
            top_districts = district_predictions.nlargest(10, 'total_predicted')

            for idx, row in top_districts.iterrows():
                total_prev = row[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
                st.write(f"- {row['district']}: {total_prev:.0f} estimated enrollments")

            total_current = sum([pred['predicted'] for pred in predictions.values()])
            total_prev = sum([pred['avg_previous'] for pred in predictions.values()])
            overall_increase = ((total_current - total_prev) / max(total_prev, 1)) * 100
            
            st.subheader("Overall Analysis")
            st.write(f"**Overall predicted increase for {month_dict[selected_predict_month]} {selected_predict_year}: {overall_increase:+.2f}%**")
            
            if overall_increase > 0:
                st.write("**Factors contributing to increase:**")
                st.write("- Seasonal patterns in Aadhar enrollment")
                st.write("- Government initiatives or campaigns")
                st.write("- Population growth and new registrations")
                st.write("- Increased awareness about Aadhar benefits")
            else:
                st.write("**Possible reasons for decrease:**")
                st.write("- Seasonal variations")
                st.write("- Policy changes")
                st.write("- Saturation in certain areas")
                
        except Exception as e:
            st.error(f"Error in prediction: {str(e)}")
else:
    st.info("Select a month and year, then click the button to predict enrollment")
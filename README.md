# Aadhar Trends Dashboard

A Streamlit dashboard for visualizing Aadhar enrollment data across Indian states and districts.

## Features

- Interactive state selection dropdown
- District-wise enrollment visualization
- Age group breakdown of enrollments
- Real-time metric display for total enrollments

## Dependencies

This project uses the following main dependencies:
- pandas: For data manipulation and analysis
- streamlit: For creating the interactive web dashboard
- Other supporting libraries as defined in pyproject.toml

## Installation

1. Clone the repository
2. Install the dependencies using uv:
   ```
   uv sync
   ```
3. Ensure you have the required data file in `./api_data_aadhar_enrolment/api_data_aadhar_enrolment_1000000_1006029.csv`

## Usage

Run the Streamlit application:
```
streamlit run main.py
```

The dashboard will be available at `http://localhost:8501`

## Data Structure

The application expects a CSV file with the following columns:
- `state`: Name of the state
- `district`: Name of the district
- `age_0_5`, `age_6_10`, `age_11_15`, etc.: Enrollment counts for each age group

## Project Analysis

This project is designed to visualize Aadhar enrollment trends across different states and districts in India. It provides insights into demographic distribution of Aadhar enrollments through an interactive dashboard.
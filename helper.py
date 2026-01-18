import glob
import pandas as pd
import streamlit as st

ENROLLMENT_DIR = "./api_data_aadhar_enrolment"
BIOMETRIC_DIR = "./api_data_aadhar_biometric"
DEMOGRAPHIC_DIR = "./api_data_aadhar_demographic"

OFFICIAL_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
    "Uttaranchal", "Tamilnadu", "Chhatisgarh"
]

CORRECTIONS = corrections = {
    # Invalid Uttar Pradesh Names 
    "Uttar P10000Radesh": "Uttar Pradesh",

    # Different wordings of West Bengal
    "Westbengal": "West Bengal",
    "West Bangal": "West Bengal",
    "West\xa0 Bengal": "West Bengal", # This handles the "non-breaking space" ghost character
    "West  Bengal": "West Bengal",   # Handles double spaces
    
    # Old names just in case
    "Orissa": "Odisha",
    "Pondicherry": "Puducherry",

    # "and", "And" and "&" conflict
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Andaman & Nicobar Islands": "Andaman and Nicobar Islands",
    
    # lowercasing "And" from J&K
    "?": "Unknown",
    "Jammu And Kashmir": "Jammu and Kashmir",
    "Andaman And Nicobar Islands": "Andaman and Nicobar Islands",

    # Merge Dadar and Nagar Haveli & Daman and Diu
    "Dadra & Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "Dadra And Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman & Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "The Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",

    # fix: cities/districts appearing in State Column
    "West Bengli": "West Bengal",           # Typo
    "Jaipur": "Rajasthan",                  # City
    "Nagpur": "Maharashtra",                # City
    "Darbhanga": "Bihar",                   # District
    "Madanapalle": "Andhra Pradesh",        # City
    "Balanagar": "Telangana",               # Locality (Hyderabad)
    "Raja Annamalai Puram": "Tamil Nadu",   # Locality (Chennai)
    "Puttenahalli": "Karnataka",            # Locality (Bengaluru)
}

DISTRICT_CORRECTIONS = {
    "Dadra & Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "Dadra And Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman & Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman": "Dadra and Nagar Haveli and Daman and Diu",
    "Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "The Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "?": "Unknown",
}

@st.cache_data
def load_csv(file: str) -> pd.DataFrame:
    files: list[str] = glob.glob(f"./{file}/*.csv")

    if not files:
        print(f"No files found in {file}")

    dfs: list[pd.DataFrame] = []
    try:
        for f in files:
            df = pd.read_csv(f)
            dfs.append(df)

    except Exception as e:
        print(f"Error: {e}")

    if dfs:
        return pd.concat(dfs)
    return pd.DataFrame()

@st.cache_data
def filter_state_data(df: pd.DataFrame) -> pd.DataFrame:
    # Remove numeric state values (filtering)
    df = df[~df["state"].astype(str).str.isnumeric()]

    # Normalize capitalization (title case) & any leadig / trailing asterisks
    df.loc[:, "state"] = df.loc[:, "state"].str.title().str.replace("*", "", regex=False).str.strip()

    # Apply the dictionary corrections
    df.loc[:, "state"] = df.loc[:, "state"].replace(CORRECTIONS)

    return df

def bad_state_labels(df: pd.DataFrame) -> bool:
    bad_labels = set(df["state"].unique()) - set(OFFICIAL_STATES)
    if bad_labels:
        print(f"Bad Labels: {bad_labels}")
        return True
    
    print("No Bad Lables...")
    return False

@st.cache_data
def filter_district_data(df: pd.DataFrame) -> pd.DataFrame:
    # Remove numeric state values (filtering)
    df = df[~df["district"].astype(str).str.isnumeric()]

    # Normalize capitalization (title case) & any leadig / trailing asterisks
    df.loc[:, "district"] = df.loc[:, "district"].str.title().str.replace("*", "", regex=False).str.strip()

    # Apply the dictionary corrections
    df.loc[:, "district"] = df.loc[:, "district"].replace(DISTRICT_CORRECTIONS)

    return df

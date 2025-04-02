import streamlit as st
import pandas as pd
import math
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import json
from io import StringIO

# Initialize session state variables
if 'sales_data' not in st.session_state:
    st.session_state.sales_data = {}
if 'available_sites' not in st.session_state:
    st.session_state.available_sites = []
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'top_month_df' not in st.session_state:
    st.session_state.top_month_df = pd.DataFrame()
if 'last_six_df' not in st.session_state:
    st.session_state.last_six_df = pd.DataFrame()
if 'future_proj' not in st.session_state:
    st.session_state.future_proj = pd.DataFrame()

# Public Holidays Data (2021–2025)
holidays_sa = { ... }  # (existing data remains the same)

def round_up_to_thousand(x):
    return math.ceil(x / 1000) * 1000

def get_last_six_months(selected_month, selected_year):
    # Existing implementation remains the same

def get_yoy_growth(site, month, year):
    # Existing implementation remains the same

def get_mom_growth(site, month, year):
    # Existing implementation remains the same

def get_future_months(selected_month, selected_year, months_ahead=6):
    # Existing implementation remains the same

def main():
    st.set_page_config(layout="wide", page_title="Fuel Sales Dashboard")
    st.title("South Africa Fuel Sales Analysis Dashboard")

    # SIDEBAR SETUP with enhanced error handling
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type=["csv"])
        st.sidebar.subheader("Parameters")
        base_years_input = st.text_input("Base Years (comma-separated)", "2021,2022,2024")
        optimistic_percent = st.number_input("Optimistic % Boost", 0.0, 100.0, 5.0)
        conservative_percent = st.number_input("Conservative % Buffer", 0.0, 100.0, 10.0)
        selected_month = st.selectbox("Select Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        selected_year = st.number_input("Select Year", 2021, 2025, 2025)
        calculation_mode = st.radio("Calculation Mode", ("Per Site", "Combined"), index=0)
        
        # Add loading indicator
        data_load_state = st.text('Loading data...')
        if "available_sites" in st.session_state:
            selected_sites = st.multiselect("Select Sites", 
                                           st.session_state.available_sites, 
                                           default=st.session_state.available_sites)
        else:
            selected_sites = []
        data_load_state.text("")

    # DATA LOADING with enhanced validation
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = {"Year", "Month", "Sales", "Site"}
            
            # Additional validation checks
            if not required_columns.issubset(df.columns):
                st.error(f"Missing required columns: {required_columns - set(df.columns)}")
                return
            
            # Check data types
            if not pd.api.types.is_integer_dtype(df['Year']):
                st.error("Year column must contain integer values")
                return
            if not pd.api.types.is_string_dtype(df['Month']):
                st.error("Month column must contain string values (e.g., 'Jan', 'Feb')")
                return
            if not (pd.api.types.is_integer_dtype(df['Sales']) or 
                    pd.api.types.is_float_dtype(df['Sales'])):
                st.error("Sales column must contain numeric values")
                return

            # Process data
            sales_data = {}
            for _, row in df.iterrows():
                site = str(row["Site"])
                year = int(row["Year"])
                month = row["Month"]
                sales = float(row["Sales"])
                
                if site not in sales_data:
                    sales_data[site] = {}
                if year not in sales_data[site]:
                    sales_data[site][year] = {}
                sales_data[site][year][month] = sales  # Overwrite duplicates instead of summing

            st.session_state.sales_data = sales_data
            st.session_state.available_sites = list(sales_data.keys())
            st.success(f"Loaded data for {len(sales_data)} sites successfully!")
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.stop()

    # CALCULATION LOGIC with improved error handling
    if st.button("Calculate Targets"):
        if not st.session_state.sales_data:
            st.error("No sales data loaded. Please upload valid data first.")
            return
        if not selected_sites:
            st.error("Please select at least one site to analyze.")
            return

        base_years = []
        try:
            base_years = [int(s.strip()) for s in base_years_input.split(",")]
        except ValueError:
            st.error("Invalid base years format. Please use comma-separated integers.")
            return

        # ... rest of calculation logic ...

    # ANALYSIS COMPONENTS with added try-except blocks
    try:
        if st.session_state.sales_data and selected_sites:
            # Existing analysis code with added error handling
            # ...
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")

    # DASHBOARD LAYOUT with improved error handling
    if st.session_state.results_df.empty:
        st.warning("No results to display. Please run calculations first.")
    else:
        # Existing dashboard code with added try-except blocks
        # ...

if __name__ == "__main__":
    main()

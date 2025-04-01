import streamlit as st
import pandas as pd
import math
from datetime import datetime

# Predefined Public Holidays for South Africa (2021–2025) with names
holidays_sa = {
    2021: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Apr 2 (Good Friday)",
        "Apr 5 (Family Day)",
        "Apr 27 (Freedom Day)",
        "May 1 (Workers' Day)",
        "Jun 16 (Youth Day)",
        "Aug 9 (National Women's Day)",
        "Sep 24 (Heritage Day)",
        "Dec 16 (Day of Reconciliation)",
        "Dec 25 (Christmas Day)",
        "Dec 26 (Day of Goodwill)"
    ],
    # ... [Include other years from the full code] ...
}

def main():
    st.title("South Africa Fuel Sales Analysis Tool")
    
    # Load Sales Data
    uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        sales_data = {}
        for _, row in df.iterrows():
            year = int(row["Year"])
            month = row["Month"]
            sales = row["Sales"]
            if year not in sales_data:
                sales_data[year] = {}
            sales_data[year][month] = sales
        st.session_state.sales_data = sales_data
        st.success("Sales data loaded successfully!")
    
    # Target Parameters
    base_years = st.text_input("Base Years (comma-separated)", "2021,2022,2024")
    optimistic_percent = st.number_input("Optimistic % Boost", 0.0, 100.0, 5.0)
    conservative_percent = st.number_input("Conservative % Buffer", 0.0, 100.0, 10.0)
    
    selected_month = st.selectbox("Select Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    selected_year = st.number_input("Select Year", 2021, 2025, 2025)
    
    if st.button("Calculate Target"):
        if "sales_data" not in st.session_state:
            st.error("No sales data loaded. Please upload a CSV file.")
            return
        
        historical_sales = []
        for year in map(int, base_years.split(",")):
            if str(year) in st.session_state.sales_data and selected_month in st.session_state.sales_data[year]:
                historical_sales.append(st.session_state.sales_data[year][selected_month])
            else:
                st.warning(f"Missing {selected_month} {year} data. Skipping...")
        
        if not historical_sales:
            st.error("Insufficient data for target calculation.")
            return
        
        base = sum(historical_sales) / len(historical_sales)
        optimistic = base * (1 + optimistic_percent/100)
        conservative = base * (1 - conservative_percent/100)
        
        def round_up_to_thousand(x):
            return math.ceil(x / 1000) * 1000
        
        base_rounded = round_up_to_thousand(base)
        optimistic_rounded = round_up_to_thousand(optimistic)
        conservative_rounded = round_up_to_thousand(conservative)
        
        st.subheader("Target Calculation Results:")
        st.write(f"**Base Target (Average):** {base_rounded:,}")
        st.write(f"**Optimistic Target (+{optimistic_percent}%):** {optimistic_rounded:,}")
        st.write(f"**Conservative Target (-{conservative_percent}%):** {conservative_rounded:,}")
        
        # Highlight Holidays
        if selected_year in holidays_sa:
            st.subheader("Public Holidays:")
            for holiday in holidays_sa[selected_year]:
                if holiday.startswith(selected_month):
                    st.write(f"- {holiday}")

if __name__ == "__main__":
    main()
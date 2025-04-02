import streamlit as st
import pandas as pd
import math
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import json
from io import StringIO

# Public Holidays Data (2021–2025)
holidays_sa = {
    2021: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Apr 2 (Good Friday)",
        "Apr 3 (Family Day)",  # Corrected from Apr 5
        "Apr 27 (Freedom Day)",
        "May 1 (Workers' Day)",
        "Jun 16 (Youth Day)",
        "Aug 9 (National Women's Day)",
        "Sep 24 (Heritage Day)",
        "Dec 16 (Day of Reconciliation)",
        "Dec 25 (Christmas Day)",
        "Dec 26 (Day of Goodwill)"
    ],
    2022: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Apr 15 (Good Friday)",
        "Apr 16 (Family Day)",  # Corrected from Apr 18
        "Apr 27 (Freedom Day)",
        "May 1 (Workers' Day)",
        "Jun 16 (Youth Day)",
        "Aug 9 (National Women's Day)",
        "Sep 24 (Heritage Day)",
        "Dec 16 (Day of Reconciliation)",
        "Dec 25 (Christmas Day)",
        "Dec 26 (Day of Goodwill)"
    ],
    2023: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Apr 7 (Good Friday)",
        "Apr 8 (Family Day)",  # Corrected from Apr 10
        "Apr 27 (Freedom Day)",
        "May 1 (Workers' Day)",
        "Jun 16 (Youth Day)",
        "Aug 9 (National Women's Day)",
        "Sep 24 (Heritage Day)",
        "Dec 16 (Day of Reconciliation)",
        "Dec 25 (Christmas Day)",
        "Dec 26 (Day of Goodwill)"
    ],
    2024: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Mar 28 (Good Friday)",  # Corrected from Mar 29
        "Mar 29 (Family Day)",  # Corrected from Mar 31
        "Apr 27 (Freedom Day)",
        "May 1 (Workers' Day)",
        "Jun 16 (Youth Day)",
        "Aug 9 (National Women's Day)",
        "Sep 24 (Heritage Day)",
        "Dec 16 (Day of Reconciliation)",
        "Dec 25 (Christmas Day)",
        "Dec 26 (Day of Goodwill)"
    ],
    2025: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Apr 18 (Good Friday)",
        "Apr 19 (Family Day)",  # Corrected from Apr 21
        "Apr 27 (Freedom Day)",
        "May 1 (Workers' Day)",
        "Jun 16 (Youth Day)",
        "Aug 9 (National Women's Day)",
        "Sep 24 (Heritage Day)",
        "Dec 16 (Day of Reconciliation)",
        "Dec 25 (Christmas Day)",
        "Dec 26 (Day of Goodwill)"
    ]
}

def round_up_to_thousand(x):
    return math.ceil(x / 1000) * 1000

def get_last_six_months(selected_month, selected_year):
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_month_index = month_order.index(selected_month)
    
    months = []
    for i in range(6):
        index = (current_month_index - i) % 12
        month = month_order[index]
        year = selected_year
        if index > current_month_index:
            year -= 1
        months.append((month, year))
    return months[::-1]

def get_yoy_growth(site, month, year):
    current_sales = st.session_state.sales_data[site][year].get(month, 0)
    prev_year_sales = st.session_state.sales_data[site].get(year-1, {}).get(month, 0)
    return ((current_sales - prev_year_sales)/prev_year_sales)*100 if prev_year_sales !=0 else 0

def get_mom_growth(site, month, year):
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_index = month_order.index(month)
    prev_month = month_order[(current_index -1)%12]
    prev_year = year -1 if current_index ==0 else year
    current_sales = st.session_state.sales_data[site][year].get(month, 0)
    prev_sales = st.session_state.sales_data[site].get(prev_year, {}).get(prev_month, 0)
    return ((current_sales - prev_sales)/prev_sales)*100 if prev_sales !=0 else 0

def main():
    st.set_page_config(layout="wide", page_title="Fuel Sales Dashboard")

    st.title("South Africa Fuel Sales Analysis Dashboard")
    
    # SIDEBAR SETUP
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type=["csv"])
        st.sidebar.subheader("Parameters")
        base_years_input = st.text_input("Base Years (comma-separated)", "2021,2022,2024")
        optimistic_percent = st.number_input("Optimistic % Boost", 0.0, 100.0, 5.0)
        conservative_percent = st.number_input("Conservative % Buffer", 0.0, 100.0, 10.0)
        selected_month = st.selectbox("Select Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        selected_year = st.number_input("Select Year", 2021, 2025, 2025)
        calculation_mode = st.radio("Calculation Mode", ("Per Site", "Combined"), index=0)
        if "available_sites" in st.session_state:
            selected_sites = st.multiselect("Select Sites", st.session_state.available_sites, default=st.session_state.available_sites)
        else:
            selected_sites = []

    # DATA LOADING
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = {"Year", "Month", "Sales", "Site"}
            if not required_columns.issubset(df.columns):
                st.error("CSV must contain columns: Year, Month, Sales, Site")
                return
            
            sales_data = {}
            for _, row in df.iterrows():
                site = row["Site"]
                year = int(row["Year"])
                month = row["Month"]
                sales = row["Sales"]
                if site not in sales_data:
                    sales_data[site] = {}
                if year not in sales_data[site]:
                    sales_data[site][year] = {}
                if month not in sales_data[site][year]:
                    sales_data[site][year][month] = 0
                sales_data[site][year][month] += sales
            
            st.session_state.sales_data = sales_data
            st.session_state.available_sites = list(sales_data.keys())
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

    # CALCULATION LOGIC
    if st.button("Calculate Targets"):
        if "sales_data" not in st.session_state:
            st.error("No sales data loaded.")
            return
        
        if not selected_sites:
            st.error("Please select at least one site.")
            return
        
        base_years = [int(s.strip()) for s in base_years_input.split(",")]
        
        if calculation_mode == "Per Site":
            results = {}
            for site in selected_sites:
                historical_sales = []
                for year in base_years:
                    if (year in st.session_state.sales_data.get(site, {}) and 
                        selected_month in st.session_state.sales_data[site][year]):
                        historical_sales.append(st.session_state.sales_data[site][year][selected_month])
                
                if historical_sales:
                    base = sum(historical_sales) / len(historical_sales)
                    optimistic = base * (1 + optimistic_percent/100)
                    conservative = base * (1 - conservative_percent/100)
                    rounded = {
                        "base": round_up_to_thousand(base),
                        "optimistic": round_up_to_thousand(optimistic),
                        "conservative": round_up_to_thousand(conservative)
                    }
                    results[site] = rounded
                else:
                    st.warning(f"Insufficient data for {site}")
            
            df_results = pd.DataFrame(results).T
            df_results.columns = ["Base Target", "Optimistic", "Conservative"]
            st.session_state.results_df = df_results
            st.session_state.selected_sites = selected_sites
            st.session_state.selected_mode = calculation_mode
        else:
            combined_historical_sales = []
            for year in base_years:
                total_sales = 0
                valid = True
                for site in selected_sites:
                    if (year in st.session_state.sales_data.get(site, {}) and 
                        selected_month in st.session_state.sales_data[site][year]):
                        total_sales += st.session_state.sales_data[site][year][selected_month]
                    else:
                        valid = False
                        break
                if valid:
                    combined_historical_sales.append(total_sales)
            
            if combined_historical_sales:
                base = sum(combined_historical_sales) / len(combined_historical_sales)
                optimistic = base * (1 + optimistic_percent/100)
                conservative = base * (1 - conservative_percent/100)
                results = {
                    "Base Target": round_up_to_thousand(base),
                    "Optimistic": round_up_to_thousand(optimistic),
                    "Conservative": round_up_to_thousand(conservative)
                }
                st.session_state.results_df = pd.DataFrame([results])
                st.session_state.selected_mode = calculation_mode
            else:
                st.error("Insufficient data for combined calculation")

    # ANALYSIS COMPONENTS
    if "sales_data" in st.session_state:
        # Top Month Analysis
        top_month_data = {}
        for site in selected_sites:
            max_sales = 0
            best_month = ""
            best_year = 0
            for year in st.session_state.sales_data[site]:
                for month in st.session_state.sales_data[site][year]:
                    sales = st.session_state.sales_data[site][year][month]
                    if sales > max_sales:
                        max_sales = sales
                        best_month = month
                        best_year = year
            top_month_data[site] = {
                "Month": f"{best_month} {best_year}",
                "Sales": max_sales
            }
        st.session_state.top_month_df = pd.DataFrame(top_month_data).T

        # Last 6 Months Analysis
        last_six_months = get_last_six_months(selected_month, selected_year)
        last_six_sales = {}
        for site in selected_sites:
            site_sales = []
            for month, year in last_six_months:
                if (year in st.session_state.sales_data.get(site, {}) and 
                    month in st.session_state.sales_data[site][year]):
                    site_sales.append(st.session_state.sales_data[site][year][month])
                else:
                    site_sales.append(0)
            last_six_sales[site] = site_sales
        st.session_state.last_six_df = pd.DataFrame(last_six_sales, index=[m[0] for m in last_six_months])

    # DASHBOARD LAYOUT
    if "results_df" in st.session_state:
        st.subheader("Dashboard Results")
        
        # Key Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Base Target", f"{st.session_state.results_df.iloc[0]['Base Target']:,}")
        with col2:
            st.metric("Optimistic Target", f"{st.session_state.results_df.iloc[0]['Optimistic']:,}")
        with col3:
            st.metric("Conservative Target", f"{st.session_state.results_df.iloc[0]['Conservative']:,}")

        # Visualization Tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Target Comparison", 
            "Historical Sales", 
            "Holiday Calendar", 
            "Top Month Sales", 
            "Last 6 Months Performance",
            "Site Report"
        ])

        with tab1:
            if st.session_state.selected_mode == "Per Site":
                fig, ax = plt.subplots(figsize=(10, 6))
                df_results = st.session_state.results_df
                df_results.plot(kind='bar', ax=ax)
                plt.title("Target Comparison by Site")
                plt.ylabel("Sales (R)")
                st.pyplot(fig)
            else:
                fig, ax = plt.subplots(figsize=(8, 4))
                values = [st.session_state.results_df.iloc[0][col] for col in ["Base Target", "Optimistic", "Conservative"]]
                labels = ["Base", "Optimistic", "Conservative"]
                ax.bar(labels, values)
                plt.title("Combined Target Comparison")
                plt.ylabel("Sales (R)")
                st.pyplot(fig)

        with tab2:
            if st.session_state.selected_mode == "Per Site":
                df_sales = pd.DataFrame()
                for site in selected_sites:
                    years = []
                    sales = []
                    for year in base_years:
                        if (year in st.session_state.sales_data.get(site, {}) and 
                            selected_month in st.session_state.sales_data[site][year]):
                            years.append(year)
                            sales.append(st.session_state.sales_data[site][year][selected_month])
                    df_sales = pd.concat([df_sales, pd.DataFrame({"Year": years, "Sales": sales, "Site": site})])
                
                fig, ax = plt.subplots(figsize=(10, 6))
                for site in selected_sites:
                    subset = df_sales[df_sales['Site'] == site]
                    ax.plot(subset['Year'], subset['Sales'], marker='o', label=site)
                plt.title(f"Historical Sales for {selected_month}")
                plt.xlabel("Year")
                plt.ylabel("Sales (R)")
                plt.legend()
                st.pyplot(fig)
            else:
                combined_sales = []
                for year in base_years:
                    total = 0
                    valid = True
                    for site in selected_sites:
                        if (year in st.session_state.sales_data.get(site, {}) and 
                            selected_month in st.session_state.sales_data[site][year]):
                            total += st.session_state.sales_data[site][year][selected_month]
                        else:
                            valid = False
                            break
                    if valid:
                        combined_sales.append(total)
                    else:
                        combined_sales.append(np.nan)
                
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(base_years, combined_sales, marker='o')
                plt.title(f"Combined Historical Sales for {selected_month}")
                plt.xlabel("Year")
                plt.ylabel("Sales (R)")
                st.pyplot(fig)

        with tab3:
            if selected_year in holidays_sa:
                holidays = [h for h in holidays_sa[selected_year] if h.startswith(selected_month)]
                st.write("### Public Holidays")
                st.table(pd.DataFrame(holidays, columns=["Holiday"]))
            else:
                st.write("No holidays data available for selected year")

        with tab4:
            st.write("### Top Performing Month for Each Site")
            st.table(st.session_state.top_month_df.style.format({"Sales": "{:,}"}))
            st.caption("Shows the month/year with highest sales for each site")

        with tab5:
            st.write("### Last 6 Months Performance")
            fig, ax = plt.subplots(figsize=(12, 6))
            for site in selected_sites:
                ax.plot(st.session_state.last_six_df.index, st.session_state.last_six_df[site], 
                        marker='o', label=site)
            plt.title("Last 6 Months Sales Trend")
            plt.xlabel("Month")
            plt.ylabel("Sales (R)")
            plt.legend()
            st.pyplot(fig)

            # Growth Analysis
            growth_rates = {}
            for site in selected_sites:
                current = st.session_state.last_six_df[site].iloc[-1]
                previous = st.session_state.last_six_df[site].iloc[-2]
                growth = ((current - previous)/previous)*100 if previous !=0 else 0
                growth_rates[site] = f"{growth:.1f}%"
            st.write("### Month-over-Month Growth")
            st.table(pd.DataFrame(growth_rates, index=["Growth"]).T)

        with tab6:
            selected_report_site = st.selectbox("Select Site for Report", selected_sites)
            if selected_report_site not in st.session_state.sales_data:
                st.error(f"No data available for {selected_report_site}")
            else:
                st.subheader(f"Report for {selected_report_site}")
                
                # KPI Section
                st.subheader("Key Performance Indicators")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Month Sales", 
                            value=f"{st.session_state.sales_data[selected_report_site][selected_year].get(selected_month, 0):,}")
                with col2:
                    st.metric("YoY Growth", 
                            value=f"{get_yoy_growth(selected_report_site, selected_month, selected_year):.1f}%")
                with col3:
                    st.metric("MoM Growth", 
                            value=f"{get_mom_growth(selected_report_site, selected_month, selected_year):.1f}%")
                
                # Target Comparison
                st.subheader("Target vs Actual")
                current_sales = st.session_state.sales_data[selected_report_site].get(selected_year, {}).get(selected_month, 0)
                target = st.session_state.results_df.loc[selected_report_site]["Base Target"]
                variance = (current_sales - target)/target * 100 if target !=0 else 0
                st.write(f"*Actual Sales*: {current_sales:,}")
                st.write(f"*Base Target*: {target:,}")
                st.write(f"*Variance*: {variance:.1f}%")
                
                # Historical Sales Table
                st.subheader("Historical Sales Data")
                hist_sales = []
                for year in base_years:
                    if (year in st.session_state.sales_data[selected_report_site] and 
                        selected_month in st.session_state.sales_data[selected_report_site][year]):
                        hist_sales.append({
                            "Year": year,
                            "Sales": st.session_state.sales_data[selected_report_site][year][selected_month]
                        })
                    else:
                        hist_sales.append({
                            "Year": year,
                            "Sales": 0
                        })
                df_hist = pd.DataFrame(hist_sales)
                st.table(df_hist.style.format({"Sales": "{:,}"}))
                
                # Visualizations
                st.subheader("Sales Trend")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.bar(["Historical Average", "Base Target"], 
                      [df_hist["Sales"].mean(), target], 
                      color=["blue", "green"])
                plt.title("Historical Average vs Target")
                st.pyplot(fig)
                
                # Download Report
                report_data = {
                    "KPIs": {
                        "Current Month Sales": current_sales,
                        "YoY Growth": f"{get_yoy_growth(selected_report_site, selected_month, selected_year):.1f}%",
                        "MoM Growth": f"{get_mom_growth(selected_report_site, selected_month, selected_year):.1f}%",
                        "Variance from Target": f"{variance:.1f}%"
                    },
                    "Historical Sales": df_hist.to_dict('records'),
                    "Target Details": {
                        "Base Target": target,
                        "Optimistic": st.session_state.results_df.loc[selected_report_site]["Optimistic"],
                        "Conservative": st.session_state.results_df.loc[selected_report_site]["Conservative"]
                    }
                }
                st.download_button(
                    label="Download Site Report (JSON)",
                    data=json.dumps(report_data, indent=4),
                    file_name=f"{selected_report_site}report{selected_month}_{selected_year}.json",
                    mime="application/json"
                )
if __name__ == "__main__":

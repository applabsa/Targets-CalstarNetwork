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
holidays_sa = {
    2021: [
        "Jan 1 (New Year's Day)",
        "Mar 21 (Human Rights Day)",
        "Apr 2 (Good Friday)",
        "Apr 3 (Family Day)",
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
        "Apr 16 (Family Day)",
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
        "Apr 8 (Family Day)",
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
        "Mar 28 (Good Friday)",
        "Mar 29 (Family Day)",
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
        "Apr 19 (Family Day)",
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
    current_sales = st.session_state.sales_data[site].get(year, {}).get(month, 0)
    prev_year_sales = st.session_state.sales_data[site].get(year-1, {}).get(month, 0)
    return ((current_sales - prev_year_sales)/prev_year_sales)*100 if prev_year_sales !=0 else 0

def get_mom_growth(site, month, year):
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_index = month_order.index(month)
    prev_month = month_order[(current_index -1)%12]
    prev_year = year -1 if current_index ==0 else year
    current_sales = st.session_state.sales_data[site].get(year, {}).get(month, 0)
    prev_sales = st.session_state.sales_data[site].get(prev_year, {}).get(prev_month, 0)
    return ((current_sales - prev_sales)/prev_sales)*100 if prev_sales !=0 else 0

def get_future_months(selected_month, selected_year, months_ahead=6):
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_month_index = month_order.index(selected_month)
    future_months = []
    for i in range(1, months_ahead+1):
        index = (current_month_index + i) % 12
        month = month_order[index]
        year = selected_year + (current_month_index + i) // 12
        future_months.append((month, year))
    return future_months

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
        selected_month = st.selectbox("Select Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        selected_year = st.number_input("Select Year", 2021, 2025, 2025)
        calculation_mode = st.radio("Calculation Mode", ("Per Site", "Combined"), index=0)
        
        data_load_state = st.text('Loading data...')
        if "available_sites" in st.session_state:
            selected_sites = st.multiselect("Select Sites", 
                                           st.session_state.available_sites, 
                                           default=st.session_state.available_sites)
        else:
            selected_sites = []
        data_load_state.text("")

    # DATA LOADING
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = {"Year", "Month", "Sales", "Site"}
            
            if not required_columns.issubset(df.columns):
                st.error(f"Missing required columns: {required_columns - set(df.columns)}")
                return
            
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
                sales_data[site][year][month] = sales

            st.session_state.sales_data = sales_data
            st.session_state.available_sites = list(sales_data.keys())
            st.success(f"Loaded data for {len(sales_data)} sites successfully!")
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.stop()

    # CALCULATION LOGIC
    if st.button("Calculate Targets"):
        if not st.session_state.sales_data:
            st.error("No sales data loaded. Please upload valid data first.")
            return
        if not selected_sites:
            st.error("Please select at least one site to analyze.")
            return

        try:
            base_years = [int(s.strip()) for s in base_years_input.split(",")]
        except ValueError:
            st.error("Invalid base years format. Please use comma-separated integers.")
            return

        if calculation_mode == "Per Site":
            results = {}
            for site in selected_sites:
                historical_sales = []
                for year in base_years:
                    if (year in st.session_state.sales_data.get(site, {}) and 
                        selected_month in st.session_state.sales_data[site].get(year, {})):
                        historical_sales.append(st.session_state.sales_data[site][year][selected_month])
                if historical_sales:
                    base = sum(historical_sales) / len(historical_sales)
                    optimistic = base * (1 + optimistic_percent/100)
                    conservative = base * (1 - conservative_percent/100)
                    results[site] = {
                        "Base Target": round_up_to_thousand(base),
                        "Optimistic": round_up_to_thousand(optimistic),
                        "Conservative": round_up_to_thousand(conservative)
                    }
                else:
                    st.warning(f"Insufficient data for {site}")
            st.session_state.results_df = pd.DataFrame(results).T
        else:
            combined_historical_sales = []
            for year in base_years:
                total_sales = 0
                valid = True
                for site in selected_sites:
                    if (year in st.session_state.sales_data.get(site, {}) and 
                        selected_month in st.session_state.sales_data[site].get(year, {})):
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
                st.session_state.results_df = pd.DataFrame([results], index=["Combined"])
            else:
                st.error("Insufficient data for combined calculation")

        # Generate analysis components
        if not st.session_state.results_df.empty:
            # Top Month Analysis
            top_month_data = {}
            for site in selected_sites:
                max_sales = 0
                best_month = ""
                best_year = 0
                for year in st.session_state.sales_data.get(site, {}):
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
                        month in st.session_state.sales_data[site].get(year, {})):
                        site_sales.append(st.session_state.sales_data[site][year][month])
                    else:
                        site_sales.append(0)
                last_six_sales[site] = site_sales
            st.session_state.last_six_df = pd.DataFrame(last_six_sales, index=[m[0] for m in last_six_months])

            # Future Projections
            if "results_df" in st.session_state:
                months_ahead = 6
                future_months = get_future_months(selected_month, selected_year, months_ahead)
                sites = selected_sites if calculation_mode == "Per Site" else ["Combined"]
                avg_growth = []
                for site in sites:
                    sales = st.session_state.last_six_df[site]
                    growth = (sales.pct_change() * 100).mean()
                    avg_growth.append(growth)
                avg_growth_rate = np.mean(avg_growth) / 100 if avg_growth else 0
                base_target = st.session_state.results_df["Base Target"].mean()
                projection_data = []
                for i, (month, year) in enumerate(future_months):
                    projected = base_target * (1 + avg_growth_rate) ** (i+1)
                    projection_data.append({
                        "Month": f"{month} {year}",
                        "Projected": round(projected),
                        "Optimistic": round(projected * (1 + optimistic_percent/100)),
                        "Conservative": round(projected * (1 - conservative_percent/100))
                    })
                st.session_state.future_proj = pd.DataFrame(projection_data)

    # DASHBOARD LAYOUT
    if "results_df" in st.session_state and not st.session_state.results_df.empty:
        st.subheader("Dashboard Results")
        
        # Key Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Base Target", f"{st.session_state.results_df['Base Target'].values[0]:,}")
        with col2:
            st.metric("Optimistic Target", f"{st.session_state.results_df['Optimistic'].values[0]:,}")
        with col3:
            st.metric("Conservative Target", f"{st.session_state.results_df['Conservative'].values[0]:,}")

        tabs = st.tabs([
            "Target Comparison", 
            "Historical Sales", 
            "Holiday Calendar", 
            "Top Month Sales", 
            "Last 6 Months Performance",
            "Site Report",
            "Future Projections"
        ])

        # Tab 1: Target Comparison
        with tabs[0]:
            fig, ax = plt.subplots(figsize=(10, 6))
            if calculation_mode == "Per Site":
                st.session_state.results_df.plot(kind='bar', ax=ax)
                plt.title("Target Comparison by Site")
            else:
                st.session_state.results_df.T.plot(kind='bar', ax=ax)
                plt.title("Combined Target Comparison")
            plt.ylabel("Sales (R)")
            st.pyplot(fig)

        # Tab 2: Historical Sales
        with tabs[1]:
            if calculation_mode == "Per Site":
                df_sales = pd.DataFrame()
                for site in selected_sites:
                    years = []
                    sales = []
                    for year in base_years:
                        if (year in st.session_state.sales_data.get(site, {}) and 
                            selected_month in st.session_state.sales_data[site].get(year, {})):
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
                            selected_month in st.session_state.sales_data[site].get(year, {})):
                            total += st.session_state.sales_data[site][year][selected_month]
                        else:
                            valid = False
                            break
                    combined_sales.append(total if valid else np.nan)
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(base_years, combined_sales, marker='o')
                plt.title(f"Combined Historical Sales for {selected_month}")
                plt.xlabel("Year")
                plt.ylabel("Sales (R)")
                st.pyplot(fig)

        # Tab 3: Holiday Calendar
        with tabs[2]:
            if selected_year in holidays_sa:
                holidays = [h for h in holidays_sa[selected_year] if h.startswith(selected_month)]
                st.table(pd.DataFrame(holidays, columns=["Holiday"]))
            else:
                st.write("No holidays data available for selected year")

        # Tab 4: Top Month Sales
        with tabs[3]:
            st.table(st.session_state.top_month_df.style.format({"Sales": "{:,}"}))

        # Tab 5: Last 6 Months Performance
        with tabs[4]:
            fig, ax = plt.subplots(figsize=(12, 6))
            for site in selected_sites:
                ax.plot(st.session_state.last_six_df.index, st.session_state.last_six_df[site], 
                        marker='o', label=site)
            plt.title("Last 6 Months Sales Trend")
            plt.xlabel("Month")
            plt.ylabel("Sales (R)")
            plt.legend()
            st.pyplot(fig)
            
            growth_rates = {}
            for site in selected_sites:
                current = st.session_state.last_six_df[site].iloc[-1]
                previous = st.session_state.last_six_df[site].iloc[-2]
                growth = ((current - previous)/previous)*100 if previous !=0 else 0
                growth_rates[site] = f"{growth:.1f}%"
            st.table(pd.DataFrame(growth_rates, index=["Growth"]).T)

        # Tab 6: Site Report
        with tabs[5]:
            selected_report_site = st.selectbox("Select Site for Report", selected_sites)
            if selected_report_site not in st.session_state.sales_data:
                st.error(f"No data available for {selected_report_site}")
            else:
                current_sales = st.session_state.sales_data[selected_report_site].get(selected_year, {}).get(selected_month, 0)
                target = st.session_state.results_df.loc[selected_report_site]["Base Target"]
                variance = (current_sales - target)/target * 100 if target !=0 else 0
                
                # KPIs
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Month Sales", value=f"{current_sales:,}")
                with col2:
                    st.metric("YoY Growth", value=f"{get_yoy_growth(selected_report_site, selected_month, selected_year):.1f}%")
                with col3:
                    st.metric("MoM Growth", value=f"{get_mom_growth(selected_report_site, selected_month, selected_year):.1f}%")
                
                # Historical Sales
                hist_sales = []
                for year in base_years:
                    if (year in st.session_state.sales_data[selected_report_site] and 
                        selected_month in st.session_state.sales_data[selected_report_site].get(year, {})):
                        hist_sales.append({
                            "Year": year,
                            "Sales": st.session_state.sales_data[selected_report_site][year][selected_month]
                        })
                df_hist = pd.DataFrame(hist_sales)
                st.table(df_hist.style.format({"Sales": "{:,}"}))
                
                # Download Report
                def convert_types(obj):
                    if isinstance(obj, (np.integer, np.floating)):
                        return int(obj) if isinstance(obj, np.integer) else float(obj)
                    return obj
                
                report_data = {
                    "KPIs": {
                        "Current Month Sales": current_sales,
                        "YoY Growth": f"{get_yoy_growth(selected_report_site, selected_month, selected_year):.1f}%",
                        "MoM Growth": f"{get_mom_growth(selected_report_site, selected_month, selected_year):.1f}%",
                        "Variance from Target": f"{variance:.1f}%"
                    },
                    "Historical Sales": df_hist.to_dict('records'),
                    "Target Details": st.session_state.results_df.loc[selected_report_site].to_dict()
                }
                st.download_button(
                    label="Download Site Report (JSON)",
                    data=json.dumps(report_data, default=convert_types, indent=4),
                    file_name=f"{selected_report_site}_report_{selected_month}_{selected_year}.json",
                    mime="application/json"
                )

        # Tab 7: Future Projections
        with tabs[6]:
            if "future_proj" in st.session_state and not st.session_state.future_proj.empty:
                st.table(st.session_state.future_proj.style.format({
                    "Projected": "{:,}",
                    "Optimistic": "{:,}",
                    "Conservative": "{:,}"
                }))
                
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(st.session_state.future_proj["Month"], 
                        st.session_state.future_proj["Projected"], 
                        marker='o', label="Projected Target")
                ax.plot(st.session_state.future_proj["Month"], 
                        st.session_state.future_proj["Optimistic"], 
                        linestyle="--", label="Optimistic")
                ax.plot(st.session_state.future_proj["Month"], 
                        st.session_state.future_proj["Conservative"], 
                        linestyle=":", label="Conservative")
                plt.title("Sales Projections")
                plt.xlabel("Month")
                plt.ylabel("Sales (R)")
                plt.xticks(rotation=45)
                plt.legend()
                st.pyplot(fig)
                st.write(f"Average MoM Growth Rate: {avg_growth_rate * 100:.1f}%")

if __name__ == "__main__":
    main()

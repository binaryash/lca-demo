import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG (Mobile Friendly) ---
st.set_page_config(page_title="FORWAST Explorer", layout="centered")

# --- DATABASE PATH ---
# Detects Docker (Render) vs Local
if os.path.exists("/app/bw_data"):
    os.environ["BRIGHTWAY2_DIR"] = "/app/bw_data"
else:
    os.environ["BRIGHTWAY2_DIR"] = os.path.join(os.getcwd(), "bw_data_local")

# --- HELPER: EXACT LCA CALCULATION ---
def run_lca_trace(activity_obj):
    """
    Performs Matrix Inversion for 1.0 Unit of the activity.
    Returns: Score, DataFrame of Top 100 Contributors.
    """
    from brightway2 import LCA
    from bw2analyzer import ContributionAnalysis

    # 1. Matrix Inversion (The Exact Math)
    lca = LCA({activity_obj: 1}, ("IPCC 2013", "climate change", "global warming potential (GWP100)"))
    lca.lci()
    lca.lcia()

    # 2. Trace (Limit to 100 to save RAM on Render Free Tier)
    ca = ContributionAnalysis()
    raw_results = ca.annotated_top_processes(lca, limit=100)

    data = []
    for score, amount, proc in raw_results:
        if abs(score) > 1e-12: # Filter noise
            data.append({
                "Process Name": proc['name'],
                "Location": proc['location'],
                "Impact": score, # Exact float
                "Contribution": (score / lca.score) * 100, # Percentage
                "Unit": proc['unit']
            })
    
    return lca.score, pd.DataFrame(data)

# --- UI HEADER ---
st.title("🏭 FORWAST Explorer")
st.caption("Scientific Traceability Engine | GWP100")

# --- INITIALIZE DATABASE ---
try:
    from brightway2 import projects, Database
    if "brightway-forwast" not in projects:
        projects.set_current("brightway-forwast")
    else:
        projects.set_current("brightway-forwast")
    
    db = Database("forwast")

except Exception as e:
    st.error("⚠️ Database Error: FORWAST not found.")
    st.info("If running locally, execute `python build_db.py` first.")
    st.stop()

# --- STEP 1: SEARCH ---
st.markdown("### 1. Find Activity")
query = st.text_input("Search Database", placeholder="e.g. Electricity, Transport, Steel...")

if query:
    # Fast list comprehension search
    matches = [a for a in db if query.lower() in a['name'].lower()]
    
    if matches:
        # Create a readable list for the dropdown
        opts = {f"{a['name']} ({a['location']})": a for a in matches[:50]}
        selected = st.selectbox("Select specific process:", list(opts.keys()))
        activity = opts[selected]

        # --- STEP 2: CALCULATE ---
        st.divider()
        if st.button(f"⚡ Trace Impact (1.0 {activity['unit']})", type="primary", use_container_width=True):
            
            with st.spinner("Calculating Impact Matrix..."):
                total_score, df_trace = run_lca_trace(activity)

            # --- STEP 3: EXACT RESULTS ---
            st.success("Calculation Complete")
            
            # A. The Big Number
            st.metric(
                label="Total Global Warming Potential",
                value=f"{total_score:.5f} kg CO₂e",
                delta="100% Impact"
            )

            # B. The Pie Chart (Visual Trace)
            st.markdown("### 2. Impact Drivers")
            
            # Aggregate small contributors for a clean chart
            if len(df_trace) > 10:
                top_10 = df_trace.head(10).copy()
                others_val = df_trace.iloc[10:]["Impact"].sum()
                new_row = pd.DataFrame([{"Process Name": "Others (Supply Chain)", "Impact": others_val}])
                df_chart = pd.concat([top_10, new_row], ignore_index=True)
            else:
                df_chart = df_trace

            fig = px.pie(
                df_chart, 
                values="Impact", 
                names="Process Name", 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig, use_container_width=True)

            # C. The Exact Data Table (Evidence)
            st.markdown("### 3. Supply Chain Evidence")
            with st.expander("📄 View Detailed Data Table", expanded=True):
                # Format for display (Strings) but keep data raw in background
                display_df = df_trace.copy()
                display_df["Impact"] = display_df["Impact"].map('{:.5f}'.format)
                display_df["Contribution"] = display_df["Contribution"].map('{:.2f}%'.format)
                
                st.dataframe(
                    display_df[["Process Name", "Location", "Impact", "Contribution"]],
                    use_container_width=True,
                    height=300
                )
                
                # Download Option
                csv = df_trace.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Trace CSV",
                    csv,
                    "forwast_trace.csv",
                    "text/csv",
                    key='download-csv',
                    use_container_width=True
                )

    else:
        st.warning("No matches found in database.")
else:
    st.info("Enter a keyword above to start.")

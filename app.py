
import pandas as pd
import plotly.express as px
import streamlit as st

from solar_sim import calculate_daily_load, calculate_system

st.set_page_config(
    page_title="SolarSim | Rural Healthcare",
    page_icon="☀️",
    layout="wide",
)

st.title("☀️ SolarSim")
st.subheader("Rural Healthcare Centre Energy Simulator")
st.caption(
    "Educational design tool | Low-voltage DC loads | "
    "Preliminary estimates, not a certified installation design"
)

st.sidebar.header("System assumptions")
sun_hours = st.sidebar.slider(
    "Peak sun hours per day", 1.0, 7.0, 4.0, 0.5
)
performance_ratio = st.sidebar.slider(
    "Overall solar performance factor", 0.50, 0.90, 0.75, 0.05
)
backup_days = st.sidebar.selectbox(
    "Battery backup target (days)", [1, 2, 3], index=1
)
dod = st.sidebar.slider(
    "Permitted battery depth of discharge", 0.40, 0.90, 0.80, 0.05
)
battery_efficiency = st.sidebar.slider(
    "Battery discharge efficiency", 0.80, 0.98, 0.90, 0.01
)
battery_voltage = st.sidebar.selectbox(
    "Nominal battery voltage", [12, 24, 48], index=0
)

st.header("1. Define electrical loads")
st.write(
    "Enter the number of devices, power rating and hours of use per day."
)

load_definitions = [
    ("LED lights", 4, 5, 6),
    ("DC fans", 1, 15, 6),
    ("Optional load 1", 0, 20, 2),
    ("Optional load 2", 0, 30, 2),
    ("Optional load 3", 0, 10, 1),
]

loads = []
for name, default_count, default_watts, default_hours in load_definitions:
    with st.expander(name, expanded=(name in ["LED lights", "DC fans"])):
        c1, c2, c3 = st.columns(3)
        count = c1.number_input(
            "Number of devices",
            min_value=0,
            max_value=100,
            value=default_count,
            step=1,
            key=f"{name}_count",
        )
        watts = c2.number_input(
            "Watts per device",
            min_value=0.0,
            max_value=5000.0,
            value=float(default_watts),
            step=1.0,
            key=f"{name}_watts",
        )
        hours = c3.number_input(
            "Hours per day",
            min_value=0.0,
            max_value=24.0,
            value=float(default_hours),
            step=0.5,
            key=f"{name}_hours",
        )
    loads.append({
        "name": name,
        "count": count,
        "watts": watts,
        "hours": hours,
    })

daily_load = calculate_daily_load(loads)
load_table = pd.DataFrame([
    {
        "Load": item["name"],
        "Quantity": item["count"],
        "Watts each": item["watts"],
        "Hours/day": item["hours"],
        "Energy (Wh/day)": (
            item["count"] * item["watts"] * item["hours"]
        ),
    }
    for item in loads
])

st.dataframe(load_table, use_container_width=True, hide_index=True)

st.header("2. Solar panel and battery sizing")

c1, c2 = st.columns(2)
with c1:
    panel_choice = st.selectbox(
        "Panel capacity to evaluate",
        [50, 100, 150, 200, 300, 400, 500],
        index=1,
    )
with c2:
    panel_cost_per_w = st.number_input(
        "Panel cost assumption (₹ per W)",
        min_value=0.0,
        value=40.0,
        step=5.0,
    )

results = calculate_system(
    daily_load_wh=daily_load,
    peak_sun_hours=sun_hours,
    performance_ratio=performance_ratio,
    backup_days=float(backup_days),
    depth_of_discharge=dod,
    battery_efficiency=battery_efficiency,
    battery_voltage=float(battery_voltage),
    panel_size_w=float(panel_choice),
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Daily energy demand", f"{daily_load:,.0f} Wh")
m2.metric("Estimated panel size", f"{results.panel_size_w:,.0f} W")
m3.metric("Selected panel generation", f"{results.daily_generation_wh:,.0f} Wh/day")
m4.metric("Battery capacity estimate", f"{results.battery_capacity_ah:,.1f} Ah")

if results.daily_generation_wh >= daily_load:
    st.success("Estimated daily solar generation meets the entered daily load.")
else:
    st.warning(
        "The selected panel's estimated daily generation is below the load. "
        "Consider a larger panel, reduced load or revised assumptions."
    )

st.caption(
    "The battery estimate represents nominal capacity for the selected "
    "backup duration and assumptions. It does not simulate battery ageing, "
    "temperature effects, or detailed charging behaviour."
)

st.header("3. Graphs")

generation_data = pd.DataFrame({
    "Category": ["Daily load", "Solar generation"],
    "Energy (Wh/day)": [
        daily_load,
        results.daily_generation_wh,
    ],
})
fig1 = px.bar(
    generation_data,
    x="Category",
    y="Energy (Wh/day)",
    title="Estimated daily energy: demand versus generation",
    text_auto=".0f",
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### Scenario comparison")
st.write(
    "Compare the selected panel under lower and higher sunlight conditions. "
    "These are simplified daily-energy scenarios."
)

scenarios = []
for scenario_name, hours_factor, load_factor in [
    ("Low sunlight / high load", 0.60, 1.25),
    ("Selected conditions", 1.00, 1.00),
    ("Good sunlight / lower load", 1.20, 0.85),
]:
    scenario_generation = (
        panel_choice * sun_hours * hours_factor * performance_ratio
    )
    scenario_load = daily_load * load_factor
    scenarios.append({
        "Scenario": scenario_name,
        "Generation (Wh/day)": scenario_generation,
        "Demand (Wh/day)": scenario_load,
        "Balance (Wh/day)": scenario_generation - scenario_load,
    })

scenario_df = pd.DataFrame(scenarios)
fig2 = px.bar(
    scenario_df,
    x="Scenario",
    y=["Generation (Wh/day)", "Demand (Wh/day)"],
    barmode="group",
    title="Generation and demand under different scenarios",
)
st.plotly_chart(fig2, use_container_width=True)
st.dataframe(scenario_df.round(1), use_container_width=True, hide_index=True)

st.header("4. Preliminary cost estimate")
st.write(
    "Enter indicative prices for planning. Replace these assumptions with "
    "actual supplier quotations before final submission."
)

battery_cost_per_wh = st.number_input(
    "Battery cost assumption (₹ per nominal Wh)",
    min_value=0.0,
    value=15.0,
    step=1.0,
)
controller_cost = st.number_input(
    "Charge controller estimate (₹)", min_value=0.0, value=700.0, step=100.0
)
protection_cost = st.number_input(
    "Wires, fuse, switches and mounting (₹)",
    min_value=0.0,
    value=800.0,
    step=100.0,
)

panel_cost = panel_choice * panel_cost_per_w
battery_cost = results.battery_capacity_wh * battery_cost_per_wh
total_cost = panel_cost + battery_cost + controller_cost + protection_cost

cost_df = pd.DataFrame({
    "Component": [
        "Solar panel",
        "Battery (capacity estimate)",
        "Charge controller",
        "Wiring, protection and mounting",
    ],
    "Estimated cost (₹)": [
        panel_cost,
        battery_cost,
        controller_cost,
        protection_cost,
    ],
})
st.dataframe(cost_df.round(0), use_container_width=True, hide_index=True)
st.metric("Indicative total cost", f"₹{total_cost:,.0f}")

st.header("5. Download results")
summary = pd.DataFrame({
    "Parameter": [
        "Daily energy demand (Wh/day)",
        "Peak sun hours/day",
        "Performance factor",
        "Selected panel (W)",
        "Estimated required panel (W)",
        "Estimated generation (Wh/day)",
        "Backup target (days)",
        "Estimated battery capacity (Wh)",
        "Estimated battery capacity (Ah)",
        "Estimated total cost (₹)",
    ],
    "Value": [
        daily_load,
        sun_hours,
        performance_ratio,
        panel_choice,
        results.panel_size_w,
        results.daily_generation_wh,
        backup_days,
        results.battery_capacity_wh,
        results.battery_capacity_ah,
        total_cost,
    ],
})

st.dataframe(summary, use_container_width=True, hide_index=True)
st.download_button(
    "Download results as CSV",
    data=summary.to_csv(index=False).encode("utf-8"),
    file_name="solarsim_results.csv",
    mime="text/csv",
)

st.info(
    "Scope note: this model is for educational planning of basic DC loads. "
    "It does not establish suitability for medical refrigerators, clinical "
    "equipment or an actual healthcare facility."
)

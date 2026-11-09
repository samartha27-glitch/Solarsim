
"""Core engineering calculations for SolarSim."""

from dataclasses import dataclass

@dataclass
class SystemResults:
    daily_load_wh: float
    panel_size_w: float
    daily_generation_wh: float
    battery_capacity_wh: float
    battery_capacity_ah: float
    daily_surplus_wh: float

def calculate_daily_load(loads):
    """Each load is a dict with count, watts and hours."""
    total = 0.0

    for load in loads:
        count = float(load["count"])
        watts = float(load["watts"])
        hours = float(load["hours"])

        if count < 0 or watts < 0 or not 0 <= hours <= 24:
            raise ValueError("Invalid load values.")

        total += count * watts * hours

    return total

def calculate_system(
    daily_load_wh,
    peak_sun_hours=4.0,
    performance_ratio=0.75,
    backup_days=2.0,
    depth_of_discharge=0.80,
    battery_efficiency=0.90,
    battery_voltage=12.0,
    panel_size_w=None,
):
    """Estimate system size for a low-voltage DC demonstration."""

    if daily_load_wh < 0:
        raise ValueError("Daily load cannot be negative.")
    if peak_sun_hours <= 0:
        raise ValueError("Peak sun hours must be positive.")
    if not 0 < performance_ratio <= 1:
        raise ValueError("Performance ratio must be in (0, 1].")
    if backup_days <= 0:
        raise ValueError("Backup days must be positive.")
    if not 0 < depth_of_discharge <= 1:
        raise ValueError("Depth of discharge must be in (0, 1].")
    if not 0 < battery_efficiency <= 1:
        raise ValueError("Battery efficiency must be in (0, 1].")
    if battery_voltage <= 0:
        raise ValueError("Battery voltage must be positive.")

    required_panel_w = (
        daily_load_wh / (peak_sun_hours * performance_ratio)
        if daily_load_wh > 0 else 0.0
    )

    selected_panel_w = (
        required_panel_w if panel_size_w is None else float(panel_size_w)
    )
    if selected_panel_w < 0:
        raise ValueError("Panel size cannot be negative.")

    generation_wh = (
        selected_panel_w * peak_sun_hours * performance_ratio
    )

    battery_wh = (
        daily_load_wh * backup_days
        / (depth_of_discharge * battery_efficiency)
    )

    battery_ah = battery_wh / battery_voltage
    surplus_wh = generation_wh - daily_load_wh

    return SystemResults(
        daily_load_wh=daily_load_wh,
        panel_size_w=required_panel_w,
        daily_generation_wh=generation_wh,
        battery_capacity_wh=battery_wh,
        battery_capacity_ah=battery_ah,
        daily_surplus_wh=surplus_wh,
    )
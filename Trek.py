# Creating a two-day walking itinerary map from Ranchoddas Arogya Bhavan in Matheran
import matplotlib.pyplot as plt
import numpy as np
import os

# Set style
plt.style.use('seaborn-v0_8')

# Base location: Ranchoddas Arogya Bhavan
base_lat, base_lon = 18.999306, 73.276139

# Define Day 1 and Day 2 points with approximate distances (in km)
day1_points = {
    "Charlotte Lake": (1.5, 45),
    "Echo Point": (2.0, 60),
    "Louisa Point": (2.5, 90),
    "Alexander Point": (1.5, 135),
    "King George Point": (2.0, 180),
    "Monkey Point": (2.0, 225),
    "Sunset Point": (2.5, 270)
}

day2_points = {
    "Panorama Point": (3.5, 30),
    "One Tree Hill Point": (3.0, 75),
    "Hart Point": (2.0, 120),
    "Garbett Point": (6.5, 165)
}

# Function to compute new lat/lon from base using distance and angle
def compute_coordinates(base_lat, base_lon, distance_km, angle_deg):
    # Approximate conversion: 1 deg latitude ~ 111 km, 1 deg longitude ~ 111 km * cos(latitude)
    delta_lat = (distance_km * np.cos(np.radians(angle_deg))) / 111
    delta_lon = (distance_km * np.sin(np.radians(angle_deg))) / (111 * np.cos(np.radians(base_lat)))
    return base_lat + delta_lat, base_lon + delta_lon

# Compute coordinates
day1_coords = {name: compute_coordinates(base_lat, base_lon, dist, angle) for name, (dist, angle) in day1_points.items()}
day2_coords = {name: compute_coordinates(base_lat, base_lon, dist, angle) for name, (dist, angle) in day2_points.items()}

# Plotting
fig, ax = plt.subplots(figsize=(10, 10))

# Plot base
ax.plot(base_lon, base_lat, 'ko', markersize=8, label="Start: Ranchoddas Arogya Bhavan")
ax.text(base_lon + 0.001, base_lat, "Start", fontsize=9, weight='bold')

# Plot Day 1
for name, (lat, lon) in day1_coords.items():
    ax.plot(lon, lat, 'o', color='tab:blue')
    ax.text(lon + 0.001, lat, name, fontsize=8)
    ax.plot([base_lon, lon], [base_lat, lat], linestyle='--', color='tab:blue', alpha=0.5)

# Plot Day 2
for name, (lat, lon) in day2_coords.items():
    ax.plot(lon, lat, 'o', color='tab:green')
    ax.text(lon + 0.001, lat, name, fontsize=8)
    ax.plot([base_lon, lon], [base_lat, lat], linestyle='--', color='tab:green', alpha=0.5)

# Legend and aesthetics
ax.set_title("Two-Day Walking Itinerary Map from Ranchoddas Arogya Bhavan, Matheran", fontsize=12, weight='bold')
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend(["Start", "Day 1 Points", "Day 2 Points"])
ax.grid(True)

# Save the figure
output_path = "static/images"
fig.savefig(output_path, dpi=300, bbox_inches='tight')

print("Created a two-day walking itinerary map from Ranchoddas Arogya Bhavan with labeled attractions and distances.")

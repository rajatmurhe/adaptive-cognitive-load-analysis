import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
data = pd.read_csv("cognitive_data.csv")

# Normalize time (start from 0)
data["Time"] = data["Time"] - data["Time"].iloc[0]

# Phase classification
def get_phase(cli):
    if cli < 30:
        return "Warm-up"
    elif cli < 55:
        return "Focused"
    elif cli < 75:
        return "Overload"
    else:
        return "Fatigue"

data["Phase"] = data["CognitiveLoad"].apply(get_phase)

#  PLOT 
plt.figure(figsize=(12,6))

# Plot Cognitive Load
plt.plot(data["Time"], data["CognitiveLoad"], label="Cognitive Load", linewidth=2)

# Shade phases
for i in range(len(data)-1):
    t1 = data["Time"].iloc[i]
    t2 = data["Time"].iloc[i+1]
    phase = data["Phase"].iloc[i]

    if phase == "Focused":
        plt.axvspan(t1, t2, color='green', alpha=0.1)
    elif phase == "Overload":
        plt.axvspan(t1, t2, color='orange', alpha=0.1)
    elif phase == "Fatigue":
        plt.axvspan(t1, t2, color='red', alpha=0.1)

# Plot other signals (scaled)
plt.plot(data["Time"], data["BlinkRate"]*2, label="Blink Rate (scaled)")
plt.plot(data["Time"], data["Stress"]*100, label="Stress (scaled)")
plt.plot(data["Time"], data["Distraction"]*100, label="Distraction (scaled)")

# Labels
plt.xlabel("Time (seconds)")
plt.ylabel("Values")
plt.title("Cognitive State Over Time")

plt.legend()
plt.grid()

plt.show()
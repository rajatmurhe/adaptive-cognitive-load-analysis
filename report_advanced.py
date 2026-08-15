from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#  LOAD DATA 
data = pd.read_csv("cognitive_data.csv")

data["Time"] = data["Time"] - data["Time"].iloc[0]

#  PHASE 
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

#  SUMMARY 
total = len(data)

focused = len(data[data["Phase"] == "Focused"]) / total * 100
overload = len(data[data["Phase"] == "Overload"]) / total * 100
fatigue = len(data[data["Phase"] == "Fatigue"]) / total * 100

avg_cli = data["CognitiveLoad"].mean()
max_cli = data["CognitiveLoad"].max()

#  STABILITY 
std = np.std(data["CognitiveLoad"])
stability = max(0, 100 - std * 2)

#  ATTENTION 
focus_times = []
current = 0

for p in data["Phase"]:
    if p == "Focused":
        current += 1
    else:
        focus_times.append(current)
        current = 0

max_focus = max(focus_times) if focus_times else 0

#  CORRELATION 
corr = data[["BlinkRate", "Stress", "Distraction", "CognitiveLoad"]].corr()

#  GRAPH 1 
plt.figure(figsize=(8,4))
plt.plot(data["Time"], data["CognitiveLoad"])
plt.title("Cognitive Load Over Time")
plt.xlabel("Time")
plt.ylabel("CLI")
plt.grid()

plt.savefig("cli_graph.png")
plt.close()

#  GRAPH 2 
plt.figure(figsize=(6,5))
plt.imshow(corr)
plt.colorbar()
plt.xticks(range(len(corr.columns)), corr.columns, rotation=45)
plt.yticks(range(len(corr.columns)), corr.columns)
plt.title("Correlation Matrix")

plt.savefig("corr_graph.png")
plt.close()

#  INSIGHTS 
insights = []

if overload > 30:
    insights.append("Frequent cognitive overload observed")

if fatigue > 20:
    insights.append("Fatigue detected in session")

if stability < 60:
    insights.append("Low cognitive stability")

if max_focus < 30:
    insights.append("Short attention span")

#  PDF 
doc = SimpleDocTemplate("Advanced_Cognitive_Report.pdf")
styles = getSampleStyleSheet()

elements = []

# Title
elements.append(Paragraph("Advanced Cognitive Analysis Report", styles["Title"]))
elements.append(Spacer(1, 20))

# Summary
elements.append(Paragraph("Session Summary", styles["Heading2"]))
elements.append(Paragraph(
    f"Focused: {focused:.2f}%<br/>"
    f"Overload: {overload:.2f}%<br/>"
    f"Fatigue: {fatigue:.2f}%<br/>"
    f"Average CLI: {avg_cli:.2f}<br/>"
    f"Peak CLI: {max_cli}<br/>",
    styles["Normal"]
))
elements.append(Spacer(1, 15))

# Advanced Metrics
elements.append(Paragraph("Advanced Metrics", styles["Heading2"]))
elements.append(Paragraph(
    f"Cognitive Stability: {stability:.2f}%<br/>"
    f"Max Attention Span: {max_focus} seconds",
    styles["Normal"]
))
elements.append(Spacer(1, 15))

# Insights
elements.append(Paragraph("Insights", styles["Heading2"]))
for i in insights:
    elements.append(Paragraph(f"- {i}", styles["Normal"]))
elements.append(Spacer(1, 15))

# Graphs
elements.append(Paragraph("Cognitive Load Trend", styles["Heading2"]))
elements.append(Image("cli_graph.png", width=400, height=200))
elements.append(Spacer(1, 15))

elements.append(Paragraph("Correlation Analysis", styles["Heading2"]))
elements.append(Image("corr_graph.png", width=400, height=250))

# Build
doc.build(elements)

print("Advanced PDF Generated: Advanced_Cognitive_Report.pdf")
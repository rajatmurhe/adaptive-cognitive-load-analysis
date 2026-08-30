import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("cognitive_data.csv")

corr = data[["BlinkRate", "Stress", "Distraction", "CognitiveLoad"]].corr()
print(corr)

plt.imshow(corr, cmap="coolwarm")
plt.colorbar()
plt.xticks(range(len(corr.columns)), corr.columns, rotation=45)
plt.yticks(range(len(corr.columns)), corr.columns)
plt.title("Correlation Matrix")
plt.show()

plt.figure(figsize=(10,4))

plt.subplot(1,3,1)
plt.scatter(data["BlinkRate"], data["CognitiveLoad"])
plt.title("Blink vs CLI")

plt.subplot(1,3,2)
plt.scatter(data["Distraction"], data["CognitiveLoad"])
plt.title("Gaze vs CLI")

plt.subplot(1,3,3)
plt.scatter(data["Stress"], data["CognitiveLoad"])
plt.title("Stress vs CLI")

plt.show()
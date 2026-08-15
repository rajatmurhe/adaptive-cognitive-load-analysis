import cv2
import mediapipe as mp
import numpy as np
import time
import csv
from collections import deque

#  SETUP 
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(refine_landmarks=True)

cap = cv2.VideoCapture(0)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_IRIS = [468, 469, 470, 471]

blink_times = []
blink_state = False
face_positions = deque(maxlen=20)

#  CSV 
logfile = open("cognitive_data.csv", "w", newline="")
writer = csv.writer(logfile)
writer.writerow(["Time", "BlinkRate", "Stress", "Distraction", "CognitiveLoad"])

#  CALIBRATION 
CALIBRATION_TIME = 60
start_time = time.time()
calibrating = True

blink_samples = []
gaze_samples = []
jitter_samples = []

baseline_blink = 1
baseline_gaze = 1
baseline_jitter = 1

# ---------------- TRACKING ----------------
cli_history = deque(maxlen=30)
phase = "Calibrating"
color = (255, 255, 255)

# NEW: stability + attention
cli_full = []
focus_start = None
max_focus_duration = 0

#  FUNCTION 
def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

#  MAIN LOOP 
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        lm = results.multi_face_landmarks[0].landmark

        left_eye = np.array([[int(lm[i].x * w), int(lm[i].y * h)] for i in LEFT_EYE])
        left_iris = np.array([[int(lm[i].x * w), int(lm[i].y * h)] for i in LEFT_IRIS])

        #  BLINK 
        EAR = eye_aspect_ratio(left_eye)
        if EAR < 0.22 and not blink_state:
            blink_times.append(time.time())
            blink_state = True
        if EAR > 0.25:
            blink_state = False

        blink_times = [t for t in blink_times if time.time() - t < 60]
        blink_rate = len(blink_times)

        #  GAZE 
        iris_center = left_iris.mean(axis=0)
        eye_center = left_eye.mean(axis=0)
        gaze_dev = abs(iris_center[0] - eye_center[0])

        #  HEAD JITTER 
        nose = lm[1]
        nose_point = np.array([int(nose.x * w), int(nose.y * h)])
        face_positions.append(nose_point)

        if len(face_positions) > 1:
            diffs = np.diff(np.array(face_positions), axis=0)
            jitter = np.mean(np.linalg.norm(diffs, axis=1))
        else:
            jitter = 0

        elapsed = int(time.time() - start_time)

        #  CALIBRATION 
        if calibrating:
            blink_samples.append(blink_rate)
            gaze_samples.append(gaze_dev)
            jitter_samples.append(jitter)

            cv2.putText(frame, f"Calibrating... {elapsed}/60 sec",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 255), 2)

            if elapsed >= CALIBRATION_TIME:
                baseline_blink = np.mean(blink_samples) + 1e-5
                baseline_gaze = np.mean(gaze_samples) + 1e-5
                baseline_jitter = np.mean(jitter_samples) + 1e-5
                calibrating = False

        #  AFTER CALIBRATION 
        else:
            fatigue = blink_rate / baseline_blink
            distraction = gaze_dev / baseline_gaze
            stress = jitter / baseline_jitter

            CLI = int((0.4 * fatigue + 0.3 * distraction + 0.3 * stress) * 50)

            cli_history.append(CLI)
            cli_full.append(CLI)

            #  STABILITY SCORE 
            if len(cli_full) > 10:
                std = np.std(cli_full)
                stability = max(0, 100 - std * 2)
            else:
                stability = 100

            #  PHASE DETECTION 
            if len(cli_history) == cli_history.maxlen:
                avg_cli = np.mean(cli_history)

                if avg_cli < 30:
                    phase = "Warm-up"
                    color = (0, 255, 0)
                elif avg_cli < 55:
                    phase = "Focused"
                    color = (255, 255, 0)
                elif avg_cli < 75:
                    phase = "Overload"
                    color = (0, 165, 255)
                else:
                    phase = "Fatigue"
                    color = (0, 0, 255)

            #  ATTENTION SPAN 
            if phase == "Focused":
                if focus_start is None:
                    focus_start = time.time()
                else:
                    duration = time.time() - focus_start
                    max_focus_duration = max(max_focus_duration, duration)
            else:
                focus_start = None

            #  DISPLAY 
            cv2.putText(frame, f"CLI: {CLI}%", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

            cv2.putText(frame, f"Phase: {phase}", (30, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

            cv2.putText(frame, f"Stability: {int(stability)}%",
                        (30, 140), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 255, 255), 2)

            cv2.putText(frame, f"Max Focus: {int(max_focus_duration)}s",
                        (30, 190), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 255, 255), 2)

            #  LOG 
            writer.writerow([time.time(), blink_rate, stress, distraction, CLI])

    cv2.imshow("Advanced Cognitive System", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break


#  CLEANUP 
logfile.close()
cap.release()
cv2.destroyAllWindows()
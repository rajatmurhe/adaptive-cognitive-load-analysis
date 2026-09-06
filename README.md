# Adaptive Cognitive Vision

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Adaptive%20Cognitive%20Vision-00C853?style=for-the-badge)](https://adaptive-cognitive-load-analysis.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Face%20Landmarks-FF6F00?style=for-the-badge)](https://ai.google.dev/edge/mediapipe/solutions/guide)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge)](https://render.com/)

> **Real-time webcam-based behavioral analysis using facial landmarks, geometric feature extraction, temporal signal processing, and explainable heuristic modeling — without training an ML/DL model.**

---

## Live Demo

### 🌐 [Open Adaptive Cognitive Vision](https://adaptive-cognitive-load-analysis.vercel.app/)

The application performs real-time browser-based facial landmark analysis and communicates behavioral features to a FastAPI backend through WebSockets.

**Note:** Webcam access requires browser permission and a secure HTTPS context.

---

## Overview

**Adaptive Cognitive Vision** is a real-time computer vision system designed to estimate behavioral indicators associated with cognitive load, attention, fatigue, distraction, and stress-like movement patterns.

Instead of using a trained machine learning or deep learning classifier, the system uses:

- Facial landmark geometry
- Eye Aspect Ratio (EAR)
- Iris-based gaze deviation
- Head movement estimation
- Personalized baseline calibration
- Temporal signal analysis
- Weighted signal fusion
- Rolling-window phase detection
- Explainable heuristic rules

The goal is to demonstrate how a practical behavioral analysis system can be built from **classical computer vision and signal-processing techniques**, while keeping the decision process interpretable.

---

# Problem Statement

Traditional webcam-based monitoring systems often rely on black-box ML/DL models that require datasets, training, inference infrastructure, and model maintenance.

This project explores an alternative:

> **Can behavioral signals extracted from facial geometry be transformed into an interpretable real-time cognitive-state indicator without training a machine learning model?**

The system focuses on measurable visual signals instead of attempting to directly diagnose or classify a person's mental or medical condition.

---

# 💡 Key Features

### 🎥 Real-Time Computer Vision

Processes webcam video continuously in the browser using MediaPipe Face Landmarker.

### 👁️ Blink Detection

Uses **Eye Aspect Ratio (EAR)** to detect eye closure events and estimate blink activity.

### 👀 Gaze Analysis

Uses iris position relative to the eye geometry to estimate gaze deviation from the personalized baseline.

### 🧭 Head Movement Analysis

Tracks facial/nose landmark movement over time to estimate head-motion instability.

### 🎯 Personalized Calibration

Each session begins with a calibration period to establish the user's normal behavioral baseline.

### 🧮 Cognitive Load Index

Combines normalized behavioral signals into a weighted heuristic Cognitive Load Index:

CLI =
    0.40 × Fatigue Signal
  + 0.30 × Distraction Signal
  + 0.30 × Stress Signal

The resulting value is scaled into a percentage-style indicator.

Temporal Behavioral Analysis

The system evaluates cognitive signals over time rather than relying only on individual frames.

Cognitive Phase Detection

A rolling window is used to classify the current behavioral trend into:

Warm-up
Focused
Overload
Fatigue
Stability Estimation

Measures variation in the Cognitive Load Index over time.

Lower variation → higher stability.

Attention Span

Tracks the maximum continuous duration during which the rolling system remains in the focused state.

💬 Explainable Output

The dashboard can surface behavioral reasons such as:

Blink activity above baseline
Gaze deviation above baseline
Head movement above baseline
Session Logging

Each session is stored as structured CSV data containing:

Time
BlinkRate
Stress
Distraction
CognitiveLoad
Phase
Stability
AttentionSpan
 Automated Session Reporting

Completed sessions can be transformed into an analytical PDF report containing:

Session statistics
Cognitive-load timeline
Behavioral signal plots
Cognitive phase distribution
Correlation analysis
Automated behavioral insights


```text
 System Architecture
                         USER WEBCAM
                              │
                              ▼
                     Browser / Frontend
                              │
                              ▼
                 MediaPipe Face Landmarker
                              │
                              ▼
                  Facial Landmark Geometry
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
       Blink / EAR       Gaze Deviation    Head Movement
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                     Behavioral Features
                              │
                              ▼
                         WebSocket
                              │
                              ▼
                         FastAPI API
                              │
                              ▼
                      Cognitive Engine
                              │
                              ├───────────────┐
                              │               │
                              ▼               ▼
                    Cognitive Load Index   Phase Detection
                              │               │
                              └───────┬───────┘
                                      ▼
                               Session Logging
                                      │
                                      ▼
                                CSV Session
                                      │
                                      ▼
                             Analysis Pipeline
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
               Time Analysis   Correlation Analysis   PDF Report
```
🧪 Methodology
1. Facial Landmark Extraction

The browser obtains facial landmarks from the webcam stream using MediaPipe.

These landmarks provide geometric information about:

Eyes
Iris
Nose
Face contour
Other facial regions
2. Blink Detection

The system calculates the Eye Aspect Ratio (EAR):

EAR = (A + B) / (2C)

where the distances between selected eye landmarks represent vertical and horizontal eye dimensions.

A lower EAR indicates eye closure.

3. Gaze Estimation

The iris center is compared with the eye center.

The resulting normalized horizontal displacement provides a gaze-deviation signal.

Gaze Deviation
    =
|Iris Center - Eye Center|
--------------------------
      Eye Width
4. Head Motion

The system tracks the nose landmark across consecutive frames.

The movement between consecutive positions is used as a simple head-motion signal.

Head Jitter
    =
Mean displacement
between recent positions
5. Personalized Calibration

The first part of a session establishes a subject-specific baseline for:

Blink activity
Gaze deviation
Head movement

This allows the system to compare later observations against the user's own baseline instead of relying only on fixed absolute values.

6. Signal Normalization

After calibration, each behavioral signal is normalized relative to its baseline.

Conceptually:

Normalized Signal =
Current Signal / Baseline Signal
7. Cognitive Load Fusion

The normalized signals are combined using a deterministic weighted model.

Fatigue     → 40%
Distraction → 30%
Stress      → 30%

The weighted result produces the Cognitive Load Index.

8. Temporal Modeling

Instead of interpreting every frame independently, the system maintains a rolling history of cognitive-load values.

This allows the system to identify behavioral phases using recent temporal context.

Analytics

After a session, the system generates analytical outputs including:

Cognitive Load Timeline

Tracks the Cognitive Load Index across the session.

Behavioral Signal Analysis

Visualizes:

Blink rate
Stress signal
Distraction signal
Phase Distribution

Shows how much of the session was classified as:

Warm-up
Focused
Overload
Fatigue
Correlation Analysis

Calculates Pearson correlation between:

Blink Rate
Stress
Distraction
Cognitive Load

This is used for exploratory analysis of relationships between the signals.

Important: correlation indicates statistical association, not causation.

Automated PDF Report

```text
A completed session can be converted into an analytical report containing:

Session Summary
        ↓
Cognitive Phase Distribution
        ↓
Cognitive Load Trend
        ↓
Behavioral Signal Analysis
        ↓
Correlation Analysis
        ↓
Automated Behavioral Insights
        ↓
Methodology + Disclaimer

```

Tech Stack
Category	Technologies
Computer Vision	OpenCV, MediaPipe
Browser Vision	MediaPipe Tasks Vision
Frontend	HTML, CSS, JavaScript
Visualization	Chart.js, Matplotlib
Backend	FastAPI
Real-Time Communication	WebSocket
Data Processing	NumPy, Pandas
Reporting	ReportLab
Frontend Deployment	Vercel
Backend Deployment	Render
Language	Python, JavaScript
gnitive_data.csv

# Adaptive Cognitive Load and Behavioral Analysis System

A real-time computer vision system for analyzing facial behavioral signals and estimating cognitive state using classical computer vision techniques.

## Overview

The system uses webcam input to analyze facial behavior in real time. It extracts measurable visual signals such as blinking, gaze deviation, and head movement and combines them using temporal analysis to generate interpretable cognitive-state indicators.

The project does not use a trained machine-learning model for the cognitive-state estimation.

## Key Features

- Real-time webcam processing
- 468-point facial landmark detection using MediaPipe FaceMesh
- Blink detection using Eye Aspect Ratio (EAR)
- Iris-based gaze estimation
- Head movement analysis
- Personalized baseline calibration
- Cognitive Load Index (CLI)
- Focus / overload / fatigue phase analysis
- Stability analysis
- Attention-span analysis
- Time-series visualization
- Correlation analysis
- Automated PDF report generation

## System Pipeline

Webcam
→
Face Detection & Landmarks
→
Feature Extraction
→
Blink / Gaze / Head Movement
→
Temporal Signal Processing
→
Cognitive Load Index
→
Phase Analysis
→
Visualization & Report

## Technologies

- Python 3.11
- OpenCV
- MediaPipe FaceMesh
- NumPy
- Pandas
- Matplotlib
- ReportLab

## Project Structure

```text
machinevisionproject/
│
├── vision_core.py
├── time_analysis.py
├── correlation_analysis.py
├── report_advanced.py
├── cognitive_data.csv
├── requirements.txt
├── README.md
└── .gitignore

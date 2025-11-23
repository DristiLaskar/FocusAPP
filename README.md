<h1 align="center">🧠⚡ FlowStateModel</h1>
<h3 align="center">AI-Powered Focus & Productivity Tracker</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Desktop-lightgrey?style=flat-square">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square">
</p>

<p align="center">
  <b>An intelligent Pomodoro system that tracks your focus using computer vision, window activity, and behavior patterns — helping you enter and maintain deep work flow states.</b>
</p>

---

## 🚀 What is FlowStateModel?

FlowStateModel is an AI-assisted productivity app that combines:

✅ **Mediapipe Face Mesh** — detects attention, drowsiness & head posture  
✅ **Webcam-based focus tracking**  
✅ **Window switching detection**  
✅ **Keyboard & mouse activity monitoring**  
✅ **Pomodoro-style session management**  
✅ **Flow analytics & insights dashboard**

It doesn’t just time your work —  
it *understands how focused you actually are.*

---

## 🧠 Core Features

### 🎯 **Smart Focus Detection**
- Detects when you're:
  - Looking away
  - Drowsy
  - Looking down
  - Not present
- Gives visual + audio alerts

### 🖥️ **Window / Tab Switch Monitoring**
- Detects when attention shifts to another app
- Logs interruptions as *flow breaks*

### ⏱️ **Adaptive Pomodoro Timer**
- Work + short break + long break cycles
- Auto-session switching
- Plays audio alerts

### 👁️ **Live Focus Dashboard**
Displays in real-time:
- Focus status (Focused / Unfocused / No Face)
- Keyboard & mouse activity
- Webcam feed overlay

### 📊 **Session Insights Popup**
After each session you get:
- Total work duration
- Total flow time
- Longest flow streak
- Focus ratio %
- Most common distraction triggers
- Personalized suggestions ✅

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| GUI | `CustomTkinter` |
| Face tracking | `Mediapipe FaceMesh` |
| Webcam processing | `OpenCV` |
| Audio alerts | `Pygame` |
| Activity monitoring | `pynput` |
| Window tracking | `pygetwindow` |
| Analytics engine | Custom Session Flow Model |

---

## 📦 Installation

### 1️⃣ Clone the repo

```bash
git clone https://github.com/DristiLaskar/FlowStateModel.git
cd FlowStateModel

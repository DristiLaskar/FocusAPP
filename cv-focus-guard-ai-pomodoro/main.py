import customtkinter as ctk
import threading
import time
import pygame
import cv2
import mediapipe as mp
from PIL import Image
from focus_detector import FocusDetector
from activity_tracker import ActivityTracker
from analytics import SessionAnalytics   # Analytics import


WORK_MIN = 25
SHORT_BREAK_MIN = 5
LONG_BREAK_MIN = 20
SESSIONS_BEFORE_LONG_BREAK = 4

SOUND_SESSION_END = "assets/session_end.mp3"
SOUND_FOCUS_ALERT = "assets/focus_alert.mp3"

COLOR_TEXT = "#FFFFFF"
COLOR_WARN = "#FFCC00"


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Guard")
        self.root.geometry("400x700")
        self.root.resizable(False, False)

        self.sessions = 0
        self.is_running = False
        self.is_paused = False
        self.current_time = WORK_MIN * 60
        self.current_session_type = "Work"
        self.timer_thread = None

        # Analytics tracking
        self.analytics = None
        self.previous_in_flow = False
        # Flags used in flow detection logic (placeholders for future features)
        self.window_warning_active = False
        self.inactivity_warning_active = False

        pygame.mixer.init()
        self.cap = cv2.VideoCapture(0)
        self.activity_tracker = ActivityTracker()

        from window_tracker import WindowTracker
        self.window_tracker = WindowTracker()

        # Face Mesh Model
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(
            thickness=1,
            circle_radius=1,
            color=(0, 255, 0)
        )

        self.unfocused_counter = 0
        self.VISUAL_WARNING_THRESHOLD_FRAMES = 15
        self.SOUND_ALERT_THRESHOLD_FRAMES = 45

        # UI
        self.session_label = ctk.CTkLabel(root, text="", font=("Helvetica", 24, "bold"))
        self.session_label.pack(pady=10)

        self.timer_label = ctk.CTkLabel(root, text="", font=("Helvetica", 80, "bold"))
        self.timer_label.pack(pady=10)

        self.unfocused_reason_label = ctk.CTkLabel(
            root, text="", font=("Helvetica", 16), text_color=COLOR_WARN
        )
        self.unfocused_reason_label.pack(pady=5)

        control_frame = ctk.CTkFrame(root, fg_color="transparent")
        control_frame.pack(pady=10)

        self.start_button = ctk.CTkButton(
            control_frame, text="Start", command=self.start_timer, width=90
        )
        self.start_button.pack(side="left", padx=4)

        self.pause_button = ctk.CTkButton(
            control_frame, text="Pause", command=self.pause_timer, width=90, state="disabled"
        )
        self.pause_button.pack(side="left", padx=4)

        self.reset_button = ctk.CTkButton(
            control_frame, text="Reset", command=self.reset_timer, width=90
        )
        self.reset_button.pack(side="left", padx=4)

        # Insights button (for analytics summary)
        self.insights_button = ctk.CTkButton(
            control_frame, text="Insights", command=self.show_insights, width=90
        )
        self.insights_button.pack(side="left", padx=4)

        self.webcam_label = ctk.CTkLabel(root, text="")
        self.webcam_label.pack(pady=10)

        # ---------- Simple Live Dashboard ----------
        self.dashboard_frame = ctk.CTkFrame(root)
        self.dashboard_frame.pack(fill="x", padx=10, pady=10)

        self.dashboard_title = ctk.CTkLabel(
            self.dashboard_frame,
            text="Live Focus Dashboard",
            font=("Helvetica", 16, "bold"),
        )
        self.dashboard_title.pack(anchor="w", padx=10, pady=(5, 5))

        self.focus_state_label = ctk.CTkLabel(
            self.dashboard_frame,
            text="Focus Status: -",
            font=("Helvetica", 14),
        )
        self.focus_state_label.pack(anchor="w", padx=15, pady=2)

        self.activity_state_label = ctk.CTkLabel(
            self.dashboard_frame,
            text="Activity: Keys=0 | Clicks=0",
            font=("Helvetica", 14),
        )
        self.activity_state_label.pack(anchor="w", padx=15, pady=(2, 8))

        self.update_display()
        self.update_webcam()

    # ----------------------------------------------------
    # Sound
    # ----------------------------------------------------
    def play_sound(self, sound_file):
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except pygame.error as e:
            print(f"Unable to play sound: {e}. Check assets folder.")

    # ----------------------------------------------------
    # Timer Logic
    # ----------------------------------------------------
    def update_display(self):
        mins, secs = divmod(self.current_time, 60)
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        self.session_label.configure(
            text=f"{self.current_session_type} Session ({self.sessions}/{SESSIONS_BEFORE_LONG_BREAK})"
        )

    def countdown(self):
        while self.is_running and self.current_time > 0:
            if not self.is_paused:
                self.current_time -= 1
                self.root.after(0, self.update_display)
                time.sleep(1)

        if self.is_running and self.current_time == 0:
            self.play_sound(SOUND_SESSION_END)
            self.root.after(0, self.next_session)

    def start_timer(self):
        if not self.is_running:
            self.is_running = True

            # Start analytics if this is a Work session
            if self.current_session_type == "Work":
                self.analytics = SessionAnalytics(start_time=time.time())
                self.previous_in_flow = False

            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.timer_thread = threading.Thread(target=self.countdown, daemon=True)
            self.timer_thread.start()

    def pause_timer(self):
        self.is_paused = not self.is_paused
        self.pause_button.configure(text="Resume" if self.is_paused else "Pause")

    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.sessions = 0
        self.current_session_type = "Work"
        self.current_time = WORK_MIN * 60
        self.update_display()
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled", text="Pause")
        self.unfocused_reason_label.configure(text="")
        self.unfocused_counter = 0

        # Finish analytics if a session was running
        if self.analytics:
            self.analytics.finish_session()
            self.analytics = None
            self.previous_in_flow = False

    def next_session(self):
        if self.current_session_type == "Work":
            # Work session just finished, close analytics session
            if self.analytics:
                self.analytics.finish_session()
                # keep analytics object so Insights can read it

            self.sessions += 1
            if self.sessions % SESSIONS_BEFORE_LONG_BREAK == 0:
                self.current_session_type = "Long Break"
                self.current_time = LONG_BREAK_MIN * 60
            else:
                self.current_session_type = "Short Break"
                self.current_time = SHORT_BREAK_MIN * 60
        else:
            self.current_session_type = "Work"
            self.current_time = WORK_MIN * 60

        self.is_paused = False
        self.update_display()
        self.timer_thread = threading.Thread(target=self.countdown, daemon=True)
        self.timer_thread.start()

    # ----------------------------------------------------
    # Webcam + Focus Detection + Flow Tracking + Dashboard
    # ----------------------------------------------------
    def update_webcam(self):
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(10, self.update_webcam)
            return

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        face_detected = results.multi_face_landmarks is not None
        print("Face detected" if face_detected else "No face detected")

        is_focus_active = (
            self.current_session_type == "Work" and self.is_running and not self.is_paused
        )

        # ---- Flow detection ----
        in_flow = (
            is_focus_active
            and face_detected
            and not self.window_warning_active
            and not self.inactivity_warning_active
        )

        now = time.time()

        if self.analytics:
            # FLOW OFF -> ON
            if in_flow and not self.previous_in_flow:
                self.analytics.start_flow(now)

            # FLOW ON -> OFF
            if not in_flow and self.previous_in_flow:
                reason = "Unknown"
                if self.window_warning_active:
                    reason = "Window Switch"
                elif self.inactivity_warning_active:
                    reason = "Inactivity"
                else:
                    reason = "Lost Focus"
                self.analytics.end_flow(now, reason)

        self.previous_in_flow = in_flow

        # ---- Focus detection UI / sound (existing behavior) ----
        unfocused_reason = None  # default so we can use it for dashboard later

        if results.multi_face_landmarks and is_focus_active:
            for face_landmarks in results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.drawing_spec
                )

            detector = FocusDetector(results.multi_face_landmarks[0].landmark)
            unfocused_reason = detector.is_unfocused()
            print(
                "Yaw =", detector.get_head_yaw(),
                "| Down =", detector.is_looking_down(),
                "| Drowsy =", detector.is_drowsy(),
                "| Reason =", unfocused_reason
            )

            if unfocused_reason:
                self.unfocused_counter += 1

                if self.unfocused_counter > self.VISUAL_WARNING_THRESHOLD_FRAMES:
                    self.unfocused_reason_label.configure(text=f"Warning: {unfocused_reason}")

                if self.unfocused_counter > self.SOUND_ALERT_THRESHOLD_FRAMES:
                    self.play_sound(SOUND_FOCUS_ALERT)
                    self.unfocused_counter = 0
            else:
                self.unfocused_counter = 0
                self.unfocused_reason_label.configure(text="")
        else:
            self.unfocused_counter = 0
            self.unfocused_reason_label.configure(text="")

        # ---- Activity tracking for dashboard ----
        activity = self.activity_tracker.get_activity()
        keyboard_presses = activity.get("keyboard_presses", 0)
        mouse_clicks = activity.get("mouse_clicks", 0)

        self.activity_state_label.configure(
            text=f"Activity: Keys={keyboard_presses} | Clicks={mouse_clicks}"
        )

        # ---- Focus Status text for dashboard ----
        if not self.is_running or self.current_session_type != "Work":
            focus_state = "Idle (Break / Not running)"
        elif not face_detected:
            focus_state = "No face detected"
        elif unfocused_reason:
            focus_state = f"Unfocused: {unfocused_reason}"
        else:
            focus_state = "Focused"

        self.focus_state_label.configure(text=f"Focus Status: {focus_state}")

        # ---- Show webcam frame ----
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(360, 270))
        self.webcam_label.configure(image=ctk_img)

        self.root.after(10, self.update_webcam)

    # ----------------------------------------------------
    # Insights popup (basic flow analytics + suggestions)
    # ----------------------------------------------------
    def show_insights(self):
        """
        Simple dashboard popup showing basic flow analytics
        for the current/last Work session.
        """
        if not self.analytics:
            win = ctk.CTkToplevel(self.root)
            win.title("Session Insights")
            ctk.CTkLabel(
                win,
                text="No analytics data yet.\nStart a Work session and let it run.",
                font=("Helvetica", 14),
                justify="center",
            ).pack(padx=20, pady=20)
            return

        a = self.analytics
        now = time.time()

        # Session duration
        session_end = a.end_time or now
        total_session = max(0, session_end - a.start_time)

        # Flow stats
        flow_time = 0.0
        longest_streak = 0.0
        for seg in a.flow_segments:
            seg_end = seg.end or now
            duration = max(0, seg_end - seg.start)
            flow_time += duration
            if duration > longest_streak:
                longest_streak = duration

        focus_ratio = (flow_time / total_session * 100) if total_session > 0 else 0.0

        # Break reasons (what ended flow)
        from collections import Counter
        break_reasons = [
            seg.break_reason for seg in a.flow_segments if seg.break_reason
        ]
        reason_counts = Counter(break_reasons)

        # ---- Build popup window ----
        win = ctk.CTkToplevel(self.root)
        win.title("Session Insights – Flow Analytics")
        win.geometry("420x420")

        # Summary
        ctk.CTkLabel(
            win,
            text="Flow Summary",
            font=("Helvetica", 18, "bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        summary_text = (
            f"Total Work Duration : {total_session/60:.1f} min\n"
            f"Total Flow Time     : {flow_time/60:.1f} min\n"
            f"Longest Flow Streak : {longest_streak/60:.1f} min\n"
            f"Focus Ratio         : {focus_ratio:.1f}%"
        )
        ctk.CTkLabel(
            win,
            text=summary_text,
            font=("Helvetica", 14),
            justify="left",
        ).pack(anchor="w", padx=20)

        # Break reasons
        ctk.CTkLabel(
            win,
            text="\nWhat usually breaks your flow:",
            font=("Helvetica", 16, "bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        if reason_counts:
            lines = []
            total_breaks = sum(reason_counts.values())
            for reason, count in reason_counts.most_common():
                pct = (count / total_breaks) * 100
                lines.append(f"- {reason}: {count} times ({pct:.0f}%)")
            ctk.CTkLabel(
                win,
                text="\n".join(lines),
                font=("Helvetica", 14),
                justify="left",
            ).pack(anchor="w", padx=25, pady=(0, 10))
        else:
            ctk.CTkLabel(
                win,
                text="- No flow breaks recorded yet.",
                font=("Helvetica", 14),
            ).pack(anchor="w", padx=25, pady=(0, 10))

        # ---- Suggestions Section ----
        suggestions = self.generate_suggestions(focus_ratio, longest_streak, reason_counts)

        ctk.CTkLabel(
            win,
            text="\nSuggestions",
            font=("Helvetica", 16, "bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            win,
            text="\n".join(f"• {s}" for s in suggestions),
            font=("Helvetica", 14),
            justify="left",
        ).pack(anchor="w", padx=25, pady=(0, 10))

    def generate_suggestions(self, focus_ratio, longest_streak, reason_counts):
        """
        Generate simple, actionable suggestions based on
        focus ratio, longest flow streak, and main break reasons.
        """
        suggestions = []

        # Overall focus %
        if focus_ratio < 40:
            suggestions.append(
                "Your focus ratio is below 40%. Try shorter sessions like 20–25 minutes."
            )
        elif focus_ratio < 70:
            suggestions.append(
                "Good focus! Reducing digital distractions may boost it further."
            )
        else:
            suggestions.append(
                "Excellent focus! Maintain the same routine and protect deep work time."
            )

        # Main break triggers
        if reason_counts:
            top_reason = reason_counts.most_common(1)[0][0]

            if "Window Switch" in top_reason:
                suggestions.append(
                    "Most breaks are from switching windows — close unused tabs/apps."
                )
            elif "Inactivity" in top_reason:
                suggestions.append(
                    "Inactivity breaks focus — set micro-goals before each session."
                )
            elif "Lost Focus" in top_reason:
                suggestions.append(
                    "Mental distraction detected — remove nearby physical distractions."
                )
            elif "Drowsy" in top_reason:
                suggestions.append(
                    "Drowsiness detected — take a short walk or rest before the next session."
                )
            else:
                suggestions.append(
                    f"Flow often ends due to: {top_reason}. Try to notice when this happens and adjust your environment."
                )

        # Flow streak duration
        if longest_streak < 15 * 60:
            suggestions.append(
                "Your longest streak is under 15 minutes — build up gradually with smaller goals."
            )
        else:
            suggestions.append(
                "You already maintain strong streaks — schedule longer deep-focus blocks when energy is highest."
            )

        return suggestions

    def on_closing(self):
        print("Closing application...")
        self.is_running = False

        # finalize analytics if running
        if self.analytics:
            self.analytics.finish_session()
            self.analytics = None

        self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = PomodoroTimer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

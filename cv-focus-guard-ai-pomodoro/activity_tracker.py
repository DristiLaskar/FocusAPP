from pynput import keyboard, mouse
import time

class ActivityTracker:
    def __init__(self):
        self.keyboard_presses = 0
        self.mouse_clicks = 0
        self.last_keyboard_time = None
        self.last_mouse_time = None

        self.keyboard_listener = keyboard.Listener(on_press=self.on_keypress)
        self.mouse_listener = mouse.Listener(on_click=self.on_click)

        self.keyboard_listener.start()
        self.mouse_listener.start()

    def on_keypress(self, key):
        self.keyboard_presses += 1
        self.last_keyboard_time = time.time()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.mouse_clicks += 1
            self.last_mouse_time = time.time()

    def get_activity(self):
        return {
            "keyboard_presses": self.keyboard_presses,
            "mouse_clicks": self.mouse_clicks,
            "last_keyboard_time": self.last_keyboard_time,
            "last_mouse_time": self.last_mouse_time
        }

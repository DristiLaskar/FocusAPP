import time
import pygetwindow as gw

class WindowTracker:
    def __init__(self):
        self.last_active_window = None
        self.last_switch_time = time.time()

    def get_active_window(self):
        try:
            win = gw.getActiveWindow()
            if win:
                return win.title
            return None
        except Exception:
            return None

    def check_switch(self):
        """
        Returns window title if a switch occurred, else None.
        """
        current = self.get_active_window()

        if current != self.last_active_window:
            self.last_switch_time = time.time()
            self.last_active_window = current
            return current

        return None

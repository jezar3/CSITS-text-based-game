import builtins
import contextlib
import ctypes
import os
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import game


class WindowOutput:
    encoding = "utf-8"

    def __init__(self, events):
        self.events = events

    def write(self, text):
        if text:
            self.events.put(("output", text))
        return len(text)

    def flush(self):
        return None

    def isatty(self):
        return True


class BackgroundMusic:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Background music file not found: {path}")

        self.alias = "EmberfallBackgroundMusic"
        self.winmm = ctypes.WinDLL("winmm")
        self.send_command = self.winmm.mciSendStringW
        self.send_command.argtypes = (
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
            ctypes.c_void_p,
        )
        self.send_command.restype = ctypes.c_uint
        self.get_error = self.winmm.mciGetErrorStringW
        self.get_error.argtypes = (ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint)
        self.get_error.restype = ctypes.c_int
        self.opened = False
        self.playing = False
        self._send(f'open "{path}" type mpegvideo alias {self.alias}')
        self.opened = True

    def _send(self, command):
        error_code = self.send_command(command, None, 0, None)
        if error_code:
            message = ctypes.create_unicode_buffer(256)
            if self.get_error(error_code, message, len(message)):
                raise RuntimeError(message.value)
            raise RuntimeError(f"Windows media error {error_code}.")

    def start(self):
        if not self.opened:
            raise RuntimeError("Background music is not open.")
        if not self.playing:
            self._send(f"play {self.alias} repeat")
            self.playing = True

    def stop(self):
        if self.opened and self.playing:
            self._send(f"stop {self.alias}")
            self.playing = False

    def close(self):
        if self.opened:
            self._send(f"close {self.alias}")
            self.opened = False
            self.playing = False


class GameWindow:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.answers = queue.Queue()
        self.keys = queue.Queue()
        self.input_enabled = False
        self.key_mode = False
        self.action_prompt = False
        self.closing = False
        self.fullscreen = False
        self.fit_pending = False
        self.input_frame = None
        self.output = WindowOutput(self.events)

        icon_directory = getattr(
            sys,
            "_MEIPASS",
            os.path.dirname(os.path.abspath(__file__)),
        )
        icon_path = os.path.join(icon_directory, "icon.png")
        self.window_icon = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, self.window_icon)

        root.title("The Emberfall Chronicles")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1100, max(640, screen_width - 80))
        window_height = min(850, max(480, screen_height - 100))
        root.geometry(
            f"{window_width}x{window_height}"
            f"+{(screen_width - window_width) // 2}"
            f"+{(screen_height - window_height) // 2}"
        )
        root.minsize(min(640, window_width), min(480, window_height))
        root.configure(background="#080b0a")

        self.game_font = tkfont.Font(root=root, family="Consolas", size=13)
        self.bold_font = tkfont.Font(
            root=root,
            family="Consolas",
            size=13,
            weight="bold",
        )
        self.entry_font = tkfont.Font(root=root, family="Consolas", size=12)
        self.entry_label_font = tkfont.Font(
            root=root,
            family="Consolas",
            size=10,
            weight="bold",
        )
        self.hint_font = tkfont.Font(root=root, family="Consolas", size=9)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Game.TEntry",
            fieldbackground="#101714",
            foreground="#e2f5e8",
            insertcolor="#e2f5e8",
            font=self.entry_font,
        )

        self.screen = tk.Text(
            root,
            background="#080b0a",
            foreground="#d7f5df",
            insertbackground="#d7f5df",
            selectbackground="#e2c453",
            selectforeground="#17150b",
            font=self.game_font,
            wrap="none",
            state="disabled",
            padx=16,
            pady=14,
            spacing1=0,
            spacing3=1,
            borderwidth=0,
            highlightthickness=0,
        )
        self.screen.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        self.screen.bind("<Configure>", self.schedule_screen_fit, add="+")
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.screen.yview)
        scrollbar.place(relx=1.0, rely=0.0, relheight=0.89, anchor="ne")
        self.screen.configure(yscrollcommand=scrollbar.set)
        self.foreground_tags = {
            30: "ansi_black",
            31: "ansi_red",
            32: "ansi_green",
            33: "ansi_yellow",
            34: "ansi_blue",
            35: "ansi_magenta",
            36: "ansi_cyan",
            37: "ansi_white",
            90: "ansi_bright_black",
            91: "ansi_bright_red",
            92: "ansi_bright_green",
            93: "ansi_selected_yellow",
            94: "ansi_bright_blue",
            95: "ansi_bright_magenta",
            96: "ansi_bright_cyan",
            97: "ansi_bright_white",
        }
        foreground_colors = {
            30: "#68766f",
            31: "#e97870",
            32: "#78c987",
            33: "#d6b65f",
            34: "#72a8ed",
            35: "#c18ad9",
            36: "#65c8ce",
            37: "#c6d2ca",
            90: "#829188",
            91: "#ff8b82",
            92: "#9be6a4",
            93: "#ffe17a",
            94: "#91beff",
            95: "#d8a3ef",
            96: "#8ce5e8",
            97: "#f3f8f4",
        }
        for code, tag in self.foreground_tags.items():
            options = {"foreground": foreground_colors[code]}
            if code == 93:
                options.update(background="#403714", font=self.bold_font)
            self.screen.tag_configure(tag, **options)
        self.screen.tag_configure("ansi_bold", font=self.bold_font)
        self.custom_foreground_tags = {}
        self.active_foreground = None
        self.active_bold = False

        self.entry = None
        self.submit_button = None
        footer = tk.Frame(root, background="#080b0a")
        footer.pack(fill="x", padx=14, pady=(0, 8))
        self.hint = tk.Label(
            footer,
            text=(
                "Hero selection: use UP/DOWN arrows, then ENTER. "
                "In combat, press A/S/P/F to choose an action."
            ),
            foreground="#82958a",
            background="#080b0a",
            font=self.hint_font,
            anchor="w",
        )
        self.hint.pack(side="left", fill="x", expand=True)
        self.music_button = ttk.Button(
            footer,
            text="Music: Unavailable",
            command=self.toggle_music,
            state="disabled",
        )
        self.music_button.pack(side="right", padx=(8, 0))
        self.set_input_enabled(False)

        root.bind_all("<KeyPress>", self.on_key)
        root.bind("<Configure>", self.schedule_screen_fit, add="+")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(20, self.drain_events)
        root.after_idle(self.fit_screen_text)

        self.music = None
        music_directory = getattr(
            sys,
            "_MEIPASS",
            os.path.dirname(os.path.abspath(__file__)),
        )
        music_path = os.path.join(music_directory, "Rókatánc.mp3")
        try:
            self.music = BackgroundMusic(music_path)
            self.music.start()
            self.music_button.configure(text="Music: On", state="normal")
        except (OSError, RuntimeError) as error:
            self.music_button.configure(text="Music: Unavailable")
            messagebox.showerror("Background music error", str(error), parent=root)

        self.worker = threading.Thread(target=self.run_game, daemon=True)
        self.worker.start()

    def toggle_music(self):
        if self.music is None:
            return
        try:
            if self.music.playing:
                self.music.stop()
                self.music_button.configure(text="Music: Off")
            else:
                self.music.start()
                self.music_button.configure(text="Music: On")
        except RuntimeError as error:
            self.music_button.configure(text="Music: Error", state="disabled")
            messagebox.showerror("Background music error", str(error), parent=self.root)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        self.schedule_screen_fit()

    def schedule_screen_fit(self, _event=None):
        if not self.fit_pending and not self.closing:
            self.fit_pending = True
            self.root.after_idle(self.fit_screen_text)

    def fit_screen_text(self):
        self.fit_pending = False
        if self.closing or not self.screen.winfo_ismapped():
            return

        lines = self.screen.get("1.0", "end-1c").splitlines()
        widest_line = max((len(line) for line in lines), default=1)
        available_width = max(1, self.screen.winfo_width() - 48)

        selected_size = 7
        for size in range(13, 6, -1):
            self.game_font.configure(size=size)
            line_width = widest_line * self.game_font.measure("M")
            if line_width <= available_width:
                selected_size = size
                break

        self.game_font.configure(size=selected_size)
        self.bold_font.configure(size=selected_size)
        self.entry_font.configure(size=max(8, selected_size))
        self.entry_label_font.configure(size=max(8, selected_size - 2))
        self.hint_font.configure(size=max(8, selected_size - 4))

    def set_input_enabled(self, enabled):
        self.input_enabled = enabled
        if self.entry is not None and self.submit_button is not None:
            state = "normal" if enabled else "disabled"
            self.entry.configure(state=state)
            self.submit_button.configure(state=state)
        if enabled and self.entry is not None:
            self.entry.focus_set()
        else:
            self.root.focus_set()

    def on_key(self, event):
        if self.closing:
            return
        if event.keysym == "F11":
            self.toggle_fullscreen()
            return "break"
        if event.keysym == "Escape" and self.fullscreen:
            self.toggle_fullscreen()
            return "break"
        if self.input_enabled:
            action = event.char.lower()
            if (
                self.action_prompt
                and self.entry is not None
                and action in {"a", "s", "p", "f"}
            ):
                if not self.entry.get().strip():
                    self.entry.insert(0, action)
                if self.entry.get().strip().lower() == action:
                    self.submit_answer()
                    return "break"
            return
        if not self.key_mode:
            return
        keys = {
            "Up": "UP",
            "Down": "DOWN",
            "Left": "LEFT",
            "Right": "RIGHT",
            "Return": "ENTER",
        }
        key = keys.get(event.keysym)
        if key is None and event.char:
            key = event.char.lower()
        if key is not None:
            self.keys.put(key)

    def poll_key(self):
        self.key_mode = True
        try:
            key = self.keys.get_nowait()
        except queue.Empty:
            return None
        self.key_mode = False
        return key

    def on_submit(self, _event=None):
        self.submit_answer()
        return "break"

    def submit_answer(self):
        if not self.input_enabled or self.entry is None:
            return
        answer = self.entry.get()
        self.entry.delete(0, "end")
        self.set_input_enabled(False)
        self.action_prompt = False
        self.remove_input_widget()
        self.events.put(("output", f"> {answer}\n"))
        self.answers.put(answer)

    def request_input(self, prompt=""):
        if prompt:
            self.events.put(("output", prompt))
        self.events.put(("input", prompt))
        answer = self.answers.get()
        if answer is None:
            raise EOFError
        return answer

    def render_output(self, text):
        tokens = re.split(r"(\x1b\[[0-?]*[ -/]*[@-~])", text)
        self.screen.configure(state="normal")
        for token in tokens:
            if token in ("\x1b[2J", "\x1b[H"):
                self.screen.delete("1.0", "end")
                self.active_foreground = None
                self.active_bold = False
                continue
            if token.startswith("\x1b[") and token.endswith("m"):
                self.apply_sgr(token[2:-1])
                continue
            if token.startswith("\x1b["):
                continue
            if token:
                tags = []
                if self.active_foreground is not None:
                    tags.append(self.active_foreground)
                if self.active_bold:
                    tags.append("ansi_bold")
                self.screen.insert("end", token, tuple(tags))

        if int(self.screen.index("end-1c").split(".")[0]) > 2500:
            self.screen.delete("1.0", "500.0")
        self.screen.see("end")
        self.screen.configure(state="disabled")
        self.schedule_screen_fit()

    def show_input_widget(self, prompt):
        self.action_prompt = prompt.strip() == ">"
        self.screen.configure(state="normal")
        self.screen.insert("end-1c", "\n")
        index = self.screen.index("end-1c")
        self.screen.mark_set("game_input", index)
        self.screen.mark_gravity("game_input", "left")

        self.input_frame = tk.Frame(
            self.screen,
            background="#111914",
            padx=10,
            pady=8,
        )
        prompt_text = prompt.strip()
        if "name" in prompt_text.lower():
            label = "YOUR NAME"
        elif "continue" in prompt_text.lower():
            label = "CONTINUE"
        elif "boon" in prompt_text.lower() or "reward" in prompt_text.lower():
            label = "VICTORY BOON"
        else:
            label = "YOUR MOVE"
        tk.Label(
            self.input_frame,
            text=label,
            foreground="#ffe17a",
            background="#111914",
            font=self.entry_label_font,
        ).pack(side="left", padx=(0, 10))
        self.entry = ttk.Entry(
            self.input_frame,
            style="Game.TEntry",
            font=self.entry_font,
            width=34,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.entry.bind("<Return>", self.on_submit)
        self.submit_button = ttk.Button(
            self.input_frame,
            text="Enter",
            command=self.submit_answer,
        )
        self.submit_button.pack(side="left", padx=(8, 0), ipady=3)
        self.screen.window_create("game_input", window=self.input_frame)
        self.screen.insert("end-1c", "\n")
        self.screen.configure(state="disabled")
        self.screen.see("end")
        self.set_input_enabled(True)
        self.hint.configure(
            text=(
                "Combat: press A attack, S special, P potion, F flee."
                if self.action_prompt
                else "Type your answer here and press Enter. "
                "Use UP/DOWN arrows to choose a hero."
            )
        )
        self.schedule_screen_fit()

    def remove_input_widget(self):
        if self.input_frame is None:
            return
        self.screen.configure(state="normal")
        start = self.screen.index("game_input")
        self.screen.delete(start, f"{start} +1c")
        self.screen.mark_unset("game_input")
        self.input_frame.destroy()
        self.input_frame = None
        self.entry = None
        self.submit_button = None
        self.screen.configure(state="disabled")

    def apply_sgr(self, parameters):
        codes = [int(value or "0") for value in parameters.split(";")]
        index = 0
        while index < len(codes):
            code = codes[index]
            if code == 0:
                self.active_foreground = None
                self.active_bold = False
            elif code == 1:
                self.active_bold = True
            elif code == 22:
                self.active_bold = False
            elif code == 39:
                self.active_foreground = None
            elif code in self.foreground_tags:
                self.active_foreground = self.foreground_tags[code]
            elif (
                code == 38
                and index + 4 < len(codes)
                and codes[index + 1] == 2
            ):
                red, green, blue = codes[index + 2:index + 5]
                color = f"#{red:02x}{green:02x}{blue:02x}"
                tag = self.custom_foreground_tags.get(color)
                if tag is None:
                    tag = f"ansi_{color[1:]}"
                    self.screen.tag_configure(tag, foreground=color)
                    self.custom_foreground_tags[color] = tag
                self.active_foreground = tag
                index += 4
            index += 1

    def drain_events(self):
        output = []
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "output":
                output.append(value)
            elif kind == "input":
                if output:
                    self.render_output("".join(output))
                    output.clear()
                self.show_input_widget(value)
            elif kind == "error":
                if not self.closing:
                    messagebox.showerror("Game error", value, parent=self.root)
            elif kind == "done":
                if not self.closing:
                    self.hint.configure(text="Game ended. Close this window to exit.")
                    self.set_input_enabled(False)
        if output:
            self.render_output("".join(output))
        if not self.closing:
            self.root.after(20, self.drain_events)

    def run_game(self):
        previous_input = builtins.input
        previous_stdin = game.sys.stdin
        previous_system = game.os.system
        game.terminal_keys = contextlib.nullcontext
        game.windows_quick_edit_disabled = contextlib.nullcontext
        game.poll_key = self.poll_key
        game.sys.stdin = type("WindowInputStatus", (), {"isatty": lambda self: True})()
        game.os.system = lambda _command: 0
        builtins.input = self.request_input
        try:
            with contextlib.redirect_stdout(self.output):
                game.main()
        except Exception as error:
            self.events.put(("error", f"{type(error).__name__}: {error}"))
        finally:
            builtins.input = previous_input
            game.sys.stdin = previous_stdin
            game.os.system = previous_system
            self.events.put(("done", None))

    def close(self):
        self.closing = True
        self.answers.put(None)
        if self.music is not None:
            try:
                self.music.close()
            except RuntimeError as error:
                messagebox.showerror(
                    "Background music error",
                    str(error),
                    parent=self.root,
                )
        self.root.destroy()


def main():
    root = tk.Tk()
    GameWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

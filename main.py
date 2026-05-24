from __future__ import annotations

import sys
import threading
from pathlib import Path
from tkinter import Tk, StringVar, filedialog, messagebox, ttk

try:
    import cv2
    import numpy as np
    import pyvirtualcam
except ModuleNotFoundError as exc:
    _missing_module = exc.name or "a required module"
    _root = Tk()
    _root.withdraw()
    messagebox.showerror(
        "Virtual Web Camera",
        f"Missing dependency: {_missing_module}\n\nRun:\npython -m pip install -r requirements.txt",
    )
    _root.destroy()
    sys.exit(1)


class VirtualWebcamApp:
    BACKEND_CHOICES = {
        "external": "obs",
        "unitycapture": "unitycapture",
        "auto": "auto",
    }

    DISPLAY_NAMES = {
        "external": "External Camera",
        "unitycapture": "Unity Capture",
        "auto": "Auto-detect",
    }

    def __init__(self, *, default_backend: str = "external", backend_locked: bool = False) -> None:
        self.root = Tk()
        self.root.title("Virtual Web Camera")
        self.root.geometry("460x220")
        self.root.resizable(False, False)

        self.video_path: Path | None = None
        self.stream_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.is_streaming = False
        self.backend_locked = backend_locked
        self.backend_name = StringVar(value=default_backend)

        self.status_text = StringVar(value="Choose a video to start streaming to the virtual camera.")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="Virtual Web Camera", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            frame,
            text="Pick a video and it will loop into the system virtual camera until you stop it.",
            wraplength=420,
        )
        subtitle.pack(anchor="w", pady=(4, 12))

        self.video_label = ttk.Label(frame, text="No video selected.")
        self.video_label.pack(anchor="w")

        if self.backend_locked:
            backend_row = ttk.Frame(frame)
            backend_row.pack(fill="x", pady=(10, 0))
            ttk.Label(backend_row, text="Virtual camera backend:").pack(side="left")
            ttk.Label(backend_row, text=self._backend_display_name(self.backend_name.get())).pack(side="left", padx=(8, 0))
        else:
            backend_row = ttk.Frame(frame)
            backend_row.pack(fill="x", pady=(10, 0))

            ttk.Label(backend_row, text="Virtual camera backend:").pack(side="left")
            backend_select = ttk.Combobox(
                backend_row,
                textvariable=self.backend_name,
                values=("external", "unitycapture", "auto"),
                state="readonly",
                width=18,
            )
            backend_select.pack(side="left", padx=(8, 0))
            ttk.Label(backend_row, text="External Camera uses OBS Virtual Camera underneath.").pack(side="left", padx=(10, 0))

        ttk.Label(frame, textvariable=self.status_text, wraplength=420).pack(anchor="w", pady=(12, 12))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(8, 0))

        self.start_button = ttk.Button(buttons, text="Choose Video & Start", command=self.choose_and_start)
        self.start_button.pack(side="left")

        self.stop_button = ttk.Button(buttons, text="Stop", command=self.stop_streaming, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))

        ttk.Button(buttons, text="Exit", command=self.close).pack(side="right")

    def run(self) -> None:
        self.root.after(100, self.choose_and_start)
        self.root.mainloop()

    def choose_and_start(self) -> None:
        if self.is_streaming:
            messagebox.showinfo("Virtual Web Camera", "Streaming is already running.")
            return

        video_file = filedialog.askopenfilename(
            title="Select a video to stream",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.wmv *.m4v"),
                ("All files", "*.*"),
            ],
        )

        if not video_file:
            self.status_text.set("No video selected yet.")
            return

        selected_path = Path(video_file)
        self.video_path = selected_path
        self.video_label.config(text=f"Video: {selected_path.name}")

        if not messagebox.askyesno(
            "Start streaming",
            f"Play {selected_path.name} in the virtual camera now?",
        ):
            self.status_text.set("Video selection saved. Use Start again when ready.")
            return

        self.start_streaming(selected_path)

    def start_streaming(self, video_path: Path) -> None:
        self.stop_event.clear()
        self.is_streaming = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_text.set("Starting virtual camera stream...")

        self.stream_thread = threading.Thread(target=self._stream_video, args=(video_path,), daemon=True)
        self.stream_thread.start()

    def _selected_backend(self) -> str | None:
        backend = self.backend_name.get().strip().lower()
        backend = self.BACKEND_CHOICES.get(backend, backend)
        if backend == "auto":
            return None
        return backend

    def _backend_display_name(self, backend: str) -> str:
        backend_key = backend.strip().lower()
        if self.backend_locked and backend_key == "obs":
            backend_key = "external"
        return self.DISPLAY_NAMES.get(backend_key, backend)

    def _stream_video(self, video_path: Path) -> None:
        try:
            capture = cv2.VideoCapture(str(video_path))
            if not capture.isOpened():
                raise RuntimeError(f"Could not open video: {video_path}")

            fps = capture.get(cv2.CAP_PROP_FPS)
            if not fps or fps <= 0:
                fps = 30.0

            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if width <= 0 or height <= 0:
                ok, first_frame = capture.read()
                if not ok:
                    raise RuntimeError("The selected video contains no readable frames.")
                height, width = first_frame.shape[:2]
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

            backend = self._selected_backend()
            with pyvirtualcam.Camera(width=width, height=height, fps=fps, backend=backend) as camera:
                self.root.after(
                    0,
                    lambda: self.status_text.set(
                        f"Streaming to {camera.device} at {width}x{height} @ {fps:.2f} FPS"
                    ),
                )

                while not self.stop_event.is_set():
                    ok, frame = capture.read()
                    if not ok:
                        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue

                    if frame.shape[1] != width or frame.shape[0] != height:
                        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    camera.send(np.ascontiguousarray(rgb_frame))
                    camera.sleep_until_next_frame()
        except Exception as exc:  # pragma: no cover - runtime errors should be surfaced to the user
            backend = self.backend_name.get().strip().lower()
            backend = self.BACKEND_CHOICES.get(backend, backend)
            if backend == "obs":
                detail = (
                    "External Camera was not found or is not running.\n\n"
                    "Open OBS Studio and click Start Virtual Camera first, then run this app again.\n"
                    "If you do not want the external camera, choose Unity Capture or Auto-detect instead."
                )
            elif backend == "unitycapture":
                detail = (
                    "Unity Capture was not found. Install and enable the Unity Capture virtual camera driver,\n"
                    "or switch the backend to External Camera or Auto-detect."
                )
            else:
                detail = (
                    "No virtual camera backend was found. Install OBS Virtual Camera or Unity Capture,\n"
                    "then choose the matching backend in this app."
                )
            self.root.after(0, lambda: messagebox.showerror("Virtual Web Camera", str(exc)))
            self.root.after(0, lambda: messagebox.showinfo("Virtual Web Camera", detail))
            self.root.after(0, lambda: self.status_text.set("Streaming failed. Check the selected virtual camera backend."))
        finally:
            self.root.after(0, self._stream_finished)

    def _stream_finished(self) -> None:
        self.is_streaming = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.video_path:
            self.status_text.set("Streaming stopped. Choose the same video or a different one to start again.")
        else:
            self.status_text.set("Choose a video to start streaming to the virtual camera.")

    def stop_streaming(self) -> None:
        if not self.is_streaming:
            return

        self.stop_event.set()
        self.status_text.set("Stopping stream...")

    def close(self) -> None:
        self.stop_streaming()
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        self.root.destroy()


def main(*, default_backend: str = "external", backend_locked: bool = False) -> None:
    app = VirtualWebcamApp(default_backend=default_backend, backend_locked=backend_locked)
    app.run()


if __name__ == "__main__":
    main()
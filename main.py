from __future__ import annotations

import threading
from pathlib import Path
from tkinter import Tk, StringVar, filedialog, messagebox, ttk

import cv2
import numpy as np
import pyvirtualcam


class VirtualWebcamApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Virtual Web Camera")
        self.root.geometry("460x220")
        self.root.resizable(False, False)

        self.video_path: Path | None = None
        self.stream_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.is_streaming = False

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

            with pyvirtualcam.Camera(width=width, height=height, fps=fps) as camera:
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
            self.root.after(0, lambda: messagebox.showerror("Virtual Web Camera", str(exc)))
            self.root.after(0, lambda: self.status_text.set("Streaming failed. Check that a virtual camera backend is installed."))
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


def main() -> None:
    app = VirtualWebcamApp()
    app.run()


if __name__ == "__main__":
    main()
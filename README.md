# Virtual Web Camera

This app plays a video file into a system virtual camera on Windows.

When the video reaches the end, it automatically loops back to the first frame and keeps streaming until you stop it.

## What you need

This is a single Python app, but Windows still needs a virtual camera driver/backend installed once so the app has a camera device to send frames to.

Recommended backend options:

1. Unity Capture.
2. Any other virtual camera driver supported by `pyvirtualcam`.

If you choose `obs`, open OBS Studio first and click **Start Virtual Camera** before launching this app.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## Build a single app

This creates one Windows executable that packages the Python code and its libraries into a single file.

```powershell
.\build.ps1
```

The output will be in `dist\VirtualWebCamera.exe`.

## Create a release package

This makes a zip file that includes the packaged executable and the README.

```powershell
.\package.ps1
```

The output will be in `release\VirtualWebCamera-package.zip`.

## Run

```powershell
python main.py
```

Or run the packaged app directly:

```powershell
.\dist\VirtualWebCamera.exe
```

The app will ask you to choose a video and a virtual camera backend. If you pick `obs`, start the OBS virtual camera first. Once streaming starts, pick the virtual camera in Zoom, Teams, Meet, Discord, or any other app.

## Behavior

- The selected video is streamed as a webcam feed.
- Playback loops automatically when the video ends.
- Use the Stop button to stop the virtual camera output.

## Troubleshooting

- If you choose `obs` and see a camera-not-found error, start OBS Studio and click **Start Virtual Camera**.
- If you see an error about no virtual camera backend, install a supported virtual camera driver such as Unity Capture first.
- If the video fails to open, try another format such as MP4 or MOV.
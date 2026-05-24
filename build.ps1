$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pyinstaller | Out-Host
python -m PyInstaller --noconfirm --onefile --windowed --name VirtualWebCamera main.py | Out-Host
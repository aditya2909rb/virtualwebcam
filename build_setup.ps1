$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pyinstaller | Out-Host
python -m PyInstaller --noconfirm --onefile --windowed --name VirtualWebCamera-Setup --distpath setup-dist --workpath setup-build --specpath setup-build bootstrapper.py | Out-Host
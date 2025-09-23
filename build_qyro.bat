@echo off
set VERSION=1.0.0

echo Updating version to %VERSION% in package.json...
copy package.json qyro\cli_commands\ /Y

echo cleaning up previous builds...
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q *.egg-info

echo Building wheel for qyro v%VERSION% with Poetry...
poetry build

echo Uninstalling previous version...
pip uninstall -y qyro

echo Installing local wheel...
pip install dist\qyro-%VERSION%-py3-none-any.whl

echo ✅ Installation completed for qyro v%VERSION%

pause
@echo off
title Iniciando Sistema de Caja...
cd /d "%~dp0"

echo ===================================================
echo Verificando e instalando dependencias del sistema...
echo Si es la primera vez, esto puede tardar un momento.
echo ===================================================
python -m pip install -r requirements.txt -q

if not exist "%USERPROFILE%\Desktop\Control de Caja.lnk" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$HOME\Desktop\Control de Caja.lnk'); $Shortcut.TargetPath = '%~dp0Control de Caja.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = '%~dp0icono.ico'; $Shortcut.Save()"
)

if not exist "Control de Caja - Acceso Directo.lnk" (
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%~dp0Control de Caja - Acceso Directo.lnk'); $Shortcut.TargetPath = '%~dp0Control de Caja.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = '%~dp0icono.ico'; $Shortcut.Save()"
)

start pythonw app.py
exit

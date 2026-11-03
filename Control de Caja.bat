@echo off
title Iniciando Sistema de Caja y Proveedores...
cd /d "%~dp0"

echo ===================================================
echo Verificando e instalando dependencias del sistema...
echo ===================================================
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt --no-cache-dir -q

:: Crear acceso directo limpio sin errores de ruta
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Control de Caja.lnk'); $Shortcut.TargetPath = '%~dp0Control de Caja.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = '%~dp0icono.ico'; $Shortcut.Save()"

start pythonw app.py
exit

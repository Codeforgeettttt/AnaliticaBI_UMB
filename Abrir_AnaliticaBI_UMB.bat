@echo off
title AnaliticaBI UMB
cd /d "%~dp0"
echo Carpeta: %cd%
echo.

set SCRIPT_PY=AnaliticaBI_UMB_App.py
if not exist "%SCRIPT_PY%" (
    echo [ERROR] No encuentro AnaliticaBI_UMB_App.py en esta carpeta.
    echo Pon este .bat junto al archivo .py y vuelve a abrirlo.
    goto fin
)

call :buscarpy
if defined PY goto tienepy

echo Python no esta instalado. Instalandolo automaticamente con winget...
echo (puede tardar 1-3 minutos, no cierres esta ventana)
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
call :buscarpy
if defined PY goto tienepy

echo.
echo [ERROR] No se pudo instalar Python automaticamente.
echo Instalalo a mano desde https://www.python.org/downloads/
echo y marca la casilla "Add Python to PATH". Luego abre este .bat otra vez.
goto fin

:tienepy
echo Usando: %PY%
%PY% --version

%PY% -c "import pandas, matplotlib, tkinter" >nul 2>nul
if not errorlevel 1 goto lanzar
echo Instalando dependencias, espera un momento...
%PY% -m pip install --disable-pip-version-check pandas matplotlib
%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Tu Python no trae tkinter. Reinstala Python desde python.org y deja marcada la opcion "tcl/tk and IDLE".
    goto fin
)

:lanzar
echo Abriendo la aplicacion...
%PY% "%SCRIPT_PY%"
echo.
echo Codigo de salida de la aplicacion: %errorlevel%

:fin
echo.
echo Presiona una tecla para cerrar esta ventana.
pause >nul
exit /b

:buscarpy
set PY=
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set PY=py -3
    exit /b
)
python -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set PY=python
    exit /b
)
for %%V in (313 312 311 310) do (
    if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
        set PY="%LocalAppData%\Programs\Python\Python%%V\python.exe"
        exit /b
    )
)
exit /b

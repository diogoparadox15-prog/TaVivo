@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

cd /d "%~dp0"
title TaVivo - Terminal Offline de Emergencia

echo ============================================================================
echo   TaVivo - Assistente de Sobrevivencia Offline
echo   Construido por Capitain Of Cruzades.
echo ============================================================================
echo.

set "LLAMA_PORT=9931"
set "WEB_PORT=9876"
set "LLAMA_BIN=bin\llama-server.exe"
set "MODEL_PATH=models\LFM3-Omni-2B-Uncensored-abliterated-Q4_K_M.gguf"
set "MMPROJ_PATH=models\mmproj-LFM3-Omni-2B-Q4_K_M.gguf"
set "NO_PROXY=127.0.0.1,localhost"
set "no_proxy=127.0.0.1,localhost"

:: Detectar Python portatil embutido ou Python do sistema
set "PYTHON_BIN="
if exist "python\python.exe" (
    set "PYTHON_BIN=python\python.exe"
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_BIN=python"
    )
)

if "%PYTHON_BIN%"=="" (
    echo [ERRO] Python nao encontrado em python\python.exe nem no PATH do sistema.
    echo Execute preparar_pacote.py ou instale o pacote Windows completo.
    pause
    exit /b 1
)

if not exist "%LLAMA_BIN%" (
    echo [AVISO] Binario %LLAMA_BIN% nao encontrado.
    echo O servidor web iniciara, mas o Motor IA na porta %LLAMA_PORT% ficara offline.
) else if not exist "%MODEL_PATH%" (
    echo [AVISO] Modelo %MODEL_PATH% nao encontrado.
    echo O servidor web iniciara, mas o Motor IA na porta %LLAMA_PORT% ficara offline.
) else (
    echo [1/2] Iniciando Motor IA ^(llama-server^) na porta %LLAMA_PORT%...
    set "PATH=%~dp0bin;%PATH%"
    set "NO_PROXY=127.0.0.1,localhost"
    set "no_proxy=127.0.0.1,localhost"
    set "LLAMA_HW_ARGS=-c 4096 -np 1"
    if exist "tavivo_bench.py" (
        for /f "delims=" %%A in ('"%PYTHON_BIN%" tavivo_bench.py --args 2^>nul') do set "LLAMA_HW_ARGS=%%A"
    )
    echo       Perfil de hardware: !LLAMA_HW_ARGS!
    if exist "%MMPROJ_PATH%" (
        start "TaVivo Motor IA (9931)" /B cmd /c ""%LLAMA_BIN%" -m "%MODEL_PATH%" --mmproj "%MMPROJ_PATH%" --host 127.0.0.1 --port %LLAMA_PORT% !LLAMA_HW_ARGS! > "%~dp0tavivo_llama.log" 2>&1"
    ) else (
        start "TaVivo Motor IA (9931)" /B cmd /c ""%LLAMA_BIN%" -m "%MODEL_PATH%" --host 127.0.0.1 --port %LLAMA_PORT% !LLAMA_HW_ARGS! > "%~dp0tavivo_llama.log" 2>&1"
    )
    timeout /t 2 /nobreak >nul
    tasklist /FI "IMAGENAME eq llama-server.exe" 2>nul | find /I "llama-server.exe" >nul
    if errorlevel 1 (
        echo [AVISO] llama-server.exe nao permaneceu em execucao. Verifique tavivo_llama.log:
        if exist "%~dp0tavivo_llama.log" type "%~dp0tavivo_llama.log"
    )
)

echo [2/2] Iniciando Terminal Offline TaVivo na porta %WEB_PORT%...
echo.
echo   Acesse no navegador: http://127.0.0.1:%WEB_PORT%
echo   Para encerrar tudo, feche esta janela ou pressione Ctrl+C.
echo.

set "TAVIVO_LLAMA_PORT=%LLAMA_PORT%"
set "TAVIVO_WEB_PORT=%WEB_PORT%"
set "TAVIVO_OPEN_BROWSER=1"

"%PYTHON_BIN%" servidor_tavivo.py
if errorlevel 1 (
    echo.
    echo [ERRO] O servidor web encerrou com erro.
    pause
)

echo.
echo Encerrando Motor IA (porta %LLAMA_PORT%)...
taskkill /FI "WINDOWTITLE eq TaVivo Motor IA (9931)" /F >nul 2>&1
taskkill /IM llama-server.exe /F >nul 2>&1
endlocal

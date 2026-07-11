@echo off
title PRANA Launcher

start "PRANA Frontend" cmd /k "cd /d E:\UserBenchmark\projikt\PRANA\client && npm run dev"

start "PRANA Backend" cmd /k "cd /d E:\UserBenchmark\projikt\PRANA\server && call .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

start "PRANA ComfyUI" cmd /k "cd /d E:\UserBenchmark\projikt\ComfyUI_windows_portable && run_nvidia_gpu.bat"

echo PRANA services launched.
exit
@echo off
title BranchLite VCS Server
echo ===================================================
echo   BranchLite VCS - Developer Studio Server
echo ===================================================
echo.
echo Opening http://127.0.0.1:5000 in your browser...
start http://127.0.0.1:5000
echo.
echo Starting server... (Press Ctrl+C to stop)
python gui\server.py
pause

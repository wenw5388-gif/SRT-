@echo off
chcp 65001 >nul
python app.py
if errorlevel 1 (
 echo 启动失败：请安装 Python 3 并勾选 Add Python to PATH。
 pause
)

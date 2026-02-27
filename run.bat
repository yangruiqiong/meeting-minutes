@echo off
echo Installing dependencies (using Chinese mirror)...
python -m pip install sounddevice soundfile numpy openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
echo.
echo Starting app...
python "%~dp0main.py"
pause

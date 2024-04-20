@echo off
title Installing required files

echo Installing/Updating Python
"./python_3116.exe" /passive /quite


ECHO Installing required python packages via pip [any key to confirm, otherwise close cmd]
set /p keyreceived=
python -m pip install -r ../requirements.txt

#@echo off
chcp 65001 >nul

set BASEDIR=%~dp0

set /p SRC=<"%BASEDIR%From.txt"
set /p DEST=<"%BASEDIR%To.txt"

if "%SRC%"=="" (
	echo SRC is empty
	pause
	exit
)
if "%DEST%"=="" (
	echo DEST is empty
	pause
	exit
)

robocopy "%SRC%" "%DEST%" /MIR /R:0 /W:0 /UNICODE

echo Done!
Pause
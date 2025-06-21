@echo off
REM Alphabet of Powers Calculator Helper Batch File

REM Define the path to the Python executable and the script.
REM Adjust these if your project structure or Python location is different.

REM Option 1: Assuming Python is in PATH and script is run from project root
SET PYTHON_EXE=python
SET SCRIPT_PATH=-m aopl_python_impl.aop_calculator_cli

REM Option 2: Specify full path to Python in a virtual environment (if used consistently)
REM SET VENV_PATH=%~dp0venv
REM IF EXIST "%VENV_PATH%\Scripts\python.exe" (
REM    SET PYTHON_EXE="%VENV_PATH%\Scripts\python.exe"
REM ) ELSE (
REM    REM Fallback to system Python if venv not found at expected location
REM    SET PYTHON_EXE=python
REM )
REM SET SCRIPT_MODULE_PATH=aopl_python_impl.aop_calculator_cli
REM SET SCRIPT_PATH=-m %SCRIPT_MODULE_PATH%


REM Check if any arguments were passed (for a simple help message)
IF "%~1"=="" (
    ECHO Usage: aop "expression" [options]
    ECHO Example: aop "a*b+c" --base 10
    ECHO For help on options, type: aop --help
    GOTO :EOF
)

REM Execute the Python script with all passed arguments
ECHO Executing: %PYTHON_EXE% %SCRIPT_PATH% %*
%PYTHON_EXE% %SCRIPT_PATH% %*

:EOF

@echo off

REM Determine the directory where this script resides
REM   Note that %~dp0 expands the drive and path of the batch script.
FOR %%I IN ("%~dp0.") DO SET SCRIPT_DIR=%%~fI

REM Navigate up two levels to get the repo's root directory
CD /D "%SCRIPT_DIR%\..\.."
SET CUSTOM_REPO_DIR=%CD%

ECHO Repository directory is: %CUSTOM_REPO_DIR%.

REM Pass the repository root-level directory to the Docker VM.
docker run -it --rm -p 8889:8888 --name jupyter -v %CUSTOM_REPO_DIR%:/home/jovyan/work -d my-custom-jupyter start-notebook.py --NotebookApp.token='docker'
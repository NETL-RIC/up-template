@echo off
REM get-docker (GDT server version)

REM --- Configuration ---
set repo_url=https://github.com/GreenDelta/gdt-server
set repo_dir=gdt-server
set repo_file=Dockerfile

REM --- Script Logic ---

REM 1. Clone the repository
echo Cloning the repository
git clone --depth 1 "%repo_url%"
if errorlevel 1 (
    echo Error cloning repository. Exiting
    exit /b 1
)

REM 2. Copy the file
echo Copying file ...
copy "%repo_dir%\%repo_file%" "%repo_file%"
if errorlevel 1 (
    echo Error copying file. Exiting.
    REM Clean up the cloned repo
    rmdir /s /q "%repo_dir%"
    exit /b 1
)

echo File copied successfully to %repo_file%

REM 3. Delete the repo clone
echo Deleting the cloned repository
rmdir /s /q "%repo_dir%"
if errorlevel 1 (
    echo Error deleting the repository
)

echo Done.
exit /b 0
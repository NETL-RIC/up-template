@echo off

REM --- Configuration ---
set output_file=Dockerfile

REM --- Delete the output file if it exists ---
if exist "%output_file%" (
    echo Deleting existing file: %output_file%
    del /f /q "%output_file%"
)

REM The lines of text
set line1=FROM quay.io/jupyter/minimal-notebook
set line3=RUN pip install --no-cache-dir 'olca-ipc' && \%
set line4=  fix-permissions "${CONDA_DIR}" && \%
set line5=  fix-permissions "/home/${NB_USER}"
set line7=USER root
set line9=RUN apt-get update && apt-get install -y lmodern


REM Write the lines to the file
echo %line1% >> "%output_file%"
echo. >> "%output_file%"
echo %line3% >> "%output_file%"
echo %line4% >> "%output_file%"
echo %line5% >> "%output_file%"
echo. >> "%output_file%"
echo %line7% >> "%output_file%"
echo. >> "%output_file%"
echo %line9% >> "%output_file%"

echo Successfully wrote "%output_file%".

exit /b 0
@echo off
REM get-docker (Jupyter version)

REM --- Configuration ---
set output_file=Dockerfile

REM --- Delete the output file if it exists ---
if exist "%output_file%" (
    echo Deleting existing file: %output_file%
    del /f /q "%output_file%"
)

REM The lines of text
set "line1=FROM quay.io/jupyter/minimal-notebook"

set "line2=COPY requirements.txt ."
set "line3=USER root"
set "line4=RUN chown ${NB_USER} /home/${NB_USER}/requirements.txt"
set "line5=RUN apt-get update ^&^& apt-get install -y lmodern"

set "line6=USER ${NB_USER}"
set "line7=RUN pip install --no-cache-dir -r requirements.txt \%"
set "line8=  ^&^& fix-permissions "${CONDA_DIR}" \%"
set "line9=  ^&^& fix-permissions "/home/${NB_USER}""

REM Write the lines to the file
echo %line1% >> "%output_file%"
echo. >> "%output_file%"
echo %line2% >> "%output_file%"
echo %line3% >> "%output_file%"
echo %line4% >> "%output_file%"
echo %line5% >> "%output_file%"
echo. >> "%output_file%"
echo %line6% >> "%output_file%"
echo %line7% >> "%output_file%"
echo %line8% >> "%output_file%"
echo %line9% >> "%output_file%"

echo Successfully wrote "%output_file%".

exit /b 0
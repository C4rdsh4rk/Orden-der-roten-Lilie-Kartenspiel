@echo off

echo		                             ++.                            
echo		                           .####.                           
echo		                          .######.                          
echo		                         .########.                         
echo		                         +########+                         
echo		                        .##########.                        
echo		                        +###########                        
echo		                        ############                        
echo		                 .      .##########-      .                 
echo		            .#########-  ##########  -#########.            
echo		           +############-.########.-############+           
echo		          -###############-######-###############-          
echo		          +###############+-####--###############+          
echo		          .########-..+####-####.####+..-########.          
echo		           -######.     -###-##-###-     .######-           
echo		             .+###       .+#.##.##.       ###+.             
echo		                         ##########                         
echo		                         ##########                         
echo		                    +#+  .+#.##.#+.  +#+                    
echo		                  .+###++##-####-##++###+.                  
echo		                  .+######+-####.+######+.                  
echo		                    -###+. +####+ .+###-                    
echo		                           +####+                           
echo		                           .####.                           
echo		                            .##.  
echo "+========================================================================+";
echo "|  ___          _                  _                       _             |";
echo "| / _ \ _ __ __| | ___ _ __     __| | ___ _ __   _ __ ___ | |_ ___ _ __  |";
echo "|| | | | '__/ _` |/ _ \ '_ \   / _` |/ _ \ '__| | '__/ _ \| __/ _ \ '_ \ |";
echo "|| |_| | | | (_| |  __/ | | | | (_| |  __/ |    | | | (_) | ||  __/ | | ||";
echo "| \___/|_|_ \__,_|\___|_|_|_|  \__,_|\___|_|    |_|  \___/ \__\___|_| |_||";
echo "|| |   (_) (_) ___  | |/ /__ _ _ __| |_ ___ _ __  ___ _ __ (_) ___| |    |";
echo "|| |   | | | |/ _ \ | ' // _` | '__| __/ _ \ '_ \/ __| '_ \| |/ _ \ |    |";
echo "|| |___| | | |  __/ | . \ (_| | |  | ||  __/ | | \__ \ |_) | |  __/ |    |";
echo "||_____|_|_|_|\___| |_|\_\__,_|_| _ \__\___|_| |_|___/ .__/|_|\___|_|    |";
echo "|                  |_ _|_ __  ___| |_ __ _| | | ___ _|_|                 |";
echo "|                   | || '_ \/ __| __/ _` | | |/ _ \ '__|                |";
echo "|                   | || | | \__ \ || (_| | | |  __/ |                   |";
echo "|                  |___|_| |_|___/\__\__,_|_|_|\___|_|                   |";
echo "+========================================================================+";

set "arch="

:: Check if the PROCESSOR_ARCHITECTURE environment variable is present
if defined PROCESSOR_ARCHITECTURE (
    set "arch=%PROCESSOR_ARCHITECTURE%"
) else (
    :: Check if the PROCESSOR_ARCHITEW6432 environment variable is present
    if defined PROCESSOR_ARCHITEW6432 (
        set "arch=%PROCESSOR_ARCHITEW6432%"
    )
)

if /i "%arch%"=="AMD64" (
    echo System is 64-bit
	set DOWNLOAD_URL=https://www.python.org/ftp/python/3.12.1/python-3.12.1-embed-amd64.zip
	
) else (
    echo System is 32-bit
	set DOWNLOAD_URL=https://www.python.org/ftp/python/3.12.1/python-3.12.1-embed-win32.zip
)

::Python
set PYTHON_VERSION=3.12.1
:: Create the extraction folder
mkdir \src\Python
set EXTRACT_PATH=.\src\Python

:: Download the embedded Python zip file
echo Downloading Python %PYTHON_VERSION%...
powershell -command "Invoke-WebRequest '%DOWNLOAD_URL%' -OutFile '\src\python-embed.zip' "

:: Extract the contents of the zip file
powershell -command "Expand-Archive -Path '\src\python-embed.zip' -DestinationPath '%EXTRACT_PATH%'"

echo Embedded Python Download Complete!

set PYTHON=\src\Python\python.exe

:: getPIP
powershell -command "cd .\src\; curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py"
echo getPIP Download Complete!

::installPIP
.\src\Python\python.exe .\src\get-pip.py
    echo getPIP Installed!
::powershell -command "cd .\src\;python.exe get-pip.py"

:: REQ
powershell -command "cd .\src\Python\Scripts; pip.exe freeze > ..\requirements.txt"
powershell -command "cd .\src\Python\Scripts; pip.exe install -r ..\requirements.txt"
echo Requirements Install Complete!

:: Clean UP
::powershell -command "cd .\src\Python\; Remove-item python312.zip; Remove-item python-embed.zip; Remove-item get-pip.py"
::echo Installation cleaned up!

:: LOG Folder
::mkdir logs
::echo Logs Folder Created!
echo Setup Complete!
echo GLHF!

:End
pause
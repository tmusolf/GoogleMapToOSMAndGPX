@echo off
echo.
echo Converts google my maps into OSMAnd GPX files.
echo.
echo Reads in a supplied input file containing lines of text.
echo Each line represents one GMap that you want translated.
echo Each line has the following format.  Three tokens separated by commas:
echo   (Directory Path),(MapID),(parms)
echo   (Directory Path): Required, the path\directory name where you want the resulting GPX files
echo   (MapID): Required, the GMap ID obatined from the map URL. It's the string of characters between "mid=" and the first "&" character after that.
echo   (parms): Options command line parms for the GoogleMapToOSMAndGPX utility
echo.
echo   For example:
echo     F:\TestMaps\LayersTracksWayPts,ZZZZXXXXZZZZ_xxxxxxxxxxxx, -t 80 -l
echo.
echo If no parameters are supplied batch file will ask for filename and use fixed parameters
echo You can also invoke the batch file with 2 parameters
echo     GoogleMapToOSMAndGPX.bat "(filename)" "(parms)"
echo The optional 2nd parameter (parms) is a string of GoogleMapToOSMAndGPX parms to replace default ones.  Double quotes required.
echo.
setlocal EnableDelayedExpansion
set PROGRAM="U:\Projects\Computer Projects\PC Software\GoogleMapToOSMAndGPX\GoogleMapToOSMAndGPX.py"
:: first check if the input file is specified on the command line
if "%~1" == "" (
	echo.
	set /p infile= "  Enter path to input file: "
) else (
	set infile="%~1"
)
:: we now have an infile either specified on the command line or through user input
:: Lets see if file exists
if exist %infile% goto execute 
echo.
echo ***Input file not found: %infile% ***
echo.
goto end
	
:execute
:: Get the current date in YYYY-MM-DD format
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"

set "CurrentDate=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%"
echo Current date: %CurrentDate% Input file: %infile%
set /a count=0
set /a errorCount=0

:: Read the file containing infile and outfile names
:: Tokens split on comma, first token put in %%A and second in %%B, optional 3rd is %%C
:: Lots of batch file crap having to do with file names with spaces
:: and how they are quoted.  On input from cmd line use double quotes
:: around paths that have spaces.  Single quotes won't work.  Here in the batch
:: file I found a reference that said use single quotes and type command
:: to get around these issues.
for /f "eol=# tokens=1,2,3 delims=," %%A in ('type %infile%') do (
	set /a count+=1
	set "outputfolder=%%A-%CurrentDate%"
	echo =========================================================================================
	echo Processing map #!count!
	if "%~2" NEQ "" (
		:: Command line specified parms overide defaults and those specified in input file
		echo %~2
		py %PROGRAM% %%B "!outputfolder!" %~2
	) else if "%%C" NEQ "" (
		:: If there is a third comma separated token from input file use it to override default parameters
		py %PROGRAM% %%B "!outputfolder!" %%C
	) else (
		:: Use the default parameters
		py %PROGRAM% %%B "!outputfolder!" -t 80 -w 12
	)
	if !ERRORLEVEL! NEQ 0 (
		set /a errorCount+=1
	)
	echo.
)
echo Processed %count% maps. Error count: %errorCount%
echo.
:end
endlocal
pause


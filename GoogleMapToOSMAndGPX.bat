 @echo off
echo.
echo Converts google my maps into OSMAnd GPX files.
:: Reads in a supplied file containing a google map name and its corresponding ID value (mid=xxxx)
:: The google map name does not have to be the actual name, it is the string you want used for the folder.
::
:: If no parameters are supplied batch file will ask for filename and use fixed parameters
:: You can also invoke the batch file with 2 parameters
::     GoogleMapToOSMAndGPX <filename> <parms>
:: The optional 2nd parameter is a string of program parms to replace default ones - used for testing
setlocal EnableDelayedExpansion
set PROGRAM="U:\Projects\Computer Projects\PC Software\GoogleMapToOSMAndGPX\GoogleMapToOSMAndGPX.py"
:: first check if the input file is specified on the command line
if "%~1" == "" (
	echo.
	set /p infile= "  Enter path to file with comma separated pairs <name>,<mapID> values: "
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
:: Tokens split on comma, first token put in %%A and second in %%B
:: Lots of batch file crap having to do with file names with spaces
:: and how they are quoted.  On input from cmd line use double quotes
:: around paths that have spaces.  Single quotes won't work.  Here in the batch
:: file I found a reference that said use single quotes and type command
:: to get around these issues.
for /f "eol=# tokens=1,2 delims=," %%A in ('type %infile%') do (
	set /a count+=1
	set "outputfolder=%%A-%CurrentDate%"
	echo =========================================================================================
	echo Processing map #!count!
	if "%~2" == "" (
		py %PROGRAM% %%B "!outputfolder!" -t 80 -w 12
	) else (
		py %PROGRAM% %%B "!outputfolder!" %~2
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


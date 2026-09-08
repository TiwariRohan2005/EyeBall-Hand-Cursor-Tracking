@echo off
echo ==============================================
echo   TrueEyeball Automated Test Suite
echo ==============================================

if exist venv\Scripts\activate (
    echo Activating virtual environment...
    call venv\Scripts\activate
) else if exist .venv\Scripts\activate (
    echo Activating virtual environment...
    call .venv\Scripts\activate
) else (
    echo Virtual environment not found in venv\ or .venv\
)

echo.
echo Running comprehensive test suite...
python -m pytest -x -vv --timeout=60 --tb=short

if %ERRORLEVEL% neq 0 (
    echo.
    echo Tests failed or hung! Please check the output above.
    exit /b %ERRORLEVEL%
)

echo.
echo All tests completed successfully.

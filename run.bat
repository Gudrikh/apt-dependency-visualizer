@echo off
setlocal
pushd "%~dp0" || exit /b 1
python -m src.main %*
set "result=%errorlevel%"
popd
exit /b %result%

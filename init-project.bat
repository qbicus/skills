@echo off
setlocal

REM Initializes or updates the current repository with the shared AI framework project files.
REM Usage:
REM   %USERPROFILE%\.ai\init-project.bat
REM   %USERPROFILE%\.ai\init-project.bat --type dotnet
REM   %USERPROFILE%\.ai\init-project.bat --type go
REM   %USERPROFILE%\.ai\init-project.bat --type nextjs
REM   %USERPROFILE%\.ai\init-project.bat --type python
REM   %USERPROFILE%\.ai\init-project.bat --type vb-migration --with-codex-hooks
REM   %USERPROFILE%\.ai\init-project.bat --type dotnet --with-graphify-claude
REM   %USERPROFILE%\.ai\init-project.bat --type dotnet --with-codex-hooks --with-graphify-claude
REM   %USERPROFILE%\.ai\init-project.bat --dry-run
REM   %USERPROFILE%\.ai\init-project.bat --type dotnet --action update --non-interactive
REM   %USERPROFILE%\.ai\init-project.bat --type dotnet --action reinit --non-interactive

set "FRAMEWORK_ROOT=%~dp0"
set "REPO_INIT=%FRAMEWORK_ROOT%scripts\repo-init.py"

if not exist "%REPO_INIT%" (
  echo Could not find repo-init.py at: %REPO_INIT%
  exit /b 1
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python "%REPO_INIT%" %*
  exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py "%REPO_INIT%" %*
  exit /b %ERRORLEVEL%
)

echo Python was not found. Install Python or make sure python/py is available in PATH.
exit /b 1
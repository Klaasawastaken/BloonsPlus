@echo off
setlocal
rem One-click setup of the Bloons+ virtual machine. Needs administrator rights (App Sandbox runs VMs
rem through the Windows Host Compute Service), so it re-launches itself elevated.
net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

set "APPSANDBOX_DIR=%USERPROFILE%\Downloads\AppSandbox"
set "ROOT=%~dp0.."

rem App Sandbox needs the Virtual Machine Platform feature (the one WSL2 uses). Enabling it needs a reboot.
powershell -NoProfile -Command "if ((Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State -ne 'Enabled') { exit 1 }"
if errorlevel 1 (
  echo Turning on Virtual Machine Platform...
  dism /online /Enable-Feature /FeatureName:VirtualMachinePlatform /All /NoRestart
  echo.
  echo Restart the PC, then run this file again to create the VM.
  pause
  exit /b
)

rem Start the App Sandbox daemon unless it is already running.
powershell -NoProfile -Command "if (-not (Get-Process AppSandbox -ErrorAction SilentlyContinue)) { Start-Process -FilePath '%APPSANDBOX_DIR%\AppSandbox.exe'; Start-Sleep -Seconds 5 }"

echo Building the VM. Progress is written to "%~dp0setup-vm.log" (this window can stay open).
"%ROOT%\.venv\Scripts\python.exe" -u "%~dp0setup-vm.py" > "%~dp0setup-vm.log" 2>&1
type "%~dp0setup-vm.log"
echo.
pause

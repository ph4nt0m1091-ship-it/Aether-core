$ErrorActionPreference = "Stop"

$ProjectPath = "C:\Users\juju and bobby\Documents\Aether\Aether-Core"

$PythonwPath = "C:\Users\juju and bobby\AppData\Local\Programs\Python\Python311\pythonw.exe"

$RuntimeControl = Join-Path `
    $ProjectPath `
    "runtime_control.py"

$StartupFolder = (
    [Environment]::GetFolderPath(
        "Startup"
    )
)

$LauncherPath = Join-Path `
    $StartupFolder `
    "Aether Background Runtime.cmd"


# ---------------------------------
# VERIFY PYTHON
# ---------------------------------

if (-not (Test-Path $PythonwPath)) {

    throw (
        "pythonw.exe not found: " +
        $PythonwPath
    )
}


# ---------------------------------
# VERIFY RUNTIME CONTROL
# ---------------------------------

if (-not (Test-Path $RuntimeControl)) {

    throw (
        "runtime_control.py not found: " +
        $RuntimeControl
    )
}


# ---------------------------------
# VERIFY STARTUP FOLDER
# ---------------------------------

if (-not (Test-Path $StartupFolder)) {

    throw (
        "Windows Startup folder " +
        "could not be found."
    )
}


# ---------------------------------
# BUILD STARTUP LAUNCHER
# ---------------------------------

$Launcher = @"
@echo off
cd /d "$ProjectPath"
"$PythonwPath" "$RuntimeControl" start
"@


# ---------------------------------
# INSTALL
# ---------------------------------

Set-Content `
    -Path $LauncherPath `
    -Value $Launcher `
    -Encoding ASCII


# ---------------------------------
# CONFIRM
# ---------------------------------

Write-Host ""
Write-Host "Aether Windows auto-start installed."
Write-Host ""
Write-Host "Startup launcher:"
Write-Host $LauncherPath
Write-Host ""
Write-Host (
    "Aether will start its background " +
    "runtime when you sign in to Windows."
)
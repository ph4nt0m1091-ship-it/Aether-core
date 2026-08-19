$ErrorActionPreference = "Stop"

$StartupFolder = (
    [Environment]::GetFolderPath(
        "Startup"
    )
)

$LauncherPath = Join-Path `
    $StartupFolder `
    "Aether Background Runtime.cmd"


# ---------------------------------
# REMOVE STARTUP LAUNCHER
# ---------------------------------

if (Test-Path $LauncherPath) {

    Remove-Item `
        -Path $LauncherPath `
        -Force

    Write-Host ""
    Write-Host (
        "Aether Windows auto-start removed."
    )

}
else {

    Write-Host ""
    Write-Host (
        "Aether auto-start is not installed."
    )
}
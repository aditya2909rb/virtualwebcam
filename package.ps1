$ErrorActionPreference = 'Stop'

$releaseDir = Join-Path $PSScriptRoot 'release'
$packagePath = Join-Path $releaseDir 'VirtualWebCamera-package.zip'

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

if (-not (Test-Path (Join-Path $PSScriptRoot 'dist\VirtualWebCamera.exe'))) {
    throw 'Build dist\VirtualWebCamera.exe first by running .\build.ps1'
}

if (Test-Path $packagePath) {
    Remove-Item $packagePath -Force
}

$packageItems = @(
    (Join-Path $PSScriptRoot 'dist\VirtualWebCamera.exe')
    (Join-Path $PSScriptRoot 'README.md')
)

Compress-Archive -Path $packageItems -DestinationPath $packagePath

Write-Host "Package created at $packagePath"
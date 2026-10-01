# Apaga as zonas, missões e NPCs já gravados e deixa o Forever vazio.
# O catálogo de zonas continua, todas pendentes. O cache de download continua.
#
#   .\reset.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python não está no PATH."
    exit 1
}

python .\run.py reset
exit $LASTEXITCODE

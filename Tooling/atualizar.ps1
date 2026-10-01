# Atualiza os dados do Forever.
# Sem argumentos, mostra o que já foi feito e o que falta.
#
#   .\atualizar.ps1
#   .\atualizar.ps1 list
#   .\atualizar.ps1 list pendente
#   .\atualizar.ps1 zones
#   .\atualizar.ps1 fetch eastern-kingdoms/westfall
#   .\atualizar.ps1 update eastern-kingdoms/westfall
#   .\atualizar.ps1 update eastern-kingdoms/westfall --dry-run
#   .\atualizar.ps1 build eastern-kingdoms/elwynn-forest
#   .\atualizar.ps1 seed eastern-kingdoms/westfall --refresh
#   .\atualizar.ps1 seed classes/paladin --delay=15
#   .\reset.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python não está no PATH."
    exit 1
}

if ($args.Count -eq 0) {
    python .\run.py status
    exit $LASTEXITCODE
}

python .\run.py @args
exit $LASTEXITCODE

[CmdletBinding()]
param([switch]$Development, [switch]$VerifyOnly)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$cloneRoot = $PSScriptRoot
$pythonExe = Join-Path $cloneRoot '.venv/Scripts/python.exe'

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Comando falhou (exit $LASTEXITCODE): $Executable $($Arguments -join ' ')" }
}

Push-Location $cloneRoot
try {
    if (-not $VerifyOnly) {
        $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
        if (-not $uvCommand) {
            throw 'Instale uv seguindo https://docs.astral.sh/uv/getting-started/installation/ e reabra o terminal.'
        }
        $syncArgs = @('sync', '--locked', '--python', '3.13')
        if (-not $Development) { $syncArgs += '--no-dev' }
        Invoke-Checked $uvCommand.Source $syncArgs
    }
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Ambiente ausente. Execute instalar.ps1 sem -VerifyOnly.' }
    New-Item -ItemType Directory -Path '.machine/verification' -Force | Out-Null
    & $pythonExe -m article_machine --help > '.machine/verification/cli.txt'
    if ($LASTEXITCODE -ne 0) { throw 'CLI falhou. Consulte .machine/verification/cli.txt.' }
    & $pythonExe -m article_machine machine audit --workspace-root . --strict > '.machine/verification/auditoria.json'
    if ($LASTEXITCODE -ne 0) { throw 'Auditoria bloqueou. Consulte .machine/verification/auditoria.json.' }
    Write-Host 'PASS: núcleo instalado e auditoria operacional aprovada.'
    Write-Host 'Abra GEMINI.md e docs/portugues/guia_de_uso.md no Antigravity.'
    if ($Development) { Write-Host 'Testes: .\.venv\Scripts\python.exe -m pytest tests/' }
}
finally { Pop-Location }

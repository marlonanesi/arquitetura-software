# Verificações de arquitetura como código: modelo C4, ADRs e diagramas (versão PowerShell do verificar.sh).
# É o que o CI roda em cada pull request. Precisa de Docker e Python 3.
# Uso, na pasta do lab:  .\scripts\verificar.ps1
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = '1'   # acentos corretos na saída do validador de ADRs
Set-Location (Join-Path $PSScriptRoot '..')

$montagem = "$((Get-Location).Path):/usr/local/structurizr"
function Structurizr { docker run --rm -v $montagem structurizr/structurizr @args }

Write-Host '== 1. Sintaxe do modelo (validate)'
Structurizr validate -w workspace.dsl
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host '== 2. Qualidade do modelo (inspect): relacionamentos sem tecnologia, falta de documentação'
$saida = Structurizr inspect -w workspace.dsl 2>&1 | ForEach-Object { "$_" }
$pendencias = $saida | Where-Object { $_ -match '^(ERROR|WARNING)' }
if ($pendencias) {
    $pendencias | ForEach-Object { Write-Host $_ }
    Write-Host 'O modelo tem pendências (acima).'
    exit 1
}
Write-Host 'sem pendências'

Write-Host '== 3. ADRs (formato, status e substituições)'
$py = $null
foreach ($c in 'python3', 'python') {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        & $c -c 'import sys' 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $py = $c; break }
    }
}
if (-not $py) { Write-Host 'Python 3 nao encontrado'; exit 1 }
& $py scripts/verificar_adrs.py adrs
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host '== 4. Diagramas gerados a partir do modelo (Mermaid)'
Structurizr export -w workspace.dsl -f mermaid -o diagramas 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { exit 1 }
$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($mmd in Get-ChildItem diagramas -Filter *.mmd) {
    Write-Host "  diagramas/$($mmd.Name)"
    $nome = $mmd.BaseName -replace '^structurizr-', ''
    # Cada diagrama também vira uma página Markdown, que o GitHub renderiza (e que aparece no diff do PR).
    $cerca = '```'
    $texto = "# Diagrama: $nome`n`n> Gerado a partir de workspace.dsl. Não edite à mão.`n`n${cerca}mermaid`n" +
             [System.IO.File]::ReadAllText($mmd.FullName) + "${cerca}`n"
    [System.IO.File]::WriteAllText((Join-Path (Get-Location).Path "diagramas/$nome.md"), $texto, $utf8)
}
Remove-Item diagramas/*.mmd -Force
Write-Host '  diagramas/*.md (renderizáveis no GitHub)'
exit 0

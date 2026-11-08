$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv-server\Scripts\python.exe'
if (!(Test-Path $python)) { python -m venv .venv-server }
& $python -m pip install -r requirements-server.txt
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar o servidor.' }
Start-Process 'http://127.0.0.1:5000'
& $python run_server.py

# Install ppt-course-notes to the Codex skill directory. Existing install is not overwritten.
$ErrorActionPreference = 'Stop'
$name = 'ppt-course-notes'
$source = Join-Path $PSScriptRoot $name
$targetRoot = Join-Path $HOME '.codex\skills'
$target = Join-Path $targetRoot $name
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) { throw 'SKILL.md not found in nested skill folder' }
if (Test-Path -LiteralPath $target) { throw "Already installed: $target (backup/remove old version first)" }
New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
Copy-Item -LiteralPath $source -Destination $targetRoot -Recurse -Force
Write-Host "Installed: $target"
Write-Host 'Start a new Codex conversation.'

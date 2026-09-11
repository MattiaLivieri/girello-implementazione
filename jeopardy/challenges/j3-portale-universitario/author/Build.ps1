param(
    [string]$DockerContext = "desktop-linux"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-J3Docker {
    param([string[]]$Arguments)
    & docker --context $DockerContext @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Comando Docker J3 non riuscito: $($Arguments[0])"
    }
}

function Write-J3Json {
    param([string]$Path, [object]$Value)
    $json = $Value | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText($Path, $json + "`n", [Text.UTF8Encoding]::new($false))
}

$sourceRoot = Split-Path $PSScriptRoot -Parent
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../../../.."))
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
    throw "Eseguire lo script dalla copia della repository."
}

Push-Location $repoRoot
try {
    & git check-ignore --quiet -- artifacts/j3/private/scenario.json
    if ($LASTEXITCODE -ne 0) {
        throw "artifacts/j3/private/scenario.json deve essere ignorato da Git."
    }
    $tracked = @(& git ls-files -- artifacts/j3)
    if ($LASTEXITCODE -ne 0 -or $tracked.Count -ne 0) {
        throw "Controllare Git: artifacts/j3 deve essere priva di file tracciati."
    }

    $server = ((Invoke-J3Docker -Arguments @("version", "--format", "{{.Server.Os}}/{{.Server.Arch}}")) -join "").Trim()
    if ($server -ne "linux/amd64") {
        throw "Questa build richiede il motore Docker Linux amd64. Rilevato: $server"
    }

    $artifactRoot = Join-Path $repoRoot "artifacts/j3"
    $privateDir = Join-Path $artifactRoot "private"
    $buildDir = Join-Path $artifactRoot "build"
    New-Item -ItemType Directory -Force -Path $privateDir, $buildDir | Out-Null

    $scenarioPath = Join-Path $privateDir "scenario.json"
    if (Test-Path -LiteralPath $scenarioPath) {
        $scenario = Get-Content -Raw -LiteralPath $scenarioPath | ConvertFrom-Json
        if ($scenario.flag -cnotmatch '^CRCTF\{[a-f0-9]{32}\}$') {
            throw "Configurazione privata J3 non valida; file conservato."
        }
    } else {
        $bytes = New-Object byte[] 16
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
        $token = ([BitConverter]::ToString($bytes)).Replace("-", "").ToLowerInvariant()
        Write-J3Json -Path $scenarioPath -Value @{ flag = "CRCTF{$token}" }
    }

    $lockPath = Join-Path $privateDir "build-lock.json"
    if (Test-Path -LiteralPath $lockPath) {
        $lock = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json
        $baseImage = [string]$lock.base_image
        if ($baseImage -cnotmatch '^python@sha256:[a-f0-9]{64}$') {
            throw "Digest della base J3 non valido; lock conservato."
        }
        Invoke-J3Docker -Arguments @("pull", "--platform", "linux/amd64", $baseImage)
    } else {
        $baseTag = "python:3.13-slim-bookworm"
        Invoke-J3Docker -Arguments @("pull", "--platform", "linux/amd64", $baseTag)
        $baseImage = ((Invoke-J3Docker -Arguments @("image", "inspect", $baseTag, "--format", "{{index .RepoDigests 0}}")) -join "").Trim()
        if ($baseImage -cnotmatch '^python@sha256:[a-f0-9]{64}$') {
            throw "Impossibile identificare il digest dell'immagine Python."
        }
        Write-J3Json -Path $lockPath -Value @{
            base_image = $baseImage
            source_tag = $baseTag
            platform = "linux/amd64"
        }
    }

    $contextDir = Join-Path $buildDir ("context-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $contextDir | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $contextDir "author") | Out-Null
    Copy-Item -LiteralPath (Join-Path $sourceRoot "app") -Destination $contextDir -Recurse
    foreach ($name in @("Dockerfile", "requirements.txt")) {
        Copy-Item -LiteralPath (Join-Path $sourceRoot $name) -Destination $contextDir
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "test_portal.py") -Destination (Join-Path $contextDir "author")
    Copy-Item -LiteralPath $scenarioPath -Destination (Join-Path $contextDir "scenario.json")

    $imageName = "girello/j3-portale-universitario:1.0"
    Invoke-J3Docker -Arguments @(
        "build", "--platform", "linux/amd64", "--progress", "plain",
        "--build-arg", "BASE_IMAGE=$baseImage", "--tag", $imageName, $contextDir
    )

    $imageJson = (Invoke-J3Docker -Arguments @("image", "inspect", $imageName)) -join "`n"
    $imageInfo = @($imageJson | ConvertFrom-Json)[0]
    if ($imageInfo.Os -ne "linux" -or $imageInfo.Architecture -ne "amd64" -or
        $imageInfo.Config.User -ne "10001:10001") {
        throw "Configurazione dell'immagine finale inattesa."
    }

    $hashes = @{}
    Get-ChildItem -LiteralPath $sourceRoot -Recurse -File |
        Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' } |
        ForEach-Object {
            $relative = $_.FullName.Substring($sourceRoot.Length + 1).Replace("\", "/")
            $hashes[$relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    Write-J3Json -Path (Join-Path $buildDir "build-report.json") -Value @{
        created_utc = [DateTime]::UtcNow.ToString("o")
        image = $imageName
        image_id = $imageInfo.Id
        base_image = $baseImage
        platform = "linux/amd64"
        user = $imageInfo.Config.User
        source_sha256 = $hashes
        automated_tests = "Superati nello stage checked, oppure riutilizzati dalla cache dello stesso stage."
        runtime_validation = "DA ESEGUIRE: browser, binding, avvio offline e reset."
    }
    Write-Output "Build J3 completata; controlli automatici superati."
    Write-Output "Immagine: $imageName"
    Write-Output "Image ID: $($imageInfo.Id)"
    Write-Output "Rapporto: artifacts/j3/build/build-report.json"
    Write-Output "Flag privata conservata; contenuto non stampato."
} finally {
    Pop-Location
}
[CmdletBinding()]
param(
    [string]$ServerIp = "72.56.232.208",
    [int]$SshPort = 2222,
    [string]$SshUser = "deploy",
    [string]$DeployDir = "/opt/lms",
    [string]$DockerImage = "fapepa/lms-project:latest"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvPath = Join-Path $ProjectRoot ".env"
$ComposePath = Join-Path $ProjectRoot "docker-compose.yml"
$NginxPath = Join-Path $ProjectRoot "nginx\default.conf"

if (-not (Test-Path $EnvPath)) {
    throw "The .env file was not found in the project root."
}

$TempEnv = Join-Path ([System.IO.Path]::GetTempPath()) "lms-server-$([guid]::NewGuid()).env"

try {
    $EnvLines = Get-Content $EnvPath | Where-Object {
        $_ -notmatch '^\s*(DOCKER_IMAGE|APP_VERSION)='
    }

    $EnvLines += "DOCKER_IMAGE=$DockerImage"
    Set-Content -Path $TempEnv -Value $EnvLines -Encoding ASCII

    $SshOptions = @(
        "-p", "$SshPort",
        "-o", "IPQoS=none",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=30",
        "-o", "ServerAliveInterval=15"
    )

    $ScpOptions = @(
        "-P", "$SshPort",
        "-o", "IPQoS=none",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=30"
    )

    $Remote = "$SshUser@$ServerIp"

    & ssh @SshOptions $Remote "mkdir -p '$DeployDir/nginx'"
    if ($LASTEXITCODE -ne 0) {
        throw "SSH connection failed."
    }

    & scp @ScpOptions $ComposePath "${Remote}:$DeployDir/docker-compose.yml"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload docker-compose.yml."
    }

    & scp @ScpOptions $NginxPath "${Remote}:$DeployDir/nginx/default.conf"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload nginx configuration."
    }

    & scp @ScpOptions $TempEnv "${Remote}:$DeployDir/.env"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload .env."
    }

    $RemoteCommand = @"
set -e
chmod 600 '$DeployDir/.env'
cd '$DeployDir'
docker compose --profile production pull
docker compose --profile production up -d --no-build --remove-orphans
docker compose --profile production ps
"@

    & ssh @SshOptions $Remote $RemoteCommand

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start Docker containers."
    }

    Write-Host "Server bootstrap completed successfully."
}
finally {
    Remove-Item $TempEnv -Force -ErrorAction SilentlyContinue
}

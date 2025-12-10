# setup.ps1
# PowerShell setup script for n8n on Windows (import workflows only)

# 1. Load Environment Variables from .env
if (Test-Path .env) {
    Get-Content .env |
        Where-Object { $_ -match '=' -and -not ($_ -match '^#') } |
        ForEach-Object {
            $key, $value = $_.Split('=', 2)
            [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
        }
}

$ContainerN8n = "n8n"
$ContainerDb  = "postgres"

# Fallback to defaults if env vars are missing
$DbUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "n8n" }
$DbName = if ($env:POSTGRES_DB)   { $env:POSTGRES_DB }   else { "n8n" }

Write-Host "============================================="
Write-Host "      n8n Standard Delivery Setup Script     "
Write-Host "         (Import Workflows Only)             "
Write-Host "============================================="

# 2. Check if containers are running
$n8nStatus = docker ps -q -f name=$ContainerN8n
if (-not $n8nStatus) {
    Write-Error "n8n container is not running. Please run 'docker-compose up -d' first."
    exit 1
}

$dbStatus = docker ps -q -f name=$ContainerDb
if (-not $dbStatus) {
    Write-Error "Postgres container is not running. Please run 'docker-compose up -d' first."
    exit 1
}

# 3. (Optional) Ask for User Email – ใช้เพื่อพยายามดึง userId จาก DB
$UserEmail = Read-Host "Enter the email address for the n8n Owner account (or leave blank to skip userId)"
$UserId = $null

# Helper to execute SQL in Postgres container
function Get-UserId {
    param($email)

    if ([string]::IsNullOrWhiteSpace($email)) {
        return $null
    }

    # Basic sanitization to avoid breaking SQL
    $safeEmail = $email -replace "'", "''"

    # หมายเหตุ: ตาราง "user" เป็น reserved word ต้องใส่ double-quote
    $sql = "SELECT id FROM `"`"user`"`" WHERE email = '$safeEmail' LIMIT 1;"

    $id = $sql | docker exec -i $ContainerDb psql -U $DbUser -d $DbName -At 2>$null

    if (-not $id) { return $null }

    return $id.Trim()
}

if (-not [string]::IsNullOrWhiteSpace($UserEmail)) {
    Write-Host "Checking for user in database..."
    $UserId = Get-UserId -email $UserEmail

    # Validate UUID (n8n ใช้ UUID v4)
    if ($UserId -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') {
        Write-Warning "User ID from database is not a valid UUID. Ignoring userId."
        $UserId = $null
    }
}

if ($UserId) {
    Write-Host "Found User ID: $UserId"
} else {
    Write-Host "No valid userId will be used. Workflows will be imported without --userId flag."
    Write-Host "Make sure you already have an Owner user created in n8n."
}

# 4. Import Workflows
Write-Host "Importing workflows from /workflows folder..."

if ($UserId) {
    docker exec -u node $ContainerN8n n8n import:workflow `
        --separate `
        --input /workflows `
        --userId "$UserId"
} else {
    docker exec -u node $ContainerN8n n8n import:workflow `
        --separate `
        --input /workflows
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Workflow import failed. Please check the docker logs for the n8n container."
    exit 1
}

Write-Host "============================================="
Write-Host "      Setup Complete! Workflows Imported.    "
Write-Host "============================================="
Write-Host "You can now log in at http://localhost:5678"

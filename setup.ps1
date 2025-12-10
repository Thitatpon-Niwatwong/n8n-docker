# setup.ps1
# PowerShell setup script for n8n on Windows

# 1. Load Environment Variables from .env
if (Test-Path .env) {
    Get-Content .env | Where-Object { $_ -match '=' -and -not ($_ -match '^#') } | ForEach-Object {
        $key, $value = $_.Split('=', 2)
        [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
    }
}

$ContainerN8n = "n8n"
$ContainerDb = "postgres"
# Fallback to defaults if env vars are missing
$DbUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "n8n" }
$DbName = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "n8n" }

Write-Host "============================================="
Write-Host "      n8n Standard Delivery Setup Script     "
Write-Host "============================================="

# 2. Check if containers are running
$n8nStatus = docker ps -q -f name=$ContainerN8n
if (-not $n8nStatus) {
    Write-Error "n8n container is not running. Please run 'docker-compose up -d' first."
    exit 1
}

# 3. Ask for User Email
$UserEmail = Read-Host "Enter the email address for the n8n Owner account"
if ([string]::IsNullOrWhiteSpace($UserEmail)) {
    Write-Error "Email cannot be empty."
    exit 1
}

# Helper to execute SQL in Postgres container
function Get-UserId {
    param($email)
    $sql = "SELECT id FROM `"user`" WHERE email = '$email';"
    # We use basic string manipulation to avoid creating temp files inside container if possible, 
    # but docker exec -i is reliable.
    $id = $sql | docker exec -i $ContainerDb psql -U $DbUser -d $DbName -t 2>$null
    return $id.Trim()
}

Write-Host "Checking for user in database..."
$UserId = Get-UserId -email $UserEmail

# Validate UUID
if ($UserId -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') {
    $UserId = $null
}

if (-not $UserId) {
    Write-Host "User '$UserEmail' not found."
    $create = Read-Host "Do you want to create a new Admin user with this email? (y/n)"
    if ($create -eq 'y') {
        $UserPass = Read-Host "Enter Password" -AsSecureString
        $UserPassPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($UserPass))

        Write-Host "Attempting to create user via CLI..."
        
        # Try modern command
        docker exec -u node $ContainerN8n n8n user:management:user:create --email "$UserEmail" --password "$UserPassPlain" --firstName "Admin" --lastName "User" --role global:owner 2>$null
        if ($LASTEXITCODE -ne 0) {
            # Try legacy command
            docker exec -u node $ContainerN8n n8n user:create --email "$UserEmail" --password "$UserPassPlain" --firstName "Admin" --lastName "User" --role global:owner 2>$null
        }

        # Check again
        $UserId = Get-UserId -email $UserEmail
        if ($UserId -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') {
            Write-Error "Failed to create user or retrieve ID. Please create manually at http://localhost:5678"
            exit 1
        }
    }
    else {
        Write-Error "Aborted."
        exit 1
    }
}

Write-Host "Found User ID: $UserId"

# 4. Import Workflows
Write-Host "Importing workflows from /workflows folder..."
docker exec -u node $ContainerN8n n8n import:workflow --input /workflows --userId "$UserId"

Write-Host "============================================="
Write-Host "      Setup Complete! Workflows Imported.    "
Write-Host "============================================="
Write-Host "You can now log in at http://localhost:5678"

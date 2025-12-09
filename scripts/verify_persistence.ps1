# verify_persistence.ps1
# Simplified script to verify that n8n writes edited workflows to the mounted ./workflows directory.
# It waits a few seconds for the n8n API to be ready, creates a dummy workflow via the REST API,
# updates it, and checks that the corresponding JSON file on disk reflects the change.

$baseUrl = "http://localhost:5678"
$workflowName = "verify_persistence_dummy"
$workflowFile = Join-Path (Resolve-Path "./workflows") "$workflowName.json"

# Wait for n8n API to be ready (simple retry loop)
$maxAttempts = 10
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $resp = Invoke-WebRequest -Uri "$baseUrl/rest/workflows" -Method GET -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { break }
    }
    catch { }
    Start-Sleep -Seconds 3
    $attempt++
}
if ($attempt -ge $maxAttempts) {
    Write-Error "n8n API not reachable after waiting"
    exit 1
}

# 1. Create a simple workflow via API (no auth assumed)
$payload = @{
    name        = $workflowName
    nodes       = @()
    connections = @{}
    active      = $false
    settings    = @{}
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Method POST -Uri "$baseUrl/rest/workflows" -Body $payload -ContentType "application/json"
}
catch {
    Write-Error "Failed to create workflow via API: $_"
    exit 1
}
if (-not $response.id) {
    Write-Error "API did not return workflow ID"
    exit 1
}
$workflowId = $response.id

# 2. Update the workflow name via API
$payloadUpdate = @{ name = "${workflowName}-updated" } | ConvertTo-Json
try {
    Invoke-RestMethod -Method PATCH -Uri "$baseUrl/rest/workflows/$workflowId" -Body $payloadUpdate -ContentType "application/json"
}
catch {
    Write-Error "Failed to update workflow via API: $_"
    exit 1
}

# 3. Give n8n a moment to write the file
Start-Sleep -Seconds 5

# 4. Verify the file exists and contains the updated name
if (-Not (Test-Path $workflowFile)) {
    Write-Error "Workflow file not found: $workflowFile"
    exit 1
}
$content = Get-Content $workflowFile -Raw
if ($content -notmatch '"name":"${workflowName}-updated"') {
    Write-Error "Workflow file does not contain updated name"
    exit 1
}
Write-Host "✅ Persistence verification succeeded."

# 5. Cleanup: delete the workflow via API (optional)
try { Invoke-RestMethod -Method DELETE -Uri "$baseUrl/rest/workflows/$workflowId" } catch { }

# This script verifies that n8n UI (or API) writes edited workflows to the mounted ./workflows directory.
# It waits for the n8n health endpoint to be ready, creates a dummy workflow via the REST API,
# updates it, and checks that the corresponding JSON file on disk reflects the change.

$baseUrl = "http://localhost:5678"
$healthUrl = "$baseUrl/healthz"
$workflowName = "verify_persistence_dummy"
$workflowFile = Join-Path (Resolve-Path "./workflows") "$workflowName.json"

function Wait-ForHealth {
    param([int]$timeoutSec = 30)
    $elapsed = 0
    while ($elapsed -lt $timeoutSec) {
        try {
            $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { return $true }
        }
        catch { }
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    return $false
}

if (-not (Wait-ForHealth)) {
    Write-Error "n8n health endpoint not reachable after waiting"
    exit 1
}

# 1. Create a simple workflow via API (no auth assumed)
$payload = @{
    name        = $workflowName
    nodes       = @()
    connections = @{}
    active      = $false
    settings    = @{}
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Method POST -Uri "$baseUrl/rest/workflows" -Body $payload -ContentType "application/json"
}
catch {
    Write-Error "Failed to create workflow via API: $_"
    exit 1
}
if (-not $response.id) {
    Write-Error "API did not return workflow ID"
    exit 1
}
$workflowId = $response.id

# 2. Update the workflow name via API
$payloadUpdate = @{ name = "${workflowName}-updated" } | ConvertTo-Json
try {
    Invoke-RestMethod -Method PATCH -Uri "$baseUrl/rest/workflows/$workflowId" -Body $payloadUpdate -ContentType "application/json"
}
catch {
    Write-Error "Failed to update workflow via API: $_"
    exit 1
}

# 3. Give n8n a moment to write the file
Start-Sleep -Seconds 3

# 4. Verify the file exists and contains the updated name
if (-Not (Test-Path $workflowFile)) {
    Write-Error "Workflow file not found: $workflowFile"
    exit 1
}
$content = Get-Content $workflowFile -Raw
if ($content -notmatch '"name":"${workflowName}-updated"') {
    Write-Error "Workflow file does not contain updated name"
    exit 1
}
Write-Host "✅ Persistence verification succeeded."

# 5. Cleanup: delete the workflow via API (optional)
try { Invoke-RestMethod -Method DELETE -Uri "$baseUrl/rest/workflows/$workflowId" } catch { }

# This script checks that editing a workflow via the n8n UI (or API) updates the file on disk.

# Configuration
$baseUrl = "http://localhost:5678"
$workflowName = "verify_persistence_dummy"
$workflowFile = Join-Path (Resolve-Path "./workflows") "$workflowName.json"

# 1. Create a simple workflow via API
$payload = @{
    name        = $workflowName
    nodes       = @()
    connections = @{}
    active      = $false
    settings    = @{}
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Method POST -Uri "$baseUrl/rest/workflows" -Body $payload -ContentType "application/json"
if (-not $response.id) {
    Write-Error "Failed to create workflow via API"
    exit 1
}
$workflowId = $response.id

# 2. Update the workflow (e.g., change name) via API
$payloadUpdate = @{
    name = "${workflowName}-updated"
} | ConvertTo-Json
Invoke-RestMethod -Method PATCH -Uri "$baseUrl/rest/workflows/$workflowId" -Body $payloadUpdate -ContentType "application/json"

# 3. Wait a moment for n8n to write the file
Start-Sleep -Seconds 2

# 4. Verify that the file exists and contains the updated name
if (-Not (Test-Path $workflowFile)) {
    Write-Error "Workflow file not found: $workflowFile"
    exit 1
}
$content = Get-Content $workflowFile -Raw
if ($content -notmatch '"name":"${workflowName}-updated"') {
    Write-Error "Workflow file does not contain updated name"
    exit 1
}
Write-Host "✅ Persistence verification succeeded."

# Cleanup (optional): delete the workflow via API
Invoke-RestMethod -Method DELETE -Uri "$baseUrl/rest/workflows/$workflowId"

# login_and_upload.ps1
# Настройки — отредактируй перед запуском:
$apiBase = "http://localhost:8000"
$username = "admin"
$password = "password123"    # <- поставь реальный пароль
$uploadFile = ".\data\parsed_normalized.ndjson"  # <- путь к файлу на хосте

# 1) Логин: POST /login (ожидается JSON ответ { access_token: "..."} )
$loginUrl = "$apiBase/token"

$body = @{ username = $username; password = $password } | ConvertTo-Json

Write-Host "Logging in as $username ..."
try {
    $resp = Invoke-RestMethod -Uri $loginUrl -Method Post -Body $body -ContentType 'application/json' -ErrorAction Stop
} catch {
    Write-Error "Login failed: $($_.Exception.Message)"
    exit 1
}

$token = $resp.access_token
if (-not $token) {
    Write-Error "No token received. Response: $($resp | ConvertTo-Json -Depth 5)"
    exit 1
}

Write-Host "Token received. Length:" ($token.Length)

# 2) Проверка: GET /api/v1/flights (пример)
Write-Host "Requesting /api/v1/flights ..."
try {
    $fl = Invoke-RestMethod -Uri "$apiBase/api/v1/flights" -Headers @{ Authorization = "Bearer $token" } -ErrorAction Stop
    Write-Host "Flights returned:" ($fl | Measure-Object).Count
} catch {
    Write-Warning "Warning: could not fetch flights: $($_.Exception.Message)"
}

# 3) Upload файл (multipart/form-data) — если endpoint поддерживает UploadFile
if (Test-Path $uploadFile) {
    Write-Host "Uploading file $uploadFile ..."
    # в PowerShell Invoke-RestMethod не всегда корректно формирует boundary для больших файлов,
    # поэтому используем Invoke-WebRequest с -InFile, но у некоторых версий PS нужен ручной trick.
    try {
        $form = @{ file = Get-Item $uploadFile }
        $up = Invoke-RestMethod -Uri "$apiBase/api/v1/upload" -Method Post -Headers @{ Authorization = "Bearer $token" } -Form $form -ErrorAction Stop
        Write-Host "Upload response:" ($up | ConvertTo-Json -Depth 4)
    } catch {
        Write-Warning "Upload via Invoke-RestMethod failed: $($_.Exception.Message)"
        Write-Host "Trying curl.exe fallback..."
        # fallback: use curl.exe (bundled with Windows 10+)
        $curlCmd = "curl.exe -i -X POST -H `"Authorization: Bearer $token`" -F `"file=@$uploadFile`" `"$apiBase/api/v1/upload`""
        Write-Host $curlCmd
        Invoke-Expression $curlCmd
    }
} else {
    Write-Warning "Upload file not found: $uploadFile"
}

Write-Host "Done."

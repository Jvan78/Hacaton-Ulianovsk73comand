<#
  batch_update_regions.ps1
  Запускается в Windows PowerShell / PowerShell Core.
  Из корня проекта Hacatonreal (где docker-compose.yml).
#>

param(
    [int]$Batch = 1000,          # сколько id берем за итерацию
    [int]$WithinMeters = 1000    # радиус ST_DWithin в метрах
)

function Run-BatchUpdate($sql) {
    # Возвращает число строк, которые вернул psql (кол-во id)
    $raw = docker compose exec db psql -U postgres -d gis -t -A -c "$sql" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "psql вернул ошибку: $raw"
        throw "psql failed"
    }
    # raw может содержать пустую строку; посчитаем ненулевые строки
    $lines = $raw -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    return $lines.Count
}

Write-Output "START batch updates (Batch=$Batch, WithinMeters=$WithinMeters) - $(Get-Date)"

# 1) start_region_id
Write-Output "`n=== Updating start_region_id ==="
while ($true) {
    $sql = @"
WITH to_update AS (
  SELECT id FROM flights
  WHERE start_geom IS NOT NULL AND start_region_id IS NULL
  LIMIT $Batch
)
UPDATE flights f
SET start_region_id = r.gid
FROM public.regions r, to_update t
WHERE f.id = t.id
  AND ST_DWithin(r.geom::geography, f.start_geom::geography, $WithinMeters)
RETURNING f.id;
"@

    try {
        $updated = Run-BatchUpdate $sql
    } catch {
        Write-Error "Ошибка при обновлении start_region_id: $_"
        break
    }

    Write-Output "start updated: $updated"
    if ($updated -eq 0) { break }
}

# 2) end_region_id
Write-Output "`n=== Updating end_region_id ==="
while ($true) {
    $sql = @"
WITH to_update AS (
  SELECT id FROM flights
  WHERE end_geom IS NOT NULL AND end_region_id IS NULL
  LIMIT $Batch
)
UPDATE flights f
SET end_region_id = r.gid
FROM public.regions r, to_update t
WHERE f.id = t.id
  AND ST_DWithin(r.geom::geography, f.end_geom::geography, $WithinMeters)
RETURNING f.id;
"@

    try {
        $updated = Run-BatchUpdate $sql
    } catch {
        Write-Error "Ошибка при обновлении end_region_id: $_"
        break
    }

    Write-Output "end updated: $updated"
    if ($updated -eq 0) { break }
}

Write-Output "`nBATCH UPDATES FINISHED - $(Get-Date)"
# итоговые контрольные запросы
docker compose exec db psql -U postgres -d gis -c "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE start_region_id IS NOT NULL) AS with_start_region, COUNT(*) FILTER (WHERE end_region_id IS NOT NULL) AS with_end_region FROM flights;"

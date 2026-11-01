# Extract plant hrefs from index.html
$lines = Get-Content 'index.html'
$gardenPlants = @()
foreach ($line in $lines) {
    if ($line -match 'class="plant-card"') {
        if ($line -match 'href="([^"]+\.html)"') {
            $gardenPlants += $Matches[1]
        }
    }
}

Write-Host "Plants in index.html:"
$gardenPlants | Sort-Object | ForEach-Object { Write-Host $_ }
Write-Host ""
Write-Host "Total plants in Garden: $($gardenPlants.Count)"

# Get all .html files in the directory (excluding index.html, bookmarks.html, login.html)
$allPlantFiles = Get-ChildItem -Name "*.html" | Where-Object { 
    $_ -ne 'index.html' -and
    $_ -ne 'bookmarks.html' -and 
    $_ -ne 'login.html'
}

Write-Host ""
Write-Host "All HTML files not in index.html:"
$missingFiles = $allPlantFiles | Where-Object {
    $gardenPlants -notcontains $_
}
$missingFiles | Sort-Object | ForEach-Object { Write-Host $_ }
Write-Host "Missing count: $($missingFiles.Count)"

$repos = @(
    "tk-core"
    "tk-framework-qtwidgets"
    "tk-framework-shotgunutils"
    "tk-multi-publish2"
)

foreach ($repo in $repos) {
    Write-Host
    Write-Host
    Write-Host "### Updating $repo"
    Write-Host

    # if not present, clone the repo
    if (-not (Test-Path "../$repo")) {
        Write-Host "$repo does not exist, cloning"
        git remote -v | Select-String -Pattern "origin\s+(.+)\s+\(fetch\)" | ForEach-Object {
            $baseUrl = [System.IO.Path]::GetDirectoryName($_.Matches[0].Groups[1].Value)
        }

        git clone "$baseUrl/$repo.git" "../$repo"
    }
    else {
        Write-Host "$repo already exists, pulling latest changes"
        git -C "../$repo" fetch
        git -C "../$repo" checkout .
        git -C "../$repo" clean -f -d -x .
        git -C "../$repo" switch master
        git -C "../$repo" merge
    }

    git -C "../$repo" clean -f -d -x .
}

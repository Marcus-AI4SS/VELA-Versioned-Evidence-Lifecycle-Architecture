$ErrorActionPreference = "Stop"



$git = "C:\Program Files\Git\cmd\git.exe"

$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"

$settings = Get-ItemProperty -Path $regPath



if (-not (Test-Path $git)) {

    throw "Git executable was not found at $git"

}



$proxyEnabled = $settings.ProxyEnable -eq 1 -and -not [string]::IsNullOrWhiteSpace($settings.ProxyServer)



if ($proxyEnabled) {

    $proxy = $settings.ProxyServer

    if ($proxy -notmatch '^[a-zA-Z]+://') {

        $proxy = "http://$proxy"

    }



    & $git config --global http.proxy $proxy

    & $git config --global https.proxy $proxy



    Write-Host "Git proxy synced." -ForegroundColor Green

    Write-Host "http.proxy  = $proxy"

    Write-Host "https.proxy = $proxy"

}

else {

    & $git config --global --unset-all http.proxy 2>$null

    & $git config --global --unset-all https.proxy 2>$null



    Write-Host "No user proxy is enabled in Windows. Git proxy settings were cleared." -ForegroundColor Yellow

}

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$logFile = Join-Path $scriptDir "github-trending.log"
$reportDir = "C:\Users\mooma\Desktop\github-trending"
$dateStr = Get-Date -Format "yyyy-MM-dd"
$dayOfWeek = Get-Date -Format "dddd"
$outputFile = Join-Path $reportDir "$dateStr-trending.md"

function Log($message) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$stamp] $message" | Out-File -FilePath $logFile -Append
}

try {
    Log "Starting fetch for $dateStr"
    
    $headers = @{
        "Accept" = "application/vnd.github.v3+json"
        "User-Agent" = "Growth-Architect-Agent"
    }
    if ($env:GITHUB_TOKEN) { $headers["Authorization"] = "token $env:GITHUB_TOKEN" }

    function Get-Repos($days, $limit) {
        $dateLimit = (Get-Date).AddDays(-$days).ToString("yyyy-MM-dd")
        $url = "https://api.github.com/search/repositories?q=created:%3E$dateLimit&sort=stars&order=desc&per_page=$limit"
        Start-Sleep -Seconds 3
        try {
            return (Invoke-RestMethod -Uri $url -Headers $headers -Method Get -TimeoutSec 30).items
        } catch {
            Log "API ERROR: $($_.Exception.Message)"
            return $null
        }
    }

    $dayRepos = Get-Repos 1 5
    $weekRepos = Get-Repos 7 20
    $monthRepos = Get-Repos 30 5
    # Fetch AI/DEV specific trends
    $aiTrending = (Invoke-RestMethod -Uri "https://api.github.com/search/repositories?q=created:%3E$((Get-Date).AddDays(-7).ToString('yyyy-MM-dd'))+topic:ai+topic:llm+topic:agent&sort=stars&order=desc&per_page=5" -Headers $headers).items

    $aiTerms = "ai|llm|gpt|claude|agent|machine-learning|deep-learning|generative|copilot|assistant|automation|dev-tool|developer-tool|cli|mcp"

    function Is-AiDev($repo) {
        $text = "$($repo.description) $($repo.full_name) $($repo.topics -join ' ')"
        return $text -match $aiTerms
    }

    $md += "# GitHub Trending - $dateStr ($dayOfWeek)`n`n"
    
    $md += "## Top 20 Trending This Week`n"
    $weekCount = 0
    $topAi = $null
    foreach ($repo in $weekRepos) {
        $weekCount++
        $tag = if (Is-AiDev $repo) { " **[AI/DEV]**" } else { "" }
        if ($tag -and !$topAi) { $topAi = $repo }
        $md += "$weekCount. [$($repo.full_name)]($($repo.html_url))$tag - $($repo.stargazers_count.ToString('N0')) stars, $($repo.language), Created: $($repo.created_at.Substring(0,10))<br>Topics: $($repo.topics -join ', ')<br>Description: $($repo.description)`n"
    }

    $md += "`n## Top 5 Trending This Last 24 Hours`n"
    $dayCount = 0
    foreach ($repo in $dayRepos) {
        $dayCount++
        $md += "$dayCount. [$($repo.full_name)]($($repo.html_url)) - $($repo.stargazers_count.ToString('N0')) stars, $($repo.language), Created: $($repo.created_at.Substring(0,10))<br>Topics: $($repo.topics -join ', ')<br>Description: $($repo.description)`n"
    }

    $md += "`n## Top 5 AI/DEV Specific Trending`n"
    $aiCount = 0
    foreach ($repo in $aiTrending) {
        $aiCount++
        $md += "$aiCount. [$($repo.full_name)]($($repo.html_url)) - $($repo.stargazers_count.ToString('N0')) stars, $($repo.language), Created: $($repo.created_at.Substring(0,10))<br>Topics: $($repo.topics -join ', ')<br>Description: $($repo.description)`n"
    }

    $md += "`n## Top 5 Trending This Month`n"
    $monthCount = 0
    foreach ($repo in $monthRepos) {
        $monthCount++
        $tag = if (Is-AiDev $repo) { " **[AI/DEV]**" } else { "" }
        $md += "$monthCount. [$($repo.full_name)]($($repo.html_url))$tag - $($repo.stargazers_count.ToString('N0')) stars, $($repo.language), Created: $($repo.created_at.Substring(0,10))<br>Topics: $($repo.topics -join ', ')<br>Description: $($repo.description)`n"
    }

    $aiRelevantCount = ($weekRepos | Where-Object { Is-AiDev $_ }).Count
    $md += "`n## Content Radar`n- **$aiRelevantCount** AI/DEV-relevant repos out of 10 this week."
    if ($topAi) {
        $md += "`n- **Top AI Pick**: [$($topAi.full_name)]($($topAi.html_url)) ($($topAi.stargazers_count) stars) - $($topAi.description)"
    }

    $md | Out-File -FilePath $outputFile -Encoding utf8
    Log "Successfully wrote $outputFile"

} catch {
    Log "ERROR: $($_.Exception.Message)"
    exit 1
}

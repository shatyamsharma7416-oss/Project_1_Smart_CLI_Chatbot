<#
    chat.ps1 — talk to your deployed Smart CLI Chatbot API from PowerShell.

    Usage:
      # one-off setup for this PowerShell session:
      $BaseUrl = "https://your-app-name.onrender.com"
      $ApiKey  = "your-api-key"       # only needed if you set API_KEY on Render
      . .\chat.ps1                    # dot-source to load the Chat-Bot function

      # then just chat:
      Chat-Bot "Hello, who are you?"
      Chat-Bot "Follow-up question"   # keeps using the same session automatically
      Chat-Bot "Start fresh" -NewSession -Persona casual
#>

$script:SessionId = $null

function Chat-Bot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [ValidateSet("professional", "casual", "socratic")]
        [string]$Persona = "professional",

        [switch]$NewSession
    )

    if (-not $BaseUrl) {
        Write-Error "Set `$BaseUrl first, e.g. `$BaseUrl = 'https://your-app-name.onrender.com'"
        return
    }

    $headers = @{ "Content-Type" = "application/json" }
    if ($ApiKey) { $headers["X-API-Key"] = $ApiKey }

    $body = @{
        message = $Message
        persona = $Persona
    }

    if ($script:SessionId -and -not $NewSession) {
        $body["session_id"] = $script:SessionId
    }

    $json = $body | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/chat" -Method Post -Headers $headers -Body $json
    }
    catch {
        Write-Error "Request failed: $_"
        return
    }

    $script:SessionId = $response.session_id

    Write-Host ""
    Write-Host "Bot: " -ForegroundColor Green -NoNewline
    Write-Host $response.reply
    Write-Host "  (session: $($response.session_id) | context: $($response.context_pct)%)" -ForegroundColor DarkGray
    Write-Host ""
}
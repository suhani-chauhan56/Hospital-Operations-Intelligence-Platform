param(
    [switch]$SkipTraining,
    [switch]$LoadMySQL,
    [switch]$LaunchDashboard
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

function Invoke-ProjectPython {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python stage failed ($LASTEXITCODE): python $($Arguments -join ' ')"
    }
}

Invoke-ProjectPython @("src\data_pipeline.py")

if (-not $SkipTraining) {
    Invoke-ProjectPython @("src\train_models.py")
    Invoke-ProjectPython @("src\shap_explainability.py")
}

Invoke-ProjectPython @("src\generate_executive_report.py")
Invoke-ProjectPython @("src\validate_project.py")
Invoke-ProjectPython @("src\package_streamlit_deployment.py")

if ($LoadMySQL) {
    Invoke-ProjectPython @("src\load_mysql.py", "--truncate")
    Invoke-ProjectPython @(
        "src\verify_mysql_deployment.py",
        "--require-ready"
    )
}

if ($LaunchDashboard) {
    Invoke-ProjectPython @(
        "-m",
        "streamlit",
        "run",
        "streamlit\app.py"
    )
}

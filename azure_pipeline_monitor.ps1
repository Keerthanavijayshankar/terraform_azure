# Azure Pipeline Monitor - PowerShell Wrapper
# This script provides a Windows-friendly way to run the Azure Pipeline Monitor

param(
    [string]$ConfigFile = "config.json",
    [switch]$Test = $false,
    [switch]$Help = $false
)

# Show help
if ($Help) {
    Write-Host "Azure Pipeline Monitor - PowerShell Wrapper" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\azure_pipeline_monitor.ps1                 # Run with default config"
    Write-Host "  .\azure_pipeline_monitor.ps1 -Test           # Test setup"
    Write-Host "  .\azure_pipeline_monitor.ps1 -ConfigFile custom.json  # Use custom config"
    Write-Host "  .\azure_pipeline_monitor.ps1 -Help           # Show this help"
    Write-Host ""
    Write-Host "Setup:" -ForegroundColor Yellow
    Write-Host "  1. Install Python 3.8 or higher"
    Write-Host "  2. pip install -r requirements.txt"
    Write-Host "  3. Copy config.json.template to config.json"
    Write-Host "  4. Edit config.json with your settings"
    Write-Host ""
    exit 0
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Blue
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path "venv\bin\activate") {
    Write-Host "🔄 Activating virtual environment (Linux/Mac)..." -ForegroundColor Blue
    & "venv\bin\activate"
} else {
    Write-Host "⚠️  Virtual environment not found. Using system Python." -ForegroundColor Yellow
}

# Run test if requested
if ($Test) {
    Write-Host "🧪 Running setup test..." -ForegroundColor Blue
    python test_setup.py
    exit $LASTEXITCODE
}

# Check if config file exists
if (-not (Test-Path $ConfigFile)) {
    Write-Host "❌ Configuration file '$ConfigFile' not found." -ForegroundColor Red
    Write-Host "Please copy config.json.template to $ConfigFile and edit it." -ForegroundColor Yellow
    exit 1
}

# Run the monitor
Write-Host "🔍 Starting Azure Pipeline Monitor..." -ForegroundColor Blue
Write-Host "Configuration: $ConfigFile" -ForegroundColor Gray

try {
    if ($ConfigFile -eq "config.json") {
        python azure_pipeline_monitor.py
    } else {
        # Note: You'd need to modify the Python script to accept config file parameter
        Write-Host "⚠️  Custom config file support requires modifying the Python script." -ForegroundColor Yellow
        python azure_pipeline_monitor.py
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Monitor completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Monitor failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error running monitor: $_" -ForegroundColor Red
    exit 1
}

# Show log location
if (Test-Path "azure_pipeline_monitor.log") {
    Write-Host ""
    Write-Host "📋 Log file: azure_pipeline_monitor.log" -ForegroundColor Gray
    Write-Host "Recent log entries:" -ForegroundColor Gray
    Get-Content "azure_pipeline_monitor.log" -Tail 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
}
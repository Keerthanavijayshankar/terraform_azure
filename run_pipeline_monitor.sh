#!/bin/bash

# Azure DevOps Pipeline Error Monitor
# This script sets up and runs the pipeline monitor

set -e

echo "🚀 Azure DevOps Pipeline Error Monitor"
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install required packages if not already installed
echo "📦 Installing required Python packages..."
pip3 install -r requirements.txt --quiet --user

# Check environment variables
if [[ -z "$AZURE_DEVOPS_ORG" ]]; then
    echo "❌ AZURE_DEVOPS_ORG environment variable is not set."
    echo "   Please set it to your Azure DevOps organization name."
    echo "   Example: export AZURE_DEVOPS_ORG='myorg'"
    exit 1
fi

if [[ -z "$AZURE_DEVOPS_PROJECT" ]]; then
    echo "❌ AZURE_DEVOPS_PROJECT environment variable is not set."
    echo "   Please set it to your project name."
    echo "   Example: export AZURE_DEVOPS_PROJECT='myproject'"
    exit 1
fi

if [[ -z "$AZURE_DEVOPS_PAT" ]]; then
    echo "❌ AZURE_DEVOPS_PAT environment variable is not set."
    echo "   Please set it to your Personal Access Token."
    echo "   Example: export AZURE_DEVOPS_PAT='your-pat-token'"
    echo ""
    echo "   To create a PAT:"
    echo "   1. Go to https://dev.azure.com/{your-org}/_usersSettings/tokens"
    echo "   2. Click 'New Token'"
    echo "   3. Give it a name and select 'Build (read)' scope"
    echo "   4. Copy the token and set it as AZURE_DEVOPS_PAT"
    exit 1
fi

echo "✅ Environment variables configured:"
echo "   Organization: $AZURE_DEVOPS_ORG"
echo "   Project: $AZURE_DEVOPS_PROJECT"
echo "   PAT: $(echo $AZURE_DEVOPS_PAT | cut -c1-4)****"
echo ""

# Run the monitor
echo "🔍 Running pipeline monitor..."
python3 azure_pipeline_monitor.py

echo ""
echo "✅ Pipeline monitor completed successfully!"
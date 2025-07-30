#!/bin/bash

# Demo Setup Script for Azure DevOps Pipeline Monitor
# This script helps you set up and test the pipeline monitor

echo "🎬 Azure DevOps Pipeline Monitor - Demo Setup"
echo "============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "azure_pipeline_monitor.py" ]; then
    echo "❌ azure_pipeline_monitor.py not found in current directory"
    echo "   Please run this script from the directory containing the monitor files"
    exit 1
fi

echo "📝 This demo will guide you through setting up the pipeline monitor."
echo ""

# Get organization name
echo "Please provide your Azure DevOps details:"
echo ""
read -p "🏢 Azure DevOps Organization (from URL https://dev.azure.com/YOUR_ORG): " org_name

if [ -z "$org_name" ]; then
    echo "❌ Organization name cannot be empty"
    exit 1
fi

# Get project name
read -p "📁 Project Name: " project_name

if [ -z "$project_name" ]; then
    echo "❌ Project name cannot be empty"
    exit 1
fi

# Get PAT
echo ""
echo "🔑 Personal Access Token (PAT) Setup:"
echo "   1. Go to https://dev.azure.com/$org_name/_usersSettings/tokens"
echo "   2. Click 'New Token'"
echo "   3. Name: 'Pipeline Monitor'"
echo "   4. Scope: Custom -> Build (Read)"
echo "   5. Copy the generated token"
echo ""
read -s -p "🔐 Enter your PAT: " pat_token
echo ""

if [ -z "$pat_token" ]; then
    echo "❌ PAT cannot be empty"
    exit 1
fi

# Set environment variables
export AZURE_DEVOPS_ORG="$org_name"
export AZURE_DEVOPS_PROJECT="$project_name"
export AZURE_DEVOPS_PAT="$pat_token"

echo ""
echo "✅ Environment variables set:"
echo "   Organization: $AZURE_DEVOPS_ORG"
echo "   Project: $AZURE_DEVOPS_PROJECT"
echo "   PAT: $(echo $AZURE_DEVOPS_PAT | cut -c1-4)****"
echo ""

# Save to a file for future use (excluding PAT for security)
cat > .env << EOF
# Azure DevOps Configuration
# Source this file: source .env
export AZURE_DEVOPS_ORG="$org_name"
export AZURE_DEVOPS_PROJECT="$project_name"
# Set AZURE_DEVOPS_PAT separately for security
# export AZURE_DEVOPS_PAT="your-pat-here"
EOF

echo "💾 Configuration saved to .env file (excluding PAT for security)"
echo "   To reuse: source .env && export AZURE_DEVOPS_PAT='your-pat'"
echo ""

# Test connection
echo "🔍 Testing connection to Azure DevOps..."
python3 -c "
import requests
import base64
import sys

org = '$org_name'
project = '$project_name'
pat = '$pat_token'

auth_string = f':{pat}'
encoded_auth = base64.b64encode(auth_string.encode()).decode()
headers = {'Authorization': f'Basic {encoded_auth}'}

try:
    url = f'https://dev.azure.com/{org}/{project}/_apis/build/definitions?api-version=7.0'
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', 0)
        print(f'✅ Connection successful! Found {count} pipeline(s)')
    else:
        print(f'❌ Connection failed: HTTP {response.status_code}')
        if response.status_code == 401:
            print('   Check your PAT and permissions')
        elif response.status_code == 404:
            print('   Check organization and project names')
        sys.exit(1)
except Exception as e:
    print(f'❌ Connection error: {e}')
    sys.exit(1)
" || {
    echo "❌ Connection test failed. Please check your settings and try again."
    exit 1
}

echo ""
echo "🚀 Ready to run the pipeline monitor!"
echo ""
echo "Choose an option:"
echo "1. Run the monitor now"
echo "2. Show usage instructions"
echo "3. Exit"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🔍 Running pipeline monitor..."
        ./run_pipeline_monitor.sh
        ;;
    2)
        echo ""
        echo "📖 Usage Instructions:"
        echo "====================="
        echo ""
        echo "To run the monitor anytime:"
        echo "  1. Set environment variables:"
        echo "     export AZURE_DEVOPS_ORG='$org_name'"
        echo "     export AZURE_DEVOPS_PROJECT='$project_name'"
        echo "     export AZURE_DEVOPS_PAT='your-pat'"
        echo ""
        echo "  2. Run the monitor:"
        echo "     ./run_pipeline_monitor.sh"
        echo ""
        echo "Or use the saved configuration:"
        echo "  source .env"
        echo "  export AZURE_DEVOPS_PAT='your-pat'"
        echo "  ./run_pipeline_monitor.sh"
        echo ""
        ;;
    3)
        echo "👋 Goodbye!"
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac

echo ""
echo "📚 For detailed documentation, see: PIPELINE_MONITOR_USAGE.md"
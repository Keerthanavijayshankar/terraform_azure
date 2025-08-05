#!/bin/bash

# Azure Pipeline Monitor Setup Script

echo "🔧 Setting up Azure Pipeline Monitor..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy configuration template
if [ ! -f "config.json" ]; then
    echo "📋 Creating configuration file from template..."
    cp config.json.template config.json
    echo "⚠️  Please edit config.json with your Azure DevOps and email settings"
else
    echo "✅ Configuration file already exists"
fi

# Make script executable
chmod +x azure_pipeline_monitor.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your Azure DevOps and email settings"
echo "2. Run the monitor: ./azure_pipeline_monitor.py"
echo "3. Set up a cron job for automated monitoring"
echo ""
echo "For cron job setup, add this line to your crontab (crontab -e):"
echo "# Run every hour during business hours (9 AM to 6 PM, Mon-Fri)"
echo "0 9-18 * * 1-5 cd $(pwd) && source venv/bin/activate && python azure_pipeline_monitor.py"
echo ""
echo "📖 For detailed instructions, see README.md"
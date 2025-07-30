# Azure DevOps Pipeline Error Monitor

This tool helps you quickly identify and troubleshoot Azure DevOps pipelines that have failed today, providing intelligent error analysis and suggested solutions.

## Features

- 🔍 **Automatic Detection**: Finds all pipelines that failed today
- 🧠 **Smart Error Analysis**: Analyzes logs to categorize error types
- 💡 **Solution Suggestions**: Provides specific solutions based on error patterns
- 📊 **Detailed Reports**: Shows comprehensive information about each failure
- 📄 **JSON Export**: Generates machine-readable reports for automation
- 🎯 **Error Categories**: Covers authentication, dependencies, Terraform, network, resources, and configuration issues

## Prerequisites

- Python 3.6 or higher
- pip3 (Python package manager)
- Azure DevOps Personal Access Token (PAT) with Build (read) permissions

## Quick Start

### 1. Set up Environment Variables

```bash
# Your Azure DevOps organization (from the URL: https://dev.azure.com/YOUR_ORG)
export AZURE_DEVOPS_ORG="keerthisha6"

# Your project name
export AZURE_DEVOPS_PROJECT="Terraform Code"

# Your Personal Access Token (see setup instructions below)
export AZURE_DEVOPS_PAT="BVmWuKRs0Jv3My6ni1i2ye7jqC2vH7QEE9vruXuEsbjN3DZ5oKFBJQQJ99BGACAAAAAAAAAAAAASAZDOkLhv"
```

### 2. Run the Monitor

**Option A: Use the convenience script (recommended)**
```bash
./run_pipeline_monitor.sh
```

**Option B: Run Python directly**
```bash
pip3 install -r requirements.txt
python3 azure_pipeline_monitor.py
```

## Setting up Personal Access Token (PAT)

1. Go to your Azure DevOps organization: `https://dev.azure.com/{your-org}`
2. Click on your profile picture → **Personal access tokens**
3. Click **New Token**
4. Fill in the form:
   - **Name**: Pipeline Monitor (or any descriptive name)
   - **Organization**: Select your organization
   - **Expiration**: Choose appropriate duration
   - **Scopes**: Select **Custom defined** and check:
     - **Build**: Read (required)
     - **Project and Team**: Read (optional, for better project info)
5. Click **Create**
6. Copy the token immediately (you won't see it again!)
7. Set it as an environment variable: `export AZURE_DEVOPS_PAT="your-copied-token"`

## Error Categories and Solutions

The tool automatically categorizes errors and provides relevant solutions:

### 🔐 Authentication Errors
- Invalid credentials
- Expired tokens
- Permission issues
- **Solutions**: Check service connections, verify PAT, update permissions

### 📦 Dependency Errors
- Missing packages
- Version conflicts
- Package feed issues
- **Solutions**: Update package files, clear caches, check feed access

### 🏗️ Terraform Errors
- State lock issues
- Provider errors
- Resource conflicts
- **Solutions**: Check state locks, verify permissions, validate syntax

### 🌐 Network Errors
- Connection timeouts
- DNS resolution
- Firewall issues
- **Solutions**: Check connectivity, verify firewall rules, try different agents

### 💾 Resource Errors
- Memory issues
- Disk space
- Quota limits
- **Solutions**: Increase allocations, clean up space, check quotas

### ⚙️ Configuration Errors
- YAML syntax
- Missing variables
- Invalid configurations
- **Solutions**: Validate YAML, check variables, verify service connections

## Output Examples

### Console Output
```
🔍 Checking Azure DevOps pipelines for organization: myorg
📁 Project: myproject
📅 Date: 2024-01-15

📊 Found 2 pipeline(s) with errors today:

================================================================================

1. 🔴 Pipeline: terraform-infrastructure
   📋 Pipeline ID: 123
   🏗️  Build ID: 456
   📁 Repository: infrastructure-repo
   🌿 Branch: refs/heads/main
   ⏰ Start Time: 2024-01-15T08:30:00Z
   ⏹️  Finish Time: 2024-01-15T08:35:00Z
   🏷️  Error Type: Terraform
   ❌ Error: Error: Error acquiring the state lock...

   💡 Possible Solutions:
      1. Check Terraform state lock - may need to force unlock
      2. Verify Azure provider version compatibility
      3. Ensure service principal has required Azure permissions
      4. Check if Azure resources already exist or were deleted outside Terraform
      5. Validate Terraform syntax with 'terraform validate'
      6. Update provider versions to latest stable

📈 Error Summary:
   • Terraform: 1
   • Authentication: 1
```

### JSON Report
A detailed JSON report is automatically generated: `pipeline_errors_YYYYMMDD.json`

```json
{
  "date": "2024-01-15T10:30:00",
  "organization": "myorg",
  "project": "myproject",
  "total_errors": 2,
  "errors": [
    {
      "pipeline_name": "terraform-infrastructure",
      "pipeline_id": 123,
      "build_id": 456,
      "error_type": "terraform",
      "error_message": "Error: Error acquiring the state lock...",
      "repository": "infrastructure-repo",
      "branch": "refs/heads/main",
      "start_time": "2024-01-15T08:30:00Z",
      "finish_time": "2024-01-15T08:35:00Z",
      "solutions": [
        "Check Terraform state lock - may need to force unlock",
        "Verify Azure provider version compatibility",
        "..."
      ]
    }
  ]
}
```

## Automation and Integration

### Cron Job for Daily Monitoring
Add to your crontab for daily monitoring:

```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/pipeline-monitor && ./run_pipeline_monitor.sh >> /var/log/pipeline-monitor.log 2>&1
```

### Integration with Slack/Teams
Use the JSON output to integrate with notification systems:

```bash
#!/bin/bash
./run_pipeline_monitor.sh
if [ -f "pipeline_errors_$(date +%Y%m%d).json" ]; then
    # Parse JSON and send to Slack/Teams
    python3 send_notifications.py
fi
```

### CI/CD Integration
Add to your pipeline to monitor other pipelines:

```yaml
- task: Bash@3
  displayName: 'Monitor Pipeline Errors'
  inputs:
    scriptLocation: 'inlineScript'
    inlineScript: |
      export AZURE_DEVOPS_ORG="$(System.TeamFoundationCollectionUri | sed 's|https://dev.azure.com/||' | sed 's|/||')"
      export AZURE_DEVOPS_PROJECT="$(System.TeamProject)"
      export AZURE_DEVOPS_PAT="$(System.AccessToken)"
      ./run_pipeline_monitor.sh
```

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check if PAT is correctly set
   - Verify PAT has Build (read) permissions
   - Ensure PAT hasn't expired

2. **"No builds found"**
   - Check if there were actually any failed builds today
   - Verify organization and project names are correct
   - Ensure you have access to the project

3. **"Permission denied"**
   - Check PAT permissions
   - Verify you're a member of the project
   - Ensure organization name is correct

4. **"Python packages not found"**
   - Run: `pip3 install -r requirements.txt`
   - Check Python and pip3 installation

### Debug Mode
For more detailed logging, modify the script to enable debug mode:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To extend the error patterns and solutions:

1. Edit the `error_patterns` dictionary in `azure_pipeline_monitor.py`
2. Add new patterns using regex
3. Provide relevant solutions for each pattern type
4. Test with real error logs

## Security Notes

- Store PAT securely and never commit it to version control
- Use environment variables or secure secret management
- Regularly rotate your PAT
- Limit PAT permissions to minimum required (Build read only)
- Consider using service principals for production environments

# Azure Pipeline Monitor

A comprehensive Python script that monitors Azure DevOps pipelines for failures, analyzes errors, and sends detailed reports with solutions via email.

## Features

- 🔍 **Real-time Monitoring**: Monitors all pipeline runs from today
- 🚨 **Error Detection**: Identifies and categorizes common pipeline errors
- 💡 **Solution Recommendations**: Provides specific solutions for detected errors
- 📧 **HTML Email Reports**: Sends beautiful, detailed reports via email
- 🔧 **Comprehensive Error Database**: Built-in solutions for build, test, deployment, and agent errors
- 📊 **Detailed Logging**: Tracks all monitoring activities with timestamps

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <your-repo>
   cd azure-pipeline-monitor
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure**:
   Edit `config.json` with your Azure DevOps and email settings.

3. **Run**:
   ```bash
   ./azure_pipeline_monitor.py
   ```

## Installation

### Prerequisites

- Python 3.8 or higher
- Azure DevOps organization with pipeline access
- Email account with SMTP access

### Manual Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Configuration**:
   ```bash
   cp config.json.template config.json
   # Edit config.json with your settings
   ```

3. **Make Executable**:
   ```bash
   chmod +x azure_pipeline_monitor.py
   ```

## Configuration

### Azure DevOps Setup

1. **Create Personal Access Token (PAT)**:
   - Go to Azure DevOps > User Settings > Personal Access Tokens
   - Create new token with the following scopes:
     - Build (read)
     - Release (read)
     - Pipeline (read)

2. **Get Organization and Project Names**:
   - Organization: Found in your Azure DevOps URL: `https://dev.azure.com/{organization}`
   - Project: Your specific project name

### Email Configuration

The script supports multiple email providers:

#### Gmail
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "email_user": "your-email@gmail.com",
  "email_password": "your-app-password"
}
```
**Note**: Use App Password instead of regular password for Gmail.

#### Outlook/Hotmail
```json
{
  "smtp_server": "smtp-mail.outlook.com",
  "smtp_port": 587,
  "email_user": "your-email@outlook.com",
  "email_password": "your-password"
}
```

#### Office 365
```json
{
  "smtp_server": "smtp.office365.com",
  "smtp_port": 587,
  "email_user": "your-email@company.com",
  "email_password": "your-password"
}
```

### Complete Configuration Example

```json
{
  "azure_devops_org": "mycompany",
  "azure_devops_project": "MyProject",
  "azure_devops_pat": "abcdef123456789...",
  
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "email_user": "monitoring@company.com",
  "email_password": "app-password-here",
  "recipient_emails": [
    "devops-team@company.com",
    "admin@company.com"
  ],
  
  "send_success_report": false
}
```

## Usage

### Manual Execution

```bash
# Run once
./azure_pipeline_monitor.py

# Run with specific config file
python azure_pipeline_monitor.py

# View logs
tail -f azure_pipeline_monitor.log
```

### Automated Monitoring with Cron

Set up automated monitoring by adding to your crontab:

```bash
# Edit crontab
crontab -e

# Add one of these lines:

# Every hour during business hours (9 AM to 6 PM, Mon-Fri)
0 9-18 * * 1-5 cd /path/to/azure-pipeline-monitor && source venv/bin/activate && python azure_pipeline_monitor.py

# Every 30 minutes during business hours
*/30 9-18 * * 1-5 cd /path/to/azure-pipeline-monitor && source venv/bin/activate && python azure_pipeline_monitor.py

# Daily at 9 AM
0 9 * * * cd /path/to/azure-pipeline-monitor && source venv/bin/activate && python azure_pipeline_monitor.py
```

### Systemd Service (Linux)

Create a systemd service for more robust monitoring:

1. **Create service file** (`/etc/systemd/system/azure-pipeline-monitor.service`):
   ```ini
   [Unit]
   Description=Azure Pipeline Monitor
   After=network.target

   [Service]
   Type=oneshot
   User=your-user
   WorkingDirectory=/path/to/azure-pipeline-monitor
   ExecStart=/path/to/azure-pipeline-monitor/venv/bin/python azure_pipeline_monitor.py
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

2. **Create timer file** (`/etc/systemd/system/azure-pipeline-monitor.timer`):
   ```ini
   [Unit]
   Description=Run Azure Pipeline Monitor every hour
   Requires=azure-pipeline-monitor.service

   [Timer]
   OnCalendar=hourly
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. **Enable and start**:
   ```bash
   sudo systemctl enable azure-pipeline-monitor.timer
   sudo systemctl start azure-pipeline-monitor.timer
   ```

## Error Detection and Solutions

The monitor includes a comprehensive database of common Azure Pipeline errors and their solutions:

### Build Errors
- **MSB3644**: Reference assemblies not available
- **CS0006**: Metadata file not found
- **NU1102**: Package not found
- **MSB4019**: Imported project not found

### Test Errors
- **TestHostTimeout**: Test execution timeout
- **OutOfMemoryException**: Memory issues during testing

### Deployment Errors
- **ResourceNotFound**: Azure resource not found
- **AuthorizationFailed**: Insufficient permissions

### Agent Errors
- **AgentNotFound**: No available agents
- **DiskSpaceError**: Insufficient disk space

Each error includes:
- **Description**: What the error means
- **Solution**: How to fix it
- **Commands**: Specific commands to run

## Email Report Features

The HTML email reports include:

- 📊 **Summary**: Number of failed pipelines and organization info
- 🔍 **Pipeline Details**: Name, ID, status, and timestamps
- 🚨 **Error Analysis**: Categorized errors with descriptions
- 💡 **Solutions**: Specific recommendations and commands
- 📝 **Context**: Error logs with surrounding context
- 🔗 **Links**: Direct links to Azure DevOps portal

## Logging

The script creates detailed logs in `azure_pipeline_monitor.log`:

```
2024-01-15 10:30:00,123 - INFO - Starting Azure Pipeline monitoring...
2024-01-15 10:30:01,456 - INFO - Found 5 pipeline runs today
2024-01-15 10:30:02,789 - INFO - Analyzing failed pipeline: Build Pipeline (ID: 123)
2024-01-15 10:30:05,012 - INFO - Email report sent successfully to admin@company.com
2024-01-15 10:30:05,013 - INFO - Monitoring completed successfully
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify PAT token is valid and has correct scopes
   - Check organization and project names

2. **Email Sending Fails**:
   - Verify SMTP settings
   - For Gmail, ensure you're using App Password
   - Check firewall/network restrictions

3. **No Pipeline Data**:
   - Verify the project has pipelines
   - Check date range (script monitors today's runs)

4. **Import Errors**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version: `python --version`

### Debug Mode

Add logging configuration for more detailed output:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Security Considerations

- Store PAT tokens securely
- Use App Passwords for email providers that support them
- Restrict email account permissions
- Consider using Azure Key Vault for sensitive data
- Regularly rotate PAT tokens

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new error patterns
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `azure_pipeline_monitor.log`
3. Create an issue in the repository
#!/usr/bin/env python3
"""
Azure Pipeline Monitor
A comprehensive script to monitor Azure DevOps pipelines for failures,
analyze errors, and send detailed reports with solutions via email.
"""

import os
import json
import logging
import smtplib
import requests
import base64
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import List, Dict, Any, Optional
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('azure_pipeline_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AzurePipelineMonitor:
    def __init__(self, config_file: str = 'config.json'):
        """Initialize the Azure Pipeline Monitor with configuration."""
        self.config = self.load_config(config_file)
        self.headers = self.setup_auth_headers()
        self.error_solutions = self.load_error_solutions()
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required configuration
            required_keys = [
                'azure_devops_org', 'azure_devops_project', 'azure_devops_pat',
                'smtp_server', 'smtp_port', 'email_user', 'email_password',
                'recipient_emails'
            ]
            
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing required configuration key: {key}")
            
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found. Please create it from the template.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def setup_auth_headers(self) -> Dict[str, str]:
        """Setup authentication headers for Azure DevOps API."""
        pat = self.config['azure_devops_pat']
        encoded_pat = base64.b64encode(f":{pat}".encode()).decode()
        return {
            'Authorization': f'Basic {encoded_pat}',
            'Content-Type': 'application/json'
        }
    
    def load_error_solutions(self) -> Dict[str, Dict[str, str]]:
        """Load error patterns and their solutions."""
        return {
            'build_errors': {
                'MSB3644': {
                    'description': 'The reference assemblies for framework are not available',
                    'solution': 'Install the correct .NET SDK version or update the target framework in your project file.',
                    'commands': ['dotnet --list-sdks', 'dotnet workload restore']
                },
                'CS0006': {
                    'description': 'Metadata file could not be found',
                    'solution': 'Clean and rebuild the solution. Check for missing dependencies.',
                    'commands': ['dotnet clean', 'dotnet restore', 'dotnet build']
                },
                'NU1102': {
                    'description': 'Unable to find package',
                    'solution': 'Check package source configuration and package availability.',
                    'commands': ['dotnet nuget list source', 'dotnet restore --force']
                },
                'MSB4019': {
                    'description': 'The imported project was not found',
                    'solution': 'Verify project references and SDK installation.',
                    'commands': ['dotnet restore', 'Check project file references']
                }
            },
            'test_errors': {
                'TestHostTimeout': {
                    'description': 'Test execution timed out',
                    'solution': 'Increase test timeout or optimize test performance.',
                    'commands': ['Add timeout configuration', 'Review test implementation']
                },
                'System.OutOfMemoryException': {
                    'description': 'Out of memory during test execution',
                    'solution': 'Increase agent memory or optimize test data usage.',
                    'commands': ['Configure agent pool', 'Optimize test data']
                }
            },
            'deployment_errors': {
                'ResourceNotFound': {
                    'description': 'Azure resource not found during deployment',
                    'solution': 'Verify resource group and resource names. Check permissions.',
                    'commands': ['az resource list', 'Check service connection permissions']
                },
                'AuthorizationFailed': {
                    'description': 'Insufficient permissions for deployment',
                    'solution': 'Update service principal permissions or service connection.',
                    'commands': ['Check service connection', 'Verify RBAC permissions']
                }
            },
            'agent_errors': {
                'AgentNotFound': {
                    'description': 'No available agents in the pool',
                    'solution': 'Add more agents to the pool or use Microsoft-hosted agents.',
                    'commands': ['Scale agent pool', 'Check agent status']
                },
                'DiskSpaceError': {
                    'description': 'Insufficient disk space on agent',
                    'solution': 'Clean up agent workspace or increase disk size.',
                    'commands': ['Clean workspace', 'Increase agent disk size']
                }
            }
        }
    
    def get_today_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipeline runs from today."""
        today = datetime.now().date()
        min_time = datetime.combine(today, datetime.min.time()).isoformat() + 'Z'
        max_time = datetime.combine(today + timedelta(days=1), datetime.min.time()).isoformat() + 'Z'
        
        url = f"https://dev.azure.com/{self.config['azure_devops_org']}/{self.config['azure_devops_project']}/_apis/pipelines/runs"
        params = {
            'api-version': '7.0',
            'minTime': min_time,
            'maxTime': max_time
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get('value', [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch pipeline runs: {e}")
            return []
    
    def get_pipeline_details(self, pipeline_id: int, run_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific pipeline run."""
        url = f"https://dev.azure.com/{self.config['azure_devops_org']}/{self.config['azure_devops_project']}/_apis/pipelines/{pipeline_id}/runs/{run_id}"
        params = {'api-version': '7.0'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch pipeline details for run {run_id}: {e}")
            return None
    
    def get_pipeline_logs(self, pipeline_id: int, run_id: int) -> List[str]:
        """Get logs from a failed pipeline run."""
        url = f"https://dev.azure.com/{self.config['azure_devops_org']}/{self.config['azure_devops_project']}/_apis/pipelines/{pipeline_id}/runs/{run_id}/logs"
        params = {'api-version': '7.0'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            logs_info = response.json().get('logs', [])
            
            all_logs = []
            for log_info in logs_info:
                log_id = log_info.get('id')
                if log_id:
                    log_url = f"{url}/{log_id}"
                    log_response = requests.get(log_url, headers=self.headers, params=params)
                    if log_response.status_code == 200:
                        all_logs.append(log_response.text)
            
            return all_logs
        except requests.RequestException as e:
            logger.error(f"Failed to fetch logs for run {run_id}: {e}")
            return []
    
    def analyze_error(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Analyze logs to identify errors and find solutions."""
        found_errors = []
        
        for log_content in logs:
            lines = log_content.split('\n')
            for i, line in enumerate(lines):
                # Check for various error patterns
                for category, errors in self.error_solutions.items():
                    for error_code, error_info in errors.items():
                        if error_code in line or any(keyword in line.lower() for keyword in [
                            'error', 'failed', 'exception', 'timeout', 'denied'
                        ]):
                            # Get context around the error
                            context_start = max(0, i - 3)
                            context_end = min(len(lines), i + 4)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            # Try to match specific error patterns
                            matched_error = None
                            for err_code, err_info in errors.items():
                                if err_code in line:
                                    matched_error = {
                                        'code': err_code,
                                        'category': category,
                                        'description': err_info['description'],
                                        'solution': err_info['solution'],
                                        'commands': err_info['commands'],
                                        'context': context,
                                        'line': line.strip()
                                    }
                                    break
                            
                            # Generic error if no specific match
                            if not matched_error and any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                                matched_error = {
                                    'code': 'GENERIC_ERROR',
                                    'category': 'general',
                                    'description': 'General error detected',
                                    'solution': 'Review the error context and logs for specific details. Check documentation and similar issues.',
                                    'commands': ['Review logs', 'Check documentation'],
                                    'context': context,
                                    'line': line.strip()
                                }
                            
                            if matched_error and matched_error not in found_errors:
                                found_errors.append(matched_error)
        
        return found_errors
    
    def generate_html_report(self, failed_pipelines: List[Dict[str, Any]]) -> str:
        """Generate an HTML email report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Azure Pipeline Monitoring Report - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #0078d4; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .summary {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .pipeline {{ border: 1px solid #ddd; margin-bottom: 20px; border-radius: 8px; overflow: hidden; }}
                .pipeline-header {{ background-color: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
                .pipeline-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 5px; }}
                .pipeline-info {{ color: #666; font-size: 14px; }}
                .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .error-header {{ font-weight: bold; color: #721c24; margin-bottom: 10px; }}
                .error-description {{ margin-bottom: 10px; }}
                .solution {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 3px; margin-top: 10px; }}
                .solution-title {{ font-weight: bold; color: #155724; margin-bottom: 5px; }}
                .commands {{ background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 10px; margin: 10px 0; font-family: monospace; }}
                .context {{ background-color: #f8f9fa; border: 1px solid #ddd; padding: 10px; margin: 10px 0; font-family: monospace; font-size: 12px; overflow-x: auto; }}
                .footer {{ margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; text-align: center; color: #666; }}
                .status-failed {{ color: #dc3545; font-weight: bold; }}
                .no-errors {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; text-align: center; color: #155724; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Azure Pipeline Monitoring Report</h1>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <h2>📊 Summary</h2>
                    <p><strong>Failed Pipelines Today:</strong> {len(failed_pipelines)}</p>
                    <p><strong>Organization:</strong> {self.config['azure_devops_org']}</p>
                    <p><strong>Project:</strong> {self.config['azure_devops_project']}</p>
                </div>
        """
        
        if not failed_pipelines:
            html += """
                <div class="no-errors">
                    <h2>✅ Great News!</h2>
                    <p>No failed pipelines detected today. All systems are running smoothly!</p>
                </div>
            """
        else:
            for pipeline in failed_pipelines:
                html += f"""
                <div class="pipeline">
                    <div class="pipeline-header">
                        <div class="pipeline-title">{pipeline.get('name', 'Unknown Pipeline')}</div>
                        <div class="pipeline-info">
                            <span class="status-failed">Status: {pipeline.get('state', 'Unknown')}</span> |
                            Run ID: {pipeline.get('id', 'N/A')} |
                            Started: {pipeline.get('createdDate', 'Unknown')}
                        </div>
                    </div>
                    
                    <div style="padding: 15px;">
                """
                
                if pipeline.get('errors'):
                    for error in pipeline['errors']:
                        html += f"""
                        <div class="error">
                            <div class="error-header">
                                🚨 {error['code']} ({error['category'].title()})
                            </div>
                            <div class="error-description">
                                <strong>Description:</strong> {error['description']}
                            </div>
                            <div class="error-description">
                                <strong>Error Line:</strong> <code>{error['line']}</code>
                            </div>
                            
                            <div class="solution">
                                <div class="solution-title">💡 Recommended Solution:</div>
                                <p>{error['solution']}</p>
                                
                                <div class="commands">
                                    <strong>Suggested Commands:</strong><br>
                                    {'<br>'.join([f"• {cmd}" for cmd in error['commands']])}
                                </div>
                            </div>
                            
                            <div class="context">
                                <strong>Error Context:</strong><br>
                                <pre>{error['context']}</pre>
                            </div>
                        </div>
                        """
                else:
                    html += """
                    <div class="error">
                        <div class="error-header">⚠️ Pipeline Failed</div>
                        <div class="error-description">
                            No specific error details could be extracted from the logs.
                            Please check the Azure DevOps portal for more information.
                        </div>
                    </div>
                    """
                
                html += """
                    </div>
                </div>
                """
        
        html += f"""
                <div class="footer">
                    <p>This report was generated automatically by the Azure Pipeline Monitor.</p>
                    <p>For more details, visit the <a href="https://dev.azure.com/{self.config['azure_devops_org']}/{self.config['azure_devops_project']}">Azure DevOps Portal</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_email_report(self, subject: str, html_content: str) -> bool:
        """Send HTML email report."""
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['email_user']
            msg['To'] = ', '.join(self.config['recipient_emails'])
            
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email_user'], self.config['email_password'])
                server.send_message(msg)
            
            logger.info(f"Email report sent successfully to {', '.join(self.config['recipient_emails'])}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def monitor_pipelines(self) -> None:
        """Main monitoring function."""
        logger.info("Starting Azure Pipeline monitoring...")
        
        # Get today's pipeline runs
        pipeline_runs = self.get_today_pipelines()
        logger.info(f"Found {len(pipeline_runs)} pipeline runs today")
        
        failed_pipelines = []
        
        for run in pipeline_runs:
            if run.get('state') in ['failed', 'canceled']:
                logger.info(f"Analyzing failed pipeline: {run.get('name')} (ID: {run.get('id')})")
                
                # Get detailed information
                pipeline_id = run.get('pipeline', {}).get('id')
                run_id = run.get('id')
                
                if pipeline_id and run_id:
                    # Get pipeline details
                    details = self.get_pipeline_details(pipeline_id, run_id)
                    
                    # Get and analyze logs
                    logs = self.get_pipeline_logs(pipeline_id, run_id)
                    errors = self.analyze_error(logs) if logs else []
                    
                    failed_pipeline = {
                        'name': run.get('name', 'Unknown'),
                        'id': run_id,
                        'pipeline_id': pipeline_id,
                        'state': run.get('state'),
                        'createdDate': run.get('createdDate'),
                        'finishedDate': run.get('finishedDate'),
                        'errors': errors,
                        'details': details
                    }
                    
                    failed_pipelines.append(failed_pipeline)
        
        # Generate and send report
        if failed_pipelines or self.config.get('send_success_report', False):
            subject = f"Azure Pipeline Report - {datetime.now().strftime('%Y-%m-%d')}"
            if failed_pipelines:
                subject += f" - {len(failed_pipelines)} Failed Pipeline(s)"
            else:
                subject += " - All Pipelines Successful"
            
            html_report = self.generate_html_report(failed_pipelines)
            
            if self.send_email_report(subject, html_report):
                logger.info("Monitoring completed successfully")
            else:
                logger.error("Monitoring completed but email sending failed")
        else:
            logger.info("No failed pipelines found and success reporting is disabled")

def main():
    """Main function to run the Azure Pipeline Monitor."""
    try:
        monitor = AzurePipelineMonitor()
        monitor.monitor_pipelines()
    except Exception as e:
        logger.error(f"Monitor failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Azure DevOps Pipeline Error Monitor

This script fetches Azure DevOps pipelines that have errored today and provides
possible solutions for common error patterns.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import base64
import re
from dataclasses import dataclass
from urllib.parse import quote

@dataclass
class PipelineError:
    pipeline_name: str
    pipeline_id: int
    build_id: int
    error_message: str
    error_type: str
    start_time: str
    finish_time: str
    repository: str
    branch: str
    possible_solutions: List[str]

class AzureDevOpsPipelineMonitor:
    def __init__(self, organization: str, project: str, personal_access_token: str):
        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        
        # Create authentication header
        auth_string = f":{personal_access_token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }
    
    def get_today_date_range(self) -> tuple:
        """Get start and end of today in ISO format"""
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        return start_of_day.isoformat() + "Z", end_of_day.isoformat() + "Z"
    
    def get_failed_builds_today(self) -> List[Dict[str, Any]]:
        """Fetch all failed builds from today"""
        start_time, end_time = self.get_today_date_range()
        
        # Get builds with failed status
        url = f"{self.base_url}/build/builds"
        params = {
            "statusFilter": "failed,partiallySucceeded",
            "minTime": start_time,
            "maxTime": end_time,
            "api-version": "7.0"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("value", [])
        except requests.RequestException as e:
            print(f"Error fetching builds: {e}")
            return []
    
    def get_build_logs(self, build_id: int) -> str:
        """Fetch build logs for error analysis"""
        url = f"{self.base_url}/build/builds/{build_id}/logs"
        
        try:
            response = requests.get(url, headers=self.headers, params={"api-version": "7.0"})
            response.raise_for_status()
            logs_info = response.json().get("value", [])
            
            # Get the main log (usually the last one or the one with errors)
            error_logs = []
            for log in logs_info:
                log_url = f"{self.base_url}/build/builds/{build_id}/logs/{log['id']}"
                log_response = requests.get(log_url, headers=self.headers, params={"api-version": "7.0"})
                if log_response.status_code == 200:
                    log_content = log_response.text
                    if any(keyword in log_content.lower() for keyword in ["error", "failed", "exception"]):
                        error_logs.append(log_content)
            
            return "\n".join(error_logs)
        except requests.RequestException as e:
            print(f"Error fetching logs for build {build_id}: {e}")
            return ""
    
    def analyze_error_and_suggest_solutions(self, error_log: str, build_info: Dict[str, Any]) -> tuple:
        """Analyze error patterns and suggest solutions"""
        error_patterns = {
            "authentication": {
                "patterns": [
                    r"authentication.*failed",
                    r"unauthorized",
                    r"access.*denied",
                    r"401",
                    r"403"
                ],
                "solutions": [
                    "Check if service connection credentials are valid",
                    "Verify Personal Access Token (PAT) hasn't expired",
                    "Ensure service principal has required permissions",
                    "Check if Azure subscription is active",
                    "Verify repository access permissions"
                ]
            },
            "dependency": {
                "patterns": [
                    r"package.*not found",
                    r"dependency.*failed",
                    r"npm.*error",
                    r"pip.*error",
                    r"nuget.*error",
                    r"maven.*error"
                ],
                "solutions": [
                    "Check if all dependencies are available in the package feed",
                    "Verify package versions are correct",
                    "Clear package cache and retry",
                    "Check if private feeds are accessible",
                    "Update package.json/requirements.txt/pom.xml"
                ]
            },
            "terraform": {
                "patterns": [
                    r"terraform.*error",
                    r"provider.*failed",
                    r"state.*lock",
                    r"resource.*not found",
                    r"azurerm.*error"
                ],
                "solutions": [
                    "Check Terraform state lock - may need to force unlock",
                    "Verify Azure provider version compatibility",
                    "Ensure service principal has required Azure permissions",
                    "Check if Azure resources already exist or were deleted outside Terraform",
                    "Validate Terraform syntax with 'terraform validate'",
                    "Update provider versions to latest stable"
                ]
            },
            "network": {
                "patterns": [
                    r"connection.*timeout",
                    r"network.*error",
                    r"dns.*resolution",
                    r"unable to connect",
                    r"host.*unreachable"
                ],
                "solutions": [
                    "Check network connectivity from build agent",
                    "Verify DNS resolution is working",
                    "Check firewall rules and security groups",
                    "Ensure build agent has internet access",
                    "Try using different build agent pool"
                ]
            },
            "resource": {
                "patterns": [
                    r"out of memory",
                    r"disk.*full",
                    r"quota.*exceeded",
                    r"insufficient.*resources",
                    r"timeout.*exceeded"
                ],
                "solutions": [
                    "Increase build agent memory allocation",
                    "Clean up disk space on build agents",
                    "Check Azure subscription quotas",
                    "Optimize build process to use fewer resources",
                    "Increase pipeline timeout values"
                ]
            },
            "configuration": {
                "patterns": [
                    r"configuration.*error",
                    r"invalid.*syntax",
                    r"yaml.*error",
                    r"missing.*variable",
                    r"undefined.*variable"
                ],
                "solutions": [
                    "Validate YAML syntax in pipeline files",
                    "Check if all required variables are defined",
                    "Verify variable group permissions",
                    "Ensure service connections are properly configured",
                    "Check for typos in variable names"
                ]
            }
        }
        
        error_log_lower = error_log.lower()
        detected_errors = []
        all_solutions = []
        
        for error_type, config in error_patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, error_log_lower):
                    detected_errors.append(error_type)
                    all_solutions.extend(config["solutions"])
                    break
        
        # If no specific patterns found, provide general solutions
        if not detected_errors:
            detected_errors = ["general"]
            all_solutions = [
                "Check build logs for detailed error messages",
                "Verify all prerequisites are met",
                "Try running the pipeline again",
                "Check recent changes that might have caused the issue",
                "Contact system administrator if issue persists"
            ]
        
        # Remove duplicates while preserving order
        unique_solutions = list(dict.fromkeys(all_solutions))
        
        return detected_errors[0] if detected_errors else "unknown", unique_solutions
    
    def process_failed_builds(self) -> List[PipelineError]:
        """Process all failed builds and generate error reports"""
        failed_builds = self.get_failed_builds_today()
        pipeline_errors = []
        
        for build in failed_builds:
            print(f"Processing build {build['id']} - {build['definition']['name']}")
            
            # Get build logs
            error_logs = self.get_build_logs(build['id'])
            
            # Analyze errors and get solutions
            error_type, solutions = self.analyze_error_and_suggest_solutions(error_logs, build)
            
            # Extract error message from logs (first few lines with "error")
            error_lines = [line for line in error_logs.split('\n') if 'error' in line.lower()]
            error_message = error_lines[0] if error_lines else "Build failed - check logs for details"
            
            pipeline_error = PipelineError(
                pipeline_name=build['definition']['name'],
                pipeline_id=build['definition']['id'],
                build_id=build['id'],
                error_message=error_message[:200] + "..." if len(error_message) > 200 else error_message,
                error_type=error_type,
                start_time=build.get('startTime', ''),
                finish_time=build.get('finishTime', ''),
                repository=build.get('repository', {}).get('name', 'Unknown'),
                branch=build.get('sourceBranch', 'Unknown'),
                possible_solutions=solutions
            )
            
            pipeline_errors.append(pipeline_error)
        
        return pipeline_errors
    
    def display_pipeline_errors(self, pipeline_errors: List[PipelineError]):
        """Display pipeline errors in a formatted way"""
        if not pipeline_errors:
            print("🎉 No pipeline errors found today!")
            return
        
        print(f"\n📊 Found {len(pipeline_errors)} pipeline(s) with errors today:\n")
        print("=" * 80)
        
        for i, error in enumerate(pipeline_errors, 1):
            print(f"\n{i}. 🔴 Pipeline: {error.pipeline_name}")
            print(f"   📋 Pipeline ID: {error.pipeline_id}")
            print(f"   🏗️  Build ID: {error.build_id}")
            print(f"   📁 Repository: {error.repository}")
            print(f"   🌿 Branch: {error.branch}")
            print(f"   ⏰ Start Time: {error.start_time}")
            print(f"   ⏹️  Finish Time: {error.finish_time}")
            print(f"   🏷️  Error Type: {error.error_type.title()}")
            print(f"   ❌ Error: {error.error_message}")
            
            print(f"\n   💡 Possible Solutions:")
            for j, solution in enumerate(error.possible_solutions, 1):
                print(f"      {j}. {solution}")
            
            print("\n" + "-" * 80)
        
        # Summary
        error_types = {}
        for error in pipeline_errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        print(f"\n📈 Error Summary:")
        for error_type, count in error_types.items():
            print(f"   • {error_type.title()}: {count}")

def main():
    """Main function to run the pipeline monitor"""
    # Get configuration from environment variables
    organization = os.getenv('AZURE_DEVOPS_ORG')
    project = os.getenv('AZURE_DEVOPS_PROJECT')
    pat = os.getenv('AZURE_DEVOPS_PAT')
    
    if not all([organization, project, pat]):
        print("❌ Missing required environment variables:")
        print("   - AZURE_DEVOPS_ORG: Your Azure DevOps organization name")
        print("   - AZURE_DEVOPS_PROJECT: Your project name")
        print("   - AZURE_DEVOPS_PAT: Personal Access Token with Build (read) permissions")
        print("\nExample:")
        print("   export AZURE_DEVOPS_ORG='myorg'")
        print("   export AZURE_DEVOPS_PROJECT='myproject'")
        print("   export AZURE_DEVOPS_PAT='your-pat-token'")
        sys.exit(1)
    
    print(f"🔍 Checking Azure DevOps pipelines for organization: {organization}")
    print(f"📁 Project: {project}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    monitor = AzureDevOpsPipelineMonitor(organization, project, pat)
    
    try:
        pipeline_errors = monitor.process_failed_builds()
        monitor.display_pipeline_errors(pipeline_errors)
        
        # Generate JSON report for automation
        json_report = {
            "date": datetime.now().isoformat(),
            "organization": organization,
            "project": project,
            "total_errors": len(pipeline_errors),
            "errors": [
                {
                    "pipeline_name": error.pipeline_name,
                    "pipeline_id": error.pipeline_id,
                    "build_id": error.build_id,
                    "error_type": error.error_type,
                    "error_message": error.error_message,
                    "repository": error.repository,
                    "branch": error.branch,
                    "start_time": error.start_time,
                    "finish_time": error.finish_time,
                    "solutions": error.possible_solutions
                }
                for error in pipeline_errors
            ]
        }
        
        with open(f"pipeline_errors_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
            json.dump(json_report, f, indent=2)
        
        print(f"\n📄 JSON report saved to: pipeline_errors_{datetime.now().strftime('%Y%m%d')}.json")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
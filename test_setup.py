#!/usr/bin/env python3
"""
Test script to validate Azure Pipeline Monitor setup
"""

import json
import sys
import importlib.util
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are available."""
    print("🔍 Testing dependencies...")
    
    required_modules = ['requests', 'json', 'smtplib', 'base64', 'datetime']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  ❌ {module}")
    
    if missing_modules:
        print(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True

def test_config_file():
    """Test if configuration file exists and is valid."""
    print("\n🔍 Testing configuration...")
    
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ config.json not found")
        print("Run: cp config.json.template config.json")
        print("Then edit config.json with your settings")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_keys = [
            'azure_devops_org', 'azure_devops_project', 'azure_devops_pat',
            'smtp_server', 'smtp_port', 'email_user', 'email_password',
            'recipient_emails'
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)
            elif isinstance(config[key], str) and config[key].startswith('your-'):
                print(f"  ⚠️  {key}: needs to be configured (still has placeholder value)")
            else:
                print(f"  ✅ {key}")
        
        if missing_keys:
            print(f"\n❌ Missing configuration keys: {', '.join(missing_keys)}")
            return False
        
        # Check if values are still placeholders
        placeholder_values = [
            'your-organization-name', 'your-project-name', 'your-personal-access-token',
            'your-email@gmail.com', 'your-app-password'
        ]
        
        has_placeholders = False
        for key, value in config.items():
            if isinstance(value, str) and value in placeholder_values:
                print(f"  ⚠️  {key}: still has placeholder value")
                has_placeholders = True
        
        if has_placeholders:
            print("\n⚠️  Configuration has placeholder values. Please update config.json")
            return False
        
        print("✅ Configuration file is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return False

def test_main_script():
    """Test if the main script can be imported."""
    print("\n🔍 Testing main script...")
    
    script_path = Path('azure_pipeline_monitor.py')
    if not script_path.exists():
        print("❌ azure_pipeline_monitor.py not found")
        return False
    
    try:
        # Try to import the main module
        spec = importlib.util.spec_from_file_location("azure_pipeline_monitor", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if main class exists
        if hasattr(module, 'AzurePipelineMonitor'):
            print("  ✅ AzurePipelineMonitor class found")
        else:
            print("  ❌ AzurePipelineMonitor class not found")
            return False
        
        print("✅ Main script is importable")
        return True
        
    except Exception as e:
        print(f"❌ Error importing main script: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Azure Pipeline Monitor Setup Test\n")
    
    tests = [
        test_dependencies,
        test_config_file,
        test_main_script
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*50)
    
    if all(results):
        print("🎉 All tests passed! The setup is ready.")
        print("\nNext steps:")
        print("1. Run the monitor: ./azure_pipeline_monitor.py")
        print("2. Check the logs: tail -f azure_pipeline_monitor.log")
        print("3. Set up automated monitoring with cron")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
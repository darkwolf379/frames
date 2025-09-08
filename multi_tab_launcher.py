#!/usr/bin/env python3
"""
Farcaster Multi-Tab CMD Launcher
Automatically launches multiple CMD tabs with individual tokens
"""

import os
import sys
import time
import subprocess
import toml
from pathlib import Path

def load_config(config_path="config.toml"):
    """Load configuration from TOML file"""
    try:
        if not os.path.exists(config_path):
            print(f"❌ Config file {config_path} not found!")
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        print(f"✅ Loaded configuration from {config_path}")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def load_tokens(file_path="account.txt"):
    """Load tokens from account.txt"""
    try:
        tokens = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    token = line.strip()
                    if token and not token.startswith('#'):
                        tokens.append(token)
        
        if tokens:
            print(f"✅ Loaded {len(tokens)} token(s) from {file_path}")
            return tokens
        else:
            print(f"❌ No valid tokens found in {file_path}")
            return []
    except Exception as e:
        print(f"❌ Error loading tokens: {e}")
        return []

def create_single_account_file(token, account_index, temp_dir="temp_accounts"):
    """Create temporary account.txt file for single account"""
    try:
        # Create temp directory if not exists
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Create account file for this specific account
        account_file = os.path.join(temp_dir, f"account_{account_index}.txt")
        
        with open(account_file, 'w', encoding='utf-8') as f:
            f.write(token)
        
        return account_file
    except Exception as e:
        print(f"❌ Error creating account file for account {account_index}: {e}")
        return None

def create_launcher_script(config, account_index, account_file):
    """Create Python launcher script for single account"""
    script_content = f'''#!/usr/bin/env python3
"""
Auto-generated launcher for Account {account_index}
"""

import os
import sys
import time
import json
from pathlib import Path

# Change to the correct directory
os.chdir(r"{os.getcwd()}")

# Import the main script
try:
    from farcaster_auto_share_like import *
    print("✅ Successfully imported farcaster_auto_share_like")
except ImportError as e:
    print(f"❌ Import error: {{e}}")
    input("Press Enter to exit...")
    sys.exit(1)

def load_single_token():
    """Load token for this account"""
    try:
        with open(r"{account_file}", 'r', encoding='utf-8') as f:
            token = f.read().strip()
        return token
    except Exception as e:
        print(f"❌ Error loading token: {{e}}")
        return None

def main():
    """Main launcher function"""
    # Configuration from TOML
    config = {{
        "mode": "{config['general']['mode']}",
        "save_links": {config['general']['save_links']},
        "use_original_only": {config['general']['use_original_only']},
        "num_shares": {config['sharing']['num_shares']},
        "share_delay_range": ({config['sharing']['share_delay_min']}, {config['sharing']['share_delay_max']}),
        "like_delay_range": ({config['liking']['like_delay_min']}, {config['liking']['like_delay_max']}),
        "cycle_delay": {config['cycle']['cycle_delay_minutes'] * 60},
        "max_wait_minutes": {config['cycle']['max_wait_minutes']},
        "check_fuel": {config['advanced']['check_fuel']},
        "test_accounts": {config['advanced']['test_accounts']},
        "debug_mode": {config['advanced']['debug_mode']}
    }}
    
    print(f"🚀 ACCOUNT {account_index} - FARCASTER AUTO SHARE + LIKE")
    print(f"{'='*60}")
    
    # Load token
    token = load_single_token()
    if not token:
        print("❌ Failed to load token!")
        input("Press Enter to exit...")
        return
    
    # Create account info
    account_info = [{{'index': {account_index}, 'token': token}}]
    
    try:
        # Initialize bot to get user info
        print(f"🔍 Initializing Account {account_index}...")
        bot = FarcasterAutoShareLike(token, {account_index}, config["save_links"])
        
        if not bot.user_id:
            print(f"❌ Account {account_index}: Failed to detect user info!")
            input("Press Enter to exit...")
            return
        
        print(f"✅ Account {account_index}: @{{bot.username}} (ID: {{bot.user_id}})")
        
        # Check fuel if enabled
        if config["check_fuel"]:
            print(f"⛽ Checking fuel status...")
            fuel = bot.check_fuel_status()
            print(f"💰 Current fuel: {{fuel}}")
        
        # Show configuration
        print(f"\\n📋 CONFIGURATION:")
        print(f"   Mode: {{config['mode']}}")
        print(f"   Save links: {{config['save_links']}}")
        print(f"   Original text only: {{config['use_original_only']}}")
        print(f"   Shares per cycle: {{config['num_shares']}}")
        print(f"   Share delay: {{config['share_delay_range'][0]}}-{{config['share_delay_range'][1]}}s")
        print(f"   Like delay: {{config['like_delay_range'][0]}}-{{config['like_delay_range'][1]}}s")
        if config['mode'] == 'infinite':
            print(f"   Cycle delay: {{config['cycle_delay']//60}} minutes")
        
        # Start automation based on mode
        if config['mode'] == 'single':
            print(f"\\n🚀 Starting single share + like process...")
            threaded_share_like_process(
                account_info, 
                config['num_shares'], 
                config['share_delay_range'], 
                config['like_delay_range'], 
                config['use_original_only'], 
                config['save_links']
            )
        elif config['mode'] == 'infinite':
            print(f"\\n🔄 Starting infinite cycle automation...")
            print(f"⛔ Press Ctrl+C to stop anytime")
            cycle_based_share_like_automation(
                account_info,
                config['num_shares'],
                config['share_delay_range'], 
                config['like_delay_range'],
                999,  # Infinite cycles
                config['cycle_delay'],
                config['use_original_only'],
                config['save_links']
            )
        
    except KeyboardInterrupt:
        print(f"\\n⛔ Account {account_index}: Stopped by user")
    except Exception as e:
        print(f"\\n❌ Account {account_index}: Error - {{e}}")
        if config["debug_mode"]:
            import traceback
            traceback.print_exc()
    finally:
        print(f"\\n🏁 Account {account_index}: Session ended")
        input("Press Enter to close this window...")

if __name__ == "__main__":
    main()
'''
    
    # Save launcher script
    launcher_file = f"temp_accounts/launcher_account_{account_index}.py"
    
    try:
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return launcher_file
    except Exception as e:
        print(f"❌ Error creating launcher script for account {account_index}: {e}")
        return None

def create_batch_launcher(account_index, temp_dir="temp_accounts"):
    """Create batch launcher for account"""
    try:
        # Read template
        with open("account_launcher_template.bat", 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Create account-specific batch file
        batch_file = os.path.join(temp_dir, f"launch_account_{account_index}.bat")
        
        # Replace placeholder with account number
        batch_content = template.replace("%1", str(account_index))
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        return batch_file
    except Exception as e:
        print(f"❌ Error creating batch launcher for account {account_index}: {e}")
        return None

def launch_cmd_tab(launcher_script, account_index, config):
    """Launch CMD tab for specific account"""
    try:
        # Create batch launcher
        batch_file = create_batch_launcher(account_index)
        if not batch_file:
            return None
        
        # Convert to absolute path
        abs_batch_file = os.path.abspath(batch_file)
        
        # Create CMD command to start new window
        cmd_command = f'start "Farcaster Account {account_index}" "{abs_batch_file}"'
        
        print(f"🔧 CMD Command: {cmd_command}")
        
        # Start the process
        process = subprocess.Popen(cmd_command, shell=True, cwd=os.getcwd())
        
        # Wait a moment to ensure process starts
        time.sleep(2)
        
        print(f"✅ Launched CMD tab for Account {account_index} (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error launching CMD tab for account {account_index}: {e}")
        return None

def show_config_summary(config):
    """Show configuration summary"""
    print(f"📋 CONFIGURATION SUMMARY")
    print(f"{'='*60}")
    print(f"Mode: {config['general']['mode']}")
    print(f"Save links: {config['general']['save_links']}")
    print(f"Original text only: {config['general']['use_original_only']}")
    print(f"Shares per cycle: {config['sharing']['num_shares']}")
    print(f"Share delay: {config['sharing']['share_delay_min']}-{config['sharing']['share_delay_max']}s")
    print(f"Like delay: {config['liking']['like_delay_min']}-{config['liking']['like_delay_max']}s")
    if config['general']['mode'] == 'infinite':
        print(f"Cycle delay: {config['cycle']['cycle_delay_minutes']} minutes")
    print(f"Auto start: {config['multitab']['auto_start']}")
    print(f"Tab start delay: {config['multitab']['tab_start_delay']}s")
    print(f"Window size: {config['multitab']['window_width']}x{config['multitab']['window_height']}")
    print(f"CMD color: {config['multitab']['cmd_color']}")
    print(f"{'='*60}")

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        temp_dir = "temp_accounts"
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary files")
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up temp files: {e}")

def check_template_file():
    """Check if template batch file exists"""
    template_file = "account_launcher_template.bat"
    if not os.path.exists(template_file):
        print(f"❌ Template file {template_file} not found!")
        print("Please make sure account_launcher_template.bat exists in the current directory.")
        return False
    return True

def main():
    """Main multi-tab launcher"""
    print(f"🚀 FARCASTER MULTI-TAB CMD LAUNCHER")
    print(f"{'='*60}")
    
    # Check template file
    if not check_template_file():
        input("Press Enter to exit...")
        return
    
    # Load configuration
    config = load_config()
    if not config:
        input("Press Enter to exit...")
        return
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        input("Press Enter to exit...")
        return
    
    # Show configuration summary
    show_config_summary(config)
    
    print(f"\\n👥 Found {len(tokens)} account(s) to launch")
    
    # Ask for confirmation if not auto start
    if not config['multitab']['auto_start']:
        confirm = input("\\nStart all CMD tabs? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '']:
            print("❌ Cancelled by user")
            return
    
    # Clean up any existing temp files
    cleanup_temp_files()
    
    # Create temp directory
    if not os.path.exists("temp_accounts"):
        os.makedirs("temp_accounts")
    
    launched_processes = []
    
    try:
        for i, token in enumerate(tokens, 1):
            print(f"\\n🔧 Setting up Account {i}...")
            
            # Create account file
            account_file = create_single_account_file(token, i)
            if not account_file:
                print(f"❌ Failed to create account file for Account {i}")
                continue
            
            # Create launcher script
            launcher_script = create_launcher_script(config, i, account_file)
            if not launcher_script:
                print(f"❌ Failed to create launcher script for Account {i}")
                continue
            
            # Launch CMD tab
            process = launch_cmd_tab(launcher_script, i, config)
            if process:
                launched_processes.append(process)
            
            # Delay between launches
            if i < len(tokens):
                delay = config['multitab']['tab_start_delay']
                print(f"⏳ Waiting {delay}s before launching next tab...")
                time.sleep(delay)
        
        print(f"\\n✅ Successfully launched {len(launched_processes)} CMD tab(s)!")
        print(f"\\n📋 INSTRUCTIONS:")
        print(f"  • Each CMD tab runs independently")
        print(f"  • All tabs share the same link_hash.json for coordination")
        print(f"  • Press Ctrl+C in any tab to stop that specific account")
        print(f"  • Close CMD windows or press Ctrl+C here to exit launcher")
        
        # Wait for user input to keep launcher alive
        print(f"\\n🎮 LAUNCHER CONTROLS:")
        print(f"  • Press Enter to clean exit launcher")
        print(f"  • Press Ctrl+C for force exit")
        
        input("\\nPress Enter to exit launcher (CMD tabs will continue running)...")
        
    except KeyboardInterrupt:
        print(f"\\n⛔ Launcher stopped by user")
    except Exception as e:
        print(f"\\n❌ Launcher error: {e}")
    finally:
        print(f"\\n🏁 Multi-tab launcher finished")
        print(f"💡 CMD tabs are still running independently")
        print(f"🧹 Temporary files will be cleaned up")
        
        # Clean up temp files
        time.sleep(2)
        cleanup_temp_files()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
🚀 FARCASTER AUTO ADD WRECK LEAGUE MINIAPPS
Multi-account automation untuk menambahkan Wreck League Versus ke favorite miniapps
Powered by anti-detection system dengan proxy & rate limiting

Author: AI Assistant
Version: 1.0.0
Features:
- ✅ Multi-account aut      try:
        print(f"\n{colored_text('🚀 STARTING WRECK LEAGUE MINIAPPS ADD PROCESS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        print(f"{colored_text('🎯 Target: Add Wreck League Versus (versus.wreckleague.xyz) to favorites', Colors.MAGENTA)}")
        print(f"{colored_text(f'🧵 Processing {len(all_tokens_data)} accounts...', Colors.MAGENTA)}") print(f"{colored_text('🚀 STARTING WRECK LEAGUE MINIAPPS ADD PROCESS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        print(f"{colored_text('🎯 Target: Add Wreck League Versus (versus.wreckleague.xyz) to favorites', Colors.MAGENTA)}")
        print(f"{colored_text(f'🧵 Processing {len(all_tokens_data)} accounts...', Colors.MAGENTA)}")ion
- ✅ Auto detect yang belum ada Wreck League
- ✅ Anti-detection system dengan proxy
- ✅ Rate limiting & random delays
- ✅ Comprehensive logging
"""

import requests
import random
import time
import uuid
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from anti_detection import AntiDetectionManager, create_anti_detection_session, make_stealth_request

# Color codes untuk output terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\033[97m'
    MAGENTA = '\033[95m'
    END = '\033[0m'

def colored_text(text, color):
    """Add color to text"""
    return f"{color}{text}{Colors.END}"

def load_authorization_tokens():
    """Load authorization tokens from account.txt"""
    try:
        tokens = []
        account_file = "account.txt"
        
        if not os.path.exists(account_file):
            print(f"{colored_text('❌ File account.txt tidak ditemukan!', Colors.RED)}")
            return tokens
            
        with open(account_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # Format: account_name:authorization_token atau hanya authorization_token
                if ':' in line:
                    account_name, auth_token = line.split(':', 1)
                    tokens.append({
                        'account_name': account_name.strip(),
                        'authorization': auth_token.strip(),
                        'account_index': i
                    })
                elif line.startswith('MK-'):
                    # Hanya token tanpa nama akun
                    tokens.append({
                        'account_name': f'account_{i}',
                        'authorization': line.strip(),
                        'account_index': i
                    })
                else:
                    print(f"{colored_text(f'⚠️ Baris {i} format salah: {line}', Colors.YELLOW)}")
                    
        print(f"{colored_text(f'✅ Loaded {len(tokens)} authorization token(s)', Colors.GREEN)}")
        return tokens
        
    except Exception as e:
        print(f"{colored_text(f'❌ Error loading tokens: {e}', Colors.RED)}")
        return []

class FarcasterWreckBot:
    def __init__(self, account_name, authorization_token, account_index):
        self.account_name = account_name
        self.authorization_token = authorization_token
        self.account_index = account_index
        self.user_id = None
        self.username = None
        self.display_name = None
        
        # Anti-detection
        self.stealth_session = create_anti_detection_session(account_index, authorization_token)
        
        # Wreck League domain
        self.wreck_domain = "versus.wreckleague.xyz"
        
        # Statistics
        self.already_has_wreck = False
        self.add_success = False
        self.add_failed = False
        
    def make_request(self, method, url, **kwargs):
        """Make HTTP request using anti-detection"""
        return make_stealth_request(self.stealth_session, method, url, self.authorization_token, **kwargs)
    
    def get_user_info(self):
        """Get user info untuk mendapatkan FID dan username"""
        try:
            url = "https://client.warpcast.com/v2/me"
            
            # Custom headers without compression
            headers = {
                'Authorization': f'Bearer {self.authorization_token}',
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json',
                'Accept-Encoding': 'identity',  # Disable compression
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = make_stealth_request(
                self.stealth_session, 
                'GET', 
                url, 
                self.authorization_token,
                api_type="farcaster",
                headers=headers
            )
            
            print(f"🔍 Account {self.account_index}: Response status {response.status_code}")
            
            if response.status_code == 200:
                # Check if response has content
                if not response.content:
                    print(f"{colored_text(f'❌ Account {self.account_index}: Empty response content', Colors.RED)}")
                    return False
                
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"{colored_text(f'❌ Account {self.account_index}: JSON decode error: {e}', Colors.RED)}")
                    print(f"Raw content: {response.content[:200]}...")
                    return False
                
                user_data = data.get('result', {}).get('user', {})
                
                self.user_id = user_data.get('fid')
                self.username = user_data.get('username', 'Unknown')
                self.display_name = user_data.get('displayName', 'Unknown')
                
                print(f"{colored_text(f'✅ Account {self.account_index}: @{self.username} (FID: {self.user_id})', Colors.GREEN)}")
                return True
            else:
                print(f"{colored_text(f'❌ Account {self.account_index}: Failed to get user info (Status: {response.status_code})', Colors.RED)}")
                print(f"Response content: {response.content[:200]}...")
                return False
                
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error getting user info: {e}', Colors.RED)}")
            return False
    
    def check_if_has_wreck_favorite(self):
        """Check if user already has Wreck League in favorites"""
        try:
            url = "https://client.farcaster.xyz/v1/favorite-frames?limit=50"
            
            # Custom headers without compression
            headers = {
                'Authorization': f'Bearer {self.authorization_token}',
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json',
                'Accept-Encoding': 'identity',  # Disable compression
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = make_stealth_request(
                self.stealth_session, 
                'GET', 
                url, 
                self.authorization_token,
                api_type="farcaster",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                favorite_frames = data.get('result', {}).get('favoriteFrames', [])
                
                for frame in favorite_frames:
                    domain = frame.get('domain', '')
                    if domain == self.wreck_domain:
                        self.already_has_wreck = True
                        print(f"{colored_text(f'⏭️  Account {self.account_index}: Already has Wreck League in favorites', Colors.YELLOW)}")
                        return True
                
                print(f"{colored_text(f'🎯 Account {self.account_index}: Wreck League not in favorites, will add it', Colors.CYAN)}")
                return False
            else:
                print(f"{colored_text(f'⚠️ Account {self.account_index}: Failed to check favorites (Status: {response.status_code})', Colors.YELLOW)}")
                return False
                
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error checking favorites: {e}', Colors.RED)}")
            return False
    
    def add_wreck_to_favorites(self):
        """Add Wreck League Versus to favorite miniapps"""
        try:
            url = "https://client.farcaster.xyz/v1/favorite-frames"
            
            payload = {
                "domain": self.wreck_domain
            }
            
            # Custom headers without compression
            headers = {
                'Authorization': f'Bearer {self.authorization_token}',
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json',
                'Accept-Encoding': 'identity',  # Disable compression
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"{colored_text(f'🚀 Account {self.account_index}: Adding Wreck League to favorites...', Colors.CYAN)}")
            
            response = make_stealth_request(
                self.stealth_session,
                'PUT', 
                url, 
                self.authorization_token,
                api_type="farcaster",
                headers=headers,
                json=payload
            )
            
            print(f"{colored_text(f'📋 Add response: Status {response.status_code}', Colors.WHITE)}")
            
            if response.status_code in [200, 201]:
                self.add_success = True
                print(f"{colored_text(f'✅ Account {self.account_index}: Successfully added Wreck League to favorites!', Colors.GREEN)}")
                return True
            else:
                self.add_failed = True
                try:
                    error_data = response.json()
                    print(f"{colored_text(f'❌ Account {self.account_index}: Failed to add Wreck League (Status: {response.status_code})', Colors.RED)}")
                    print(f"{colored_text(f'   Error details: {error_data}', Colors.RED)}")
                except:
                    print(f"{colored_text(f'❌ Account {self.account_index}: Failed to add Wreck League (Status: {response.status_code}) - No JSON response', Colors.RED)}")
                return False
                
        except Exception as e:
            self.add_failed = True
            print(f"{colored_text(f'❌ Account {self.account_index}: Error adding Wreck League: {e}', Colors.RED)}")
            return False

def process_account_wreck_add(token_data, results_queue):
    """Process single account for adding Wreck League"""
    try:
        account_index = token_data['account_index']
        print(f"{colored_text(f'🔄 [Thread-{account_index}] Starting Wreck League add process...', Colors.CYAN)}")
        
        # Initialize bot
        bot = FarcasterWreckBot(
            token_data['account_name'],
            token_data['authorization'],
            account_index
        )
        
        # Get user info
        if not bot.get_user_info():
            results_queue.put({
                'account_index': account_index,
                'account_name': token_data['account_name'],
                'success': False,
                'error': 'Failed to get user info',
                'already_has_wreck': False,
                'add_success': False
            })
            return
        
        # Check if already has Wreck League
        has_wreck = bot.check_if_has_wreck_favorite()
        
        if has_wreck:
            # Already has Wreck League
            results_queue.put({
                'account_index': account_index,
                'account_name': token_data['account_name'],
                'username': bot.username,
                'success': True,
                'already_has_wreck': True,
                'add_success': False,
                'skipped': True
            })
        else:
            # Add random delay before adding
            delay = random.uniform(2, 5)
            print(f"{colored_text(f'⏳ Account {account_index}: Waiting {delay:.1f}s before adding...', Colors.CYAN)}")
            time.sleep(delay)
            
            # Add Wreck League to favorites
            add_success = bot.add_wreck_to_favorites()
            
            results_queue.put({
                'account_index': account_index,
                'account_name': token_data['account_name'],
                'username': bot.username,
                'success': True,
                'already_has_wreck': False,
                'add_success': add_success,
                'add_failed': bot.add_failed,
                'skipped': False
            })
        
        print(f"{colored_text(f'✅ [Thread-{account_index}] Wreck League add process completed', Colors.GREEN)}")
        
    except Exception as e:
        print(f"{colored_text(f'❌ [Thread-{account_index}] Error in Wreck add process: {e}', Colors.RED)}")
        results_queue.put({
            'account_index': account_index,
            'account_name': token_data.get('account_name', 'Unknown'),
            'success': False,
            'error': str(e),
            'already_has_wreck': False,
            'add_success': False
        })

def threaded_wreck_add_process(all_tokens_data):
    """Main threaded process for adding Wreck League to all accounts"""
    try:
        print(f"\n{colored_text('🚀 STARTING WRECK LEAGUE MINIAPPS ADD PROCESS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        print(f"{colored_text('🎯 Target: Add Wreck League Versus (versus.wreckleague.xyz) to favorites', Colors.MAGENTA)}")
        print(f"{colored_text(f'🧵 Processing {len(all_tokens_data)} accounts...', Colors.MAGENTA)}")
        
        results_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=min(len(all_tokens_data), 3)) as executor:
            # Submit tasks
            futures = []
            for token_data in all_tokens_data:
                future = executor.submit(process_account_wreck_add, token_data, results_queue)
                futures.append(future)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{colored_text(f'❌ Thread error: {e}', Colors.RED)}")
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Summary
        total_accounts = len(results)
        successful_accounts = len([r for r in results if r.get('success', False)])
        already_has_wreck = len([r for r in results if r.get('already_has_wreck', False)])
        successfully_added = len([r for r in results if r.get('add_success', False)])
        failed_to_add = len([r for r in results if r.get('add_failed', False)])
        
        print(f"\n{colored_text('📊 WRECK LEAGUE MINIAPPS ADD SUMMARY', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('┌──────────────────────────────────────────────────────────┐', Colors.GREEN)}")
        print(f"{colored_text('│                WRECK LEAGUE ADD RESULTS                 │', Colors.GREEN)}")
        print(f"{colored_text('├──────────────────────────────────────────────────────────┤', Colors.GREEN)}")
        print(f"{colored_text(f'│ 🎯 Target miniapp: Wreck League Versus                   │', Colors.GREEN)}")
        print(f"{colored_text(f'│ 👥 Total accounts processed: {total_accounts:<27} │', Colors.GREEN)}")
        print(f"{colored_text(f'│ ✅ Successful accounts: {successful_accounts:<32} │', Colors.GREEN)}")
        print(f"{colored_text(f'│ ⏭️  Already had Wreck League: {already_has_wreck:<25} │', Colors.GREEN)}")
        print(f"{colored_text(f'│ 🚀 Successfully added: {successfully_added:<32} │', Colors.GREEN)}")
        print(f"{colored_text(f'│ ❌ Failed to add: {failed_to_add:<37} │', Colors.GREEN)}")
        print(f"{colored_text('└──────────────────────────────────────────────────────────┘', Colors.GREEN)}")
        
        # Individual account summary
        print(f"\n{colored_text('👤 INDIVIDUAL ACCOUNT SUMMARY', Colors.BOLD + Colors.CYAN)}")
        for result in results:
            account_name = result.get('account_name', 'Unknown')
            username = result.get('username', 'Unknown')
            account_index = result.get('account_index', 0)
            
            if result.get('success', False):
                if result.get('already_has_wreck', False):
                    print(f"{colored_text(f'Account {account_index} (@{username}):', Colors.CYAN)}")
                    print(f"  ⏭️  Already had Wreck League in favorites")
                elif result.get('add_success', False):
                    print(f"{colored_text(f'Account {account_index} (@{username}):', Colors.CYAN)}")
                    print(f"  🚀 Successfully added Wreck League to favorites")
                elif result.get('add_failed', False):
                    print(f"{colored_text(f'Account {account_index} (@{username}):', Colors.CYAN)}")
                    print(f"  ❌ Failed to add Wreck League")
            else:
                error = result.get('error', 'Unknown error')
                print(f"{colored_text(f'Account {account_index} ({account_name}):', Colors.CYAN)}")
                print(f"  ❌ Error: {error}")
        
        print(f"\n{colored_text('🎉 WRECK LEAGUE MINIAPPS ADD AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    except Exception as e:
        print(f"{colored_text(f'❌ Error in threaded Wreck add process: {e}', Colors.RED)}")

def main():
    """Main function"""
    try:
        print(f"{colored_text('🚀 FARCASTER AUTO ADD WRECK LEAGUE MINIAPPS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        print(f"{colored_text('Multi-account automation untuk menambahkan Wreck League Versus', Colors.WHITE)}")
        print(f"{colored_text('ke favorite miniapps untuk semua akun yang belum ada', Colors.WHITE)}")
        print()
        
        # Load authorization tokens
        print(f"{colored_text('📄 Loading authorization tokens...', Colors.CYAN)}")
        tokens_data = load_authorization_tokens()
        
        if not tokens_data:
            print(f"{colored_text('❌ No valid tokens found!', Colors.RED)}")
            return
        
        print(f"{colored_text(f'✅ Successfully loaded {len(tokens_data)} account(s)', Colors.GREEN)}")
        print()
        
        # Confirm action
        print(f"{colored_text('⚙️  WRECK LEAGUE MINIAPPS ADD CONFIGURATION', Colors.BOLD + Colors.YELLOW)}")
        print(f"{colored_text('🎯 Target: Wreck League Versus (versus.wreckleague.xyz)', Colors.MAGENTA)}")
        print(f"{colored_text(f'👥 Accounts to process: {len(tokens_data)}', Colors.MAGENTA)}")
        print(f"{colored_text('📊 Process: Check if already has Wreck League, add if not', Colors.MAGENTA)}")
        print(f"{colored_text('🛡️ Anti-detection: Enabled with proxy & rate limiting', Colors.MAGENTA)}")
        print()
        
        confirm = input(f"{colored_text('Do you want to proceed with adding Wreck League to all accounts? (y/n): ', Colors.YELLOW)}")
        
        if confirm.lower() != 'y':
            print(f"{colored_text('❌ Operation cancelled by user', Colors.YELLOW)}")
            return
        
        # Start the process
        threaded_wreck_add_process(tokens_data)
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⚠️ Process interrupted by user', Colors.YELLOW)}")
    except Exception as e:
        print(f"{colored_text(f'❌ Unexpected error: {e}', Colors.RED)}")

if __name__ == "__main__":
    main()

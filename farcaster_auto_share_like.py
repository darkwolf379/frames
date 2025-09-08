#!/usr/bin/env python3
"""
Farcaster Auto Share + Like Script - Advanced Multi-Account Edition with Anti-Detection
Script untuk otomatisasi share cast dan saling like antar account dengan sistem anti-deteksi
"""

import requests
import json
import time
import random
import threading
import uuid
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import queue

# Import anti-detection system
try:
    from anti_detection import create_anti_detection_session, make_stealth_request, get_anti_detection_stats
    ANTI_DETECTION_AVAILABLE = True
    print("🛡️ Anti-Detection System: ENABLED")
except ImportError:
    ANTI_DETECTION_AVAILABLE = False
    print("⚠️ Anti-Detection System: DISABLED (anti_detection.py not found)")

def save_link_hash(cast_data, cycle=None):
    """Save cast link hash to link_hash.json"""
    try:
        link_hash_file = "link_hash.json"
        
        # Load existing data
        if os.path.exists(link_hash_file):
            with open(link_hash_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        
        # Create new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "account_index": cast_data.get('account_index'),
            "username": cast_data.get('username'),
            "user_id": cast_data.get('user_id'),
            "cast_hash": cast_data.get('cast_hash'),
            "share_number": cast_data.get('share_number'),
            "cycle": cycle if cycle is not None else "single"
        }
        
        data.append(entry)
        
        # Save back to file
        with open(link_hash_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"{colored_text(f'💾 Saved link hash to {link_hash_file}', Colors.GREEN)}")
        return True
        
    except Exception as e:
        print(f"{colored_text(f'❌ Failed to save link hash: {e}', Colors.RED)}")
        return False

def load_link_hashes():
    """Load all saved link hashes"""
    try:
        link_hash_file = "link_hash.json"
        if os.path.exists(link_hash_file):
            with open(link_hash_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"{colored_text(f'❌ Failed to load link hashes: {e}', Colors.RED)}")
        return []

def check_cycle_completion(cycle, expected_accounts, expected_shares_per_account=3):
    """Check if all accounts have completed ALL their shares for a specific cycle"""
    try:
        link_hashes = load_link_hashes()
        cycle_shares = [h for h in link_hashes if h.get('cycle') == cycle]
        
        # Count shares per account for this cycle
        shares_per_account = {}
        for share in cycle_shares:
            account_idx = share.get('account_index')
            if account_idx:
                shares_per_account[account_idx] = shares_per_account.get(account_idx, 0) + 1
        
        # Check if ALL accounts have completed ALL their shares
        accounts_completed = 0
        total_shares_found = len(cycle_shares)
        expected_total_shares = expected_accounts * expected_shares_per_account
        
        for acc_idx in range(1, expected_accounts + 1):
            shares_count = shares_per_account.get(acc_idx, 0)
            if shares_count >= expected_shares_per_account:
                accounts_completed += 1
        
        # Only complete if ALL accounts have posted ALL their shares
        completed = (accounts_completed >= expected_accounts and 
                    total_shares_found >= expected_total_shares)
        
        # Show detailed progress
        if cycle_shares:
            print(f"{colored_text(f'🔍 Cycle {cycle} progress: {accounts_completed}/{expected_accounts} accounts fully completed', Colors.CYAN)}")
            print(f"{colored_text(f'📊 Total shares: {total_shares_found}/{expected_total_shares}', Colors.CYAN)}")
            
            # Show progress per account
            for acc_idx in range(1, expected_accounts + 1):
                shares_count = shares_per_account.get(acc_idx, 0)
                status = "✅" if shares_count >= expected_shares_per_account else "⏳"
                print(f"{colored_text(f'  {status} Account {acc_idx}: {shares_count}/{expected_shares_per_account} shares', Colors.CYAN)}")
            
            if not completed:
                incomplete_accounts = []
                for acc_idx in range(1, expected_accounts + 1):
                    if shares_per_account.get(acc_idx, 0) < expected_shares_per_account:
                        incomplete_accounts.append(acc_idx)
                if incomplete_accounts:
                    print(f"{colored_text(f'⏳ Waiting for accounts {incomplete_accounts} to complete all shares...', Colors.YELLOW)}")
        else:
            print(f"{colored_text(f'🔍 Cycle {cycle} check: 0/{expected_total_shares} total shares found', Colors.YELLOW)}")
        
        return completed, accounts_completed
        
    except Exception as e:
        print(f"{colored_text(f'❌ Error checking cycle completion: {e}', Colors.RED)}")
        return False, 0

def wait_for_cycle_completion(cycle, expected_accounts, expected_shares_per_account=3, max_wait_minutes=10):
    """Wait for all accounts to complete ALL their shares for a cycle"""
    try:
        max_wait_seconds = max_wait_minutes * 60
        start_time = time.time()
        check_interval = 5  # Check every 5 seconds
        expected_total_shares = expected_accounts * expected_shares_per_account
        
        print(f"\n{colored_text(f'⏳ Waiting for all {expected_accounts} accounts to complete Cycle {cycle} shares...', Colors.YELLOW)}")
        print(f"{colored_text(f'📋 Expected: {expected_total_shares} total shares ({expected_shares_per_account} per account)', Colors.CYAN)}")
        print(f"{colored_text(f'📋 Max wait time: {max_wait_minutes} minutes', Colors.CYAN)}")
        
        while time.time() - start_time < max_wait_seconds:
            completed, accounts_done = check_cycle_completion(cycle, expected_accounts, expected_shares_per_account)
            
            if completed:
                print(f"\n{colored_text(f'✅ All {expected_accounts} accounts completed ALL shares for Cycle {cycle}!', Colors.GREEN)}")
                return True
            
            # Show progress
            elapsed = int(time.time() - start_time)
            remaining = max_wait_seconds - elapsed
            print(f"{colored_text(f'⏰ Progress: {accounts_done}/{expected_accounts} accounts | Waiting {remaining}s...', Colors.YELLOW)}")
            
            # Give user option to switch to traditional mode after some time
            if elapsed > 60 and elapsed % 60 == 0:  # Every minute after first minute
                print(f"\n{colored_text('💡 No new shares detected. Options:', Colors.CYAN)}")
                print(f"{colored_text('  1. Continue waiting for multi-tab processes', Colors.CYAN)}")
                print(f"{colored_text('  2. Switch to traditional mode (run shares in this script)', Colors.CYAN)}")
                print(f"{colored_text('  3. Skip this cycle', Colors.CYAN)}")
                
                choice = input(f"{colored_text('Choose option (1/2/3) or press Enter to continue waiting: ', Colors.YELLOW)}").strip()
                if choice == '2':
                    return 'traditional'
                elif choice == '3':
                    return False
                # choice == '1' or empty continues waiting
            
            time.sleep(check_interval)
        
        # Timeout reached
        final_completed, final_accounts = check_cycle_completion(cycle, expected_accounts)
        print(f"\n{colored_text(f'⚠️ Timeout reached! Only {final_accounts}/{expected_accounts} accounts completed', Colors.RED)}")
        
        # Ask user if they want to continue anyway or switch mode
        print(f"\n{colored_text('Options:', Colors.CYAN)}")
        print(f"{colored_text('  y - Continue with incomplete cycle', Colors.CYAN)}")
        print(f"{colored_text('  t - Switch to traditional mode', Colors.CYAN)}")
        print(f"{colored_text('  n - Skip this cycle', Colors.CYAN)}")
        
        choice = input(f"{colored_text('Your choice (y/t/n): ', Colors.YELLOW)}").strip().lower()
        if choice == 't':
            return 'traditional'
        elif choice in ['y', 'yes']:
            return True
        else:
            return False
        
    except Exception as e:
        print(f"{colored_text(f'❌ Error waiting for cycle completion: {e}', Colors.RED)}")
        return False

def get_cycle_shares_for_likes(cycle):
    """Get shares from current cycle for liking"""
    try:
        link_hashes = load_link_hashes()
        cycle_shares = [h for h in link_hashes if h.get('cycle') == cycle]
        
        # Convert to format expected by like functions
        shares_data = []
        for share in cycle_shares:
            shares_data.append({
                'account_index': share.get('account_index'),
                'username': share.get('username'),
                'cast_hash': share.get('cast_hash'),
                'success': True
            })
        
        print(f"{colored_text(f'🔍 Loaded {len(shares_data)} shares from Cycle {cycle} for liking', Colors.CYAN)}")
        return shares_data
        
    except Exception as e:
        print(f"{colored_text(f'❌ Error getting cycle shares: {e}', Colors.RED)}")
        return []

# Color codes for terminal styling
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

def colored_text(text, color):
    """Add color to text"""
    return f"{color}{text}{Colors.END}"

def print_colored_box(title, content, color=Colors.CYAN):
    """Print content in a colored box"""
    lines = content.split('\n') if isinstance(content, str) else content
    max_length = max(len(line) for line in lines) if lines else 50
    box_width = max(max_length + 4, len(title) + 4, 60)
    
    print(colored_text("┌" + "─" * (box_width - 2) + "┐", color))
    print(colored_text(f"│ {title.center(box_width - 4)} │", color))
    print(colored_text("├" + "─" * (box_width - 2) + "┤", color))
    
    for line in lines:
        padding = box_width - len(line) - 4
        print(colored_text(f"│ {line}{' ' * padding} │", color))
    
    print(colored_text("└" + "─" * (box_width - 2) + "┘", color))

def print_simple_status(message, status="info"):
    """Print simple status message"""
    colors = {
        "success": Colors.GREEN,
        "error": Colors.RED, 
        "info": Colors.CYAN,
        "warning": Colors.YELLOW
    }
    color = colors.get(status, Colors.WHITE)
    print(f"{colored_text(message, color)}")
    print(f"{colored_text('═' * 70, color)}")

class FarcasterAutoShareLike:
    def __init__(self, authorization_token, account_index=1, save_links=False):
        self.authorization_token = authorization_token
        self.account_index = account_index
        self.user_id = None
        self.username = None
        self.display_name = None
        self.save_links = save_links  # New option to save link hashes
        
        # Initialize anti-detection session
        if ANTI_DETECTION_AVAILABLE:
            self.stealth_session = create_anti_detection_session(account_index, authorization_token)
            print(f"🛡️ Account {account_index}: Anti-detection session initialized")
        else:
            self.stealth_session = None
        
        # Detect user info from token
        self.detect_user_info()
        
        # Share tracking
        self.shares_posted = 0
        self.likes_given = 0
        self.shares_liked = 0
        
        # Base headers for requests (will be enhanced by anti-detection)
        self.base_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {self.authorization_token}",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

    def make_request(self, method, url, **kwargs):
        """Make request with anti-detection if available"""
        if self.stealth_session and ANTI_DETECTION_AVAILABLE:
            # Use anti-detection system
            api_type = "wreck" if "wreckleague.xyz" in url else "farcaster"
            return make_stealth_request(
                self.stealth_session, 
                method, 
                url, 
                self.authorization_token, 
                api_type,
                **kwargs
            )
        else:
            # Fallback to regular requests
            headers = kwargs.get('headers', {})
            headers.update(self.base_headers)
            kwargs['headers'] = headers
            kwargs.setdefault('timeout', 10)
            return requests.request(method, url, **kwargs)

    def detect_user_info(self):
        """Auto-detect user info dari authorization token"""
        try:
            url = "https://client.warpcast.com/v2/me"
            
            # Add specific headers to prevent compression
            headers = {
                'Authorization': f'Bearer {self.authorization_token}',
                'Accept': 'application/json',
                'Accept-Encoding': 'identity',  # Prevent compression
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.make_request('GET', url, headers=headers)
            
            if response.status_code == 200:
                print(f"{colored_text(f'✅ Account {self.account_index}: GET {url} -> {response.status_code}', Colors.GREEN)}")
                
                # Check content encoding
                content_encoding = response.headers.get('content-encoding', 'none')
                content_type = response.headers.get('content-type', 'unknown')
                print(f"{colored_text(f'📝 Account {self.account_index}: Content-Type: {content_type}, Encoding: {content_encoding}', Colors.BLUE)}")
                
                # Debug: check response content
                response_text = response.text.strip()
                if not response_text:
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: Empty response from server', Colors.YELLOW)}")
                    return False
                
                print(f"{colored_text(f'📝 Account {self.account_index}: Response preview: {response_text[:100]}...', Colors.BLUE)}")
                
                try:
                    data = response.json()
                except ValueError as json_error:
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: Invalid JSON response: {json_error}', Colors.YELLOW)}")
                    print(f"{colored_text(f'   Raw bytes: {response.content[:50]}', Colors.WHITE)}")
                    
                    # Check if it's a HTML error page
                    if b'<html' in response.content[:100].lower():
                        print(f"{colored_text(f'   Response appears to be HTML error page', Colors.WHITE)}")
                    elif response.content.startswith(b'!'):
                        print(f"{colored_text(f'   Response appears to be compressed data', Colors.WHITE)}")
                    
                    return False
                
                user_data = data.get('result', {}).get('user', {})
                self.user_id = user_data.get('fid')
                self.username = user_data.get('username', 'Unknown')
                self.display_name = user_data.get('displayName', 'Unknown')
                
                if self.user_id:
                    print(f"{colored_text(f'✅ Account {self.account_index}: @{self.username} (FID: {self.user_id})', Colors.GREEN)}")
                    return True
                else:
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: Could not extract user ID from response', Colors.YELLOW)}")
                    data_keys = list(data.keys()) if data else "No data"
                    print(f"{colored_text(f'   Data structure: {data_keys}', Colors.WHITE)}")
            else:
                print(f"{colored_text(f'❌ Account {self.account_index}: Failed to get user info (Status: {response.status_code})', Colors.RED)}")
                print(f"{colored_text(f'   Response: {response.text[:100]}...', Colors.WHITE)}")
                    
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error detecting user info: {e}', Colors.RED)}")
            
        return False

    def check_fuel_status(self):
        """Check current fuel status"""
        try:
            if not self.user_id:
                return 0
                
            url = f"https://versus-prod-api.wreckleague.xyz/v1/user/data?fId={self.user_id}"
            response = self.make_request('GET', url)
            
            if response.status_code == 200:
                data = response.json()
                # Try multiple fuel paths
                fuel_paths = [
                    ['data', 'fuelBalance'],
                    ['data', 'fuel'],
                    ['fuel'],
                    ['fuelBalance']
                ]
                
                for path in fuel_paths:
                    try:
                        current_data = data
                        for key in path:
                            current_data = current_data[key]
                        
                        fuel_amount = int(current_data)
                        print(f"{colored_text(f'⛽ Account {self.account_index} fuel: {fuel_amount}', Colors.GREEN)}")
                        return fuel_amount
                    except (KeyError, TypeError, ValueError):
                        continue
                        
                return 0
            else:
                return 0
                
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error checking fuel: {e}', Colors.RED)}")
            return 0

    def trigger_share_analysis(self):
        """Trigger analysis untuk share task"""
        try:
            url = "https://versus-prod-api.wreckleague.xyz/v1/analysis"
            headers = {
                "Authorization": f"Bearer {self.authorization_token}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"{colored_text(f'✅ Account {self.account_index}: Share analysis triggered', Colors.GREEN)}")
                return True
            else:
                print(f"{colored_text(f'⚠️  Account {self.account_index}: Analysis response: {response.status_code}', Colors.YELLOW)}")
                return True  # Not fatal, continue
                
        except Exception as e:
            print(f"{colored_text(f'⚠️  Account {self.account_index}: Analysis error: {e}', Colors.YELLOW)}")
            return True

    def generate_share_text(self, share_number=1, use_original_only=False):
        """Generate varied text for shares"""
        if use_original_only:
            # Only use the original text
            return "Help me get Fuel by liking this cast!\n5 Likes = 1 Fuel🔋\nSupport my mech battles in Wreck League Versus 🤖 by @towerecosystem"
        
        base_texts = [
            "Help me get Fuel by liking this cast!\n5 Likes = 1 Fuel🔋\nSupport my mech battles in Wreck League Versus 🤖 by @towerecosystem",
            "Help me get Fuel by liking this cast! 🔋\n5 Likes = 1 Fuel\nSupport my mech battles in Wreck League Versus 🤖",
            "Need fuel for my mech! ⚡\nLike this cast to help me fight in Wreck League! 🤖\n5 likes = 1 fuel ⛽",
            "Powering up my mech for battle! 🚀\nYour like = My fuel ⛽\nJoin the Wreck League action! 🤖",
            "Fuel needed for epic mech battles! 🔥\nEvery like counts! 👍\nWreck League awaits! ⚔️",
            "My mech needs energy! ⚡\nHelp me by liking this cast! 🔋\nWreck League versus mode activated! 🤖",
            "Battle-ready mech seeking fuel! 🛡️\nYour support powers my victories! 🏆\n5 likes = 1 precious fuel ⛽",
            "Charging up for the next fight! ⚡\nLike = Fuel = Victory! 🎯\nWreck League champion in the making! 🤖",
            "Fuel crisis! SOS! 🆘\nNeed likes to power my mech! 🔋\nEvery like brings me closer to victory! 🏅"
        ]
        
        variations = [
            "\n\n🎮 Join the battle: ",
            "\n\n⚔️ Fight with me: ",
            "\n\n🤖 Mech arena: ",
            "\n\n🔥 Battle zone: ",
            "\n\n⚡ Energy boost: "
        ]
        
        # Select base text and variation
        base_text = random.choice(base_texts)
        
        # Add some randomness
        if random.choice([True, False]):
            variation = random.choice(variations)
            vs_link = f"https://versus.wreckleague.xyz/{self.user_id}"
            final_text = base_text + variation + vs_link
        else:
            final_text = base_text
            
        # Add share number if multiple shares
        if share_number > 1:
            final_text += f"\n\n📊 Share #{share_number}"
            
        return final_text

    def post_share_cast(self, share_number=1, custom_text=None, use_original_only=False, cycle=None):
        """Post a promotional cast to get likes"""
        try:
            url = "https://client.farcaster.xyz/v2/casts"
            
            # Generate or use custom text
            if custom_text:
                cast_text = custom_text
            else:
                cast_text = self.generate_share_text(share_number, use_original_only)
            
            # Prepare payload with embed
            payload = {
                "text": cast_text,
                "embeds": [f"https://versus.wreckleague.xyz/{self.user_id}"]
            }
            
            cycle_info = f" (Cycle {cycle})" if cycle is not None else ""
            print(f"{colored_text(f'📝 Account {self.account_index}: Posting share #{share_number}{cycle_info}...', Colors.CYAN)}")
            
            # Use stealth request with additional headers for Farcaster
            extra_headers = {
                "idempotency-key": str(uuid.uuid4()),
                "fc-amplitude-device-id": str(uuid.uuid4())[:20],
                "fc-amplitude-session-id": str(int(time.time() * 1000)),
            }
            
            response = self.make_request('POST', url, json=payload, headers=extra_headers)
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                if 'result' in result and 'cast' in result['result']:
                    cast_info = result['result']['cast']
                    cast_hash = cast_info.get('hash', 'Unknown')
                    
                    self.shares_posted += 1
                    
                    print(f"{colored_text(f'✅ Account {self.account_index}: Share #{share_number}{cycle_info} posted successfully!', Colors.GREEN)}")
                    print(f"{colored_text(f'   🆔 Cast hash: {cast_hash}', Colors.WHITE)}")
                    print(f"{colored_text(f'   📊 Total shares: {self.shares_posted}', Colors.CYAN)}")
                    
                    result_data = {
                        'success': True,
                        'cast_hash': cast_hash,
                        'account_index': self.account_index,
                        'share_number': share_number,
                        'username': self.username,
                        'user_id': self.user_id
                    }
                    
                    # Save link hash if enabled
                    if self.save_links:
                        save_link_hash(result_data, cycle)
                    
                    return result_data
                    
            print(f"{colored_text(f'❌ Account {self.account_index}: Share #{share_number}{cycle_info} failed (Status: {response.status_code})', Colors.RED)}")
            return {'success': False, 'account_index': self.account_index, 'share_number': share_number}
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error posting share #{share_number}: {e}', Colors.RED)}")
            return {'success': False, 'account_index': self.account_index, 'share_number': share_number}

    def like_cast(self, cast_hash, target_account_info=None):
        """Like a specific cast"""
        try:
            url = "https://client.farcaster.xyz/v2/cast-likes"
            
            payload = {
                "castHash": cast_hash
            }
            
            target_info = f" (from @{target_account_info['username']})" if target_account_info else ""
            print(f"{colored_text(f'👍 Account {self.account_index}: Liking cast{target_info}...', Colors.YELLOW)}")
            
            # Use stealth request with additional headers for Farcaster
            extra_headers = {
                "idempotency-key": str(uuid.uuid4()),
                "fc-amplitude-device-id": str(uuid.uuid4())[:20],
                "fc-amplitude-session-id": str(int(time.time() * 1000)),
            }
            
            response = self.make_request('PUT', url, json=payload, headers=extra_headers)
            
            print(f"{colored_text(f'🔍 Like response: Status {response.status_code}', Colors.WHITE)}")
            
            if response.status_code in [200, 201]:
                self.likes_given += 1
                print(f"{colored_text(f'✅ Account {self.account_index}: Like given successfully! Total: {self.likes_given}', Colors.GREEN)}")
                return True
            else:
                try:
                    error_data = response.json()
                    print(f"{colored_text(f'❌ Account {self.account_index}: Like failed (Status: {response.status_code})', Colors.RED)}")
                    print(f"{colored_text(f'   Error details: {error_data}', Colors.RED)}")
                except:
                    print(f"{colored_text(f'❌ Account {self.account_index}: Like failed (Status: {response.status_code}) - No JSON response', Colors.RED)}")
                return False
                
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error liking cast: {e}', Colors.RED)}")
            return False

    def like_shares_from_others(self, all_shares_data, delay_range=(2, 5)):
        """Like all shares from other accounts"""
        try:
            liked_count = 0
            
            print(f"{colored_text(f'🔍 Account {self.account_index}: Starting to like shares from others...', Colors.CYAN)}")
            print(f"{colored_text(f'   📊 Total shares to process: {len(all_shares_data)}', Colors.WHITE)}")
            
            for i, share_data in enumerate(all_shares_data):
                print(f"{colored_text(f'   🔄 Processing share {i+1}/{len(all_shares_data)}...', Colors.CYAN)}")
                
                # Skip own shares
                if share_data.get('account_index') == self.account_index:
                    print(f"{colored_text(f'   ⏭️  Skipping own share (Account {self.account_index})', Colors.YELLOW)}")
                    continue
                    
                if not share_data.get('success'):
                    print(f"{colored_text(f'   ⏭️  Skipping failed share from Account {share_data.get('account_index')}', Colors.YELLOW)}")
                    continue
                    
                cast_hash = share_data.get('cast_hash')
                if not cast_hash:
                    print(f"{colored_text(f'   ❌ No cast hash found for share from Account {share_data.get('account_index')}', Colors.RED)}")
                    continue
                
                target_info = {
                    'username': share_data.get('username', 'Unknown'),
                    'account_index': share_data.get('account_index', 'Unknown')
                }
                
                print(f"{colored_text(f'   👍 Attempting to like cast from Account {target_info['account_index']} (@{target_info['username']})', Colors.CYAN)}")
                print(f"{colored_text(f'   🆔 Cast hash: {cast_hash[:10]}...', Colors.WHITE)}")
                
                # Like the cast
                if self.like_cast(cast_hash, target_info):
                    liked_count += 1
                    self.shares_liked += 1
                    print(f"{colored_text(f'   ✅ Like successful! Total likes given: {liked_count}', Colors.GREEN)}")
                    
                    # Random delay between likes
                    delay = random.uniform(delay_range[0], delay_range[1])
                    print(f"{colored_text(f'   ⏳ Waiting {delay:.1f}s before next like...', Colors.CYAN)}")
                    time.sleep(delay)
                else:
                    print(f"{colored_text(f'   ❌ Like failed for cast from Account {target_info['account_index']}', Colors.RED)}")
                    # Small delay even on failure
                    time.sleep(1)
            
            print(f"{colored_text(f'📊 Account {self.account_index}: Liked {liked_count} shares from others', Colors.MAGENTA)}")
            return liked_count
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error in like_shares_from_others: {e}', Colors.RED)}")
            return 0

    def run_share_cycle(self, num_shares=5, delay_range=(10, 30), use_original_only=False, cycle=None):
        """Run a complete share cycle for this account"""
        try:
            if shutdown_flag.is_set():
                return []
                
            cycle_info = f" (Cycle {cycle})" if cycle is not None else ""
            print(f"\n{colored_text(f'🚀 Account {self.account_index}: Starting share cycle ({num_shares} shares){cycle_info}', Colors.BOLD + Colors.CYAN)}")
            
            shares_data = []
            
            # Trigger analysis first
            self.trigger_share_analysis()
            time.sleep(2)
            
            # Post shares with delays
            for i in range(1, num_shares + 1):
                if shutdown_flag.is_set():
                    break
                    
                share_result = self.post_share_cast(i, use_original_only=use_original_only, cycle=cycle)
                shares_data.append(share_result)
                
                # Delay between shares (except for last one)
                if i < num_shares:
                    delay = random.uniform(delay_range[0], delay_range[1])
                    print(f"{colored_text(f'⏳ Account {self.account_index}: Waiting {delay:.1f}s before next share...', Colors.CYAN)}")
                    
                    # Sleep with shutdown check
                    for _ in range(int(delay)):
                        if shutdown_flag.is_set():
                            break
                        time.sleep(1)
            
            print(f"{colored_text(f'✅ Account {self.account_index}: Share cycle completed! Posted {self.shares_posted} shares', Colors.GREEN)}")
            return shares_data
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error in share cycle: {e}', Colors.RED)}")
            return []

def load_authorization_tokens(file_path="account.txt"):
    """Load multiple authorization tokens from file"""
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
                print(f"{colored_text(f'✅ Loaded {len(tokens)} authorization token(s)', Colors.GREEN)}")
                return tokens
            else:
                print(f"{colored_text(f'❌ No valid tokens found in {file_path}', Colors.RED)}")
                return []
        else:
            print(f"{colored_text(f'❌ File {file_path} not found!', Colors.RED)}")
            return []
    except Exception as e:
        print(f"{colored_text(f'❌ Error loading tokens: {e}', Colors.RED)}")
        return []

def process_account_shares(account_info, num_shares, delay_range, use_original_only, results_queue, save_links=False, cycle=None):
    """Process shares for a single account in thread"""
    try:
        account_index = account_info['index']
        token = account_info['token']
        
        cycle_info = f" (Cycle {cycle})" if cycle is not None else ""
        print(f"{colored_text(f'🔄 [Thread-{account_index}] Starting share process{cycle_info}...', Colors.CYAN)}")
        
        # Initialize bot instance with save_links option
        bot = FarcasterAutoShareLike(token, account_index, save_links)
        
        # Run share cycle with original text option and cycle info
        shares_data = bot.run_share_cycle(num_shares, delay_range, use_original_only, cycle)
        
        result = {
            'account_index': account_index,
            'bot_instance': bot,
            'shares_data': shares_data,
            'success': len([s for s in shares_data if s.get('success', False)]) > 0
        }
        
        results_queue.put(result)
        print(f"{colored_text(f'✅ [Thread-{account_index}] Share process completed{cycle_info}', Colors.GREEN)}")
        
        return result
        
    except Exception as e:
        error_result = {
            'account_index': account_info['index'],
            'success': False,
            'error': str(e),
            'shares_data': []
        }
        results_queue.put(error_result)
        print(f"{colored_text(f'❌ [Thread-{account_info['index']}] Error: {e}', Colors.RED)}")
        return error_result

def process_account_likes(bot_instance, all_shares_data, delay_range, results_queue):
    """Process likes for a single account in thread"""
    try:
        account_index = bot_instance.account_index
        
        print(f"{colored_text(f'🔄 [Like-Thread-{account_index}] Starting like process...', Colors.YELLOW)}")
        
        # Like shares from other accounts
        likes_given = bot_instance.like_shares_from_others(all_shares_data, delay_range)
        
        result = {
            'account_index': account_index,
            'likes_given': likes_given,
            'success': likes_given > 0
        }
        
        results_queue.put(result)
        print(f"{colored_text(f'✅ [Like-Thread-{account_index}] Like process completed ({likes_given} likes)', Colors.GREEN)}")
        
        return result
        
    except Exception as e:
        error_result = {
            'account_index': bot_instance.account_index,
            'success': False,
            'error': str(e),
            'likes_given': 0
        }
        results_queue.put(error_result)
        print(f"{colored_text(f'❌ [Like-Thread-{bot_instance.account_index}] Error: {e}', Colors.RED)}")
        return error_result

def threaded_share_like_process(account_info_list, num_shares=5, share_delay_range=(10, 30), like_delay_range=(2, 5), use_original_only=False, save_links=False):
    """Main threaded process for share + like automation"""
    try:
        print(f"\n{colored_text('🚀 STARTING THREADED SHARE + LIKE PROCESS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        
        # Phase 1: Share Phase (All accounts post shares)
        print(f"\n{colored_text('📝 PHASE 1: SHARE POSTING', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text(f'🧵 Starting {len(account_info_list)} share threads...', Colors.MAGENTA)}")
        
        if use_original_only:
            print(f"{colored_text('📝 Using ORIGINAL cast text only', Colors.YELLOW)}")
        else:
            print(f"{colored_text('📝 Using VARIED cast texts', Colors.YELLOW)}")
        
        if save_links:
            print(f"{colored_text('💾 Link hash saving: ENABLED', Colors.GREEN)}")
        else:
            print(f"{colored_text('💾 Link hash saving: DISABLED', Colors.YELLOW)}")
        
        share_results_queue = queue.Queue()
        all_bot_instances = []
        all_shares_data = []
        
        with ThreadPoolExecutor(max_workers=len(account_info_list)) as executor:
            # Submit share tasks
            share_futures = [
                executor.submit(process_account_shares, acc_info, num_shares, share_delay_range, use_original_only, share_results_queue, save_links)
                for acc_info in account_info_list
            ]
            
            # Wait for all share tasks to complete
            for future in as_completed(share_futures):
                try:
                    result = future.result()
                    if 'bot_instance' in result:
                        all_bot_instances.append(result['bot_instance'])
                        all_shares_data.extend(result['shares_data'])
                except Exception as e:
                    print(f"{colored_text(f'❌ Share thread error: {e}', Colors.RED)}")
        
        # Collect share results
        share_results = []
        while not share_results_queue.empty():
            share_results.append(share_results_queue.get())
        
        # Phase 1 Summary
        successful_shares = len([s for s in all_shares_data if s.get('success', False)])
        total_shares = len(all_shares_data)
        
        print(f"\n{colored_text('📊 PHASE 1 SUMMARY', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text(f'✅ Successful shares: {successful_shares}/{total_shares}', Colors.GREEN)}")
        print(f"{colored_text(f'👥 Active accounts: {len(all_bot_instances)}', Colors.CYAN)}")
        
        if successful_shares == 0:
            print(f"{colored_text('❌ No shares posted successfully! Stopping process.', Colors.RED)}")
            return
        
        # Phase 2: Like Phase (All accounts like each other's shares)
        print(f"\n{colored_text('👍 PHASE 2: CROSS-LIKING', Colors.BOLD + Colors.YELLOW)}")
        print(f"{colored_text(f'🧵 Starting {len(all_bot_instances)} like threads...', Colors.YELLOW)}")
        
        # Wait a bit for shares to be available
        print(f"{colored_text('⏳ Waiting 10 seconds for shares to be indexed...', Colors.CYAN)}")
        time.sleep(10)
        
        like_results_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=len(all_bot_instances)) as executor:
            # Submit like tasks
            like_futures = [
                executor.submit(process_account_likes, bot, all_shares_data, like_delay_range, like_results_queue)
                for bot in all_bot_instances
            ]
            
            # Wait for all like tasks to complete
            for future in as_completed(like_futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{colored_text(f'❌ Like thread error: {e}', Colors.RED)}")
        
        # Collect like results
        like_results = []
        while not like_results_queue.empty():
            like_results.append(like_results_queue.get())
        
        # Phase 2 Summary
        total_likes_given = sum(r.get('likes_given', 0) for r in like_results)
        successful_likers = len([r for r in like_results if r.get('success', False)])
        
        print(f"\n{colored_text('📊 PHASE 2 SUMMARY', Colors.BOLD + Colors.YELLOW)}")
        print(f"{colored_text(f'👍 Total likes given: {total_likes_given}', Colors.GREEN)}")
        print(f"{colored_text(f'✅ Active likers: {successful_likers}/{len(all_bot_instances)}', Colors.CYAN)}")
        
        # Final Summary
        print(f"\n{colored_text('🎉 FINAL PROCESS SUMMARY', Colors.BOLD + Colors.GREEN)}")
        print_colored_box("RESULTS", [
            f"📝 Total shares posted: {successful_shares}",
            f"👍 Total likes given: {total_likes_given}",
            f"👥 Accounts participated: {len(all_bot_instances)}",
            f"🎯 Cross-engagement rate: {total_likes_given}/{successful_shares * (len(all_bot_instances) - 1) if len(all_bot_instances) > 1 else 0}"
        ], Colors.GREEN)
        
        # Individual account summary
        print(f"\n{colored_text('👤 INDIVIDUAL ACCOUNT SUMMARY', Colors.BOLD + Colors.CYAN)}")
        for bot in all_bot_instances:
            account_shares = len([s for s in all_shares_data if s.get('account_index') == bot.account_index and s.get('success')])
            print(f"{colored_text(f'Account {bot.account_index} (@{bot.username}):', Colors.WHITE)}")
            print(f"  📝 Shares posted: {account_shares}")
            print(f"  👍 Likes given: {bot.likes_given}")
            print(f"  🎯 Shares liked: {bot.shares_liked}")
        
        print(f"\n{colored_text('🎉 SHARE + LIKE AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Process stopped by user', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Unexpected error: {e}', Colors.RED)}")

def independent_cycle_automation(account_info_list, num_shares=5, share_delay_range=(10, 30), like_delay_range=(2, 5), cycles=5, cycle_delay=300, use_original_only=False, save_links=False, expected_accounts=None):
    """Run FULLY INDEPENDENT cycle automation - each tab works independently, only checks link_hash.json"""
    try:
        # Use provided expected_accounts or default to account_info_list length
        if expected_accounts is None:
            expected_accounts = len(account_info_list)
        
        # This should be only 1 account per tab (independent mode)
        if len(account_info_list) != 1:
            print(f"{colored_text('⚠️ Independent mode: Expected 1 account per tab, got {len(account_info_list)}', Colors.YELLOW)}")
        
        # Get the single account for this tab
        account_info = account_info_list[0]
        account_index = account_info['index']
        token = account_info['token']
        
        print(f"\n{colored_text(f'� INDEPENDENT CYCLE AUTOMATION - ACCOUNT {account_index}', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text(f'� Mode: FULLY INDEPENDENT (no inter-tab communication)', Colors.CYAN)}")
        print(f"{colored_text(f'👥 Expected total accounts: {expected_accounts}', Colors.CYAN)}")
        print(f"{colored_text(f'� Running infinite cycles with {cycle_delay//60} minute intervals', Colors.CYAN)}")
        
        # Initialize single bot instance for this tab
        print(f"\n{colored_text(f'🔍 Initializing Account {account_index}...', Colors.YELLOW)}")
        try:
            bot = FarcasterAutoShareLike(token, account_index, save_links)
            if not bot.user_id:
                print(f"{colored_text(f'❌ Account {account_index}: Failed to initialize', Colors.RED)}")
                return
            print(f"{colored_text(f'✅ Account {account_index}: @{bot.username} ready', Colors.GREEN)}")
        except Exception as e:
            print(f"{colored_text(f'❌ Account {account_index}: Initialization error - {e}', Colors.RED)}")
            return
        
        print(f"{colored_text(f'✅ Account {account_index} ready for independent operation', Colors.GREEN)}")
        
        # Run infinite cycles until Ctrl+C
        cycle = 1
        try:
            while not shutdown_flag.is_set():  # Check shutdown flag
                print(f"\n{colored_text(f'🔥 STARTING CYCLE {cycle} (Press Ctrl+C to stop)', Colors.BOLD + Colors.MAGENTA)}")
                print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
                
                # Check shutdown before each phase
                if shutdown_flag.is_set():
                    break
                
                # Phase 1: Share Phase - Always do sharing, save to link_hash.json if enabled
                print(f"\n{colored_text(f'📝 CYCLE {cycle} - PHASE 1: SHARING', Colors.BOLD + Colors.CYAN)}")
                
                # Always do threaded sharing for every cycle
                print(f"{colored_text('� Starting threaded sharing for all accounts...', Colors.CYAN)}")
                if save_links:
                    print(f"{colored_text('💾 Results will be saved to link_hash.json', Colors.GREEN)}")
                
                cycle_shares_data = []
                share_results_queue = queue.Queue()
                
                with ThreadPoolExecutor(max_workers=len(all_bot_instances)) as executor:
                    # Create account info for this cycle
                    cycle_account_info = [
                        {'index': bot.account_index, 'token': bot.authorization_token}
                        for bot in all_bot_instances
                    ]
                    
                    # Submit share tasks with cycle number
                    share_futures = [
                        executor.submit(process_account_shares, acc_info, num_shares, share_delay_range, use_original_only, share_results_queue, save_links, cycle)
                        for acc_info in cycle_account_info
                    ]
                    
                    # Wait for all share tasks to complete
                    for future in as_completed(share_futures):
                        try:
                            result = future.result()
                            if 'shares_data' in result:
                                cycle_shares_data.extend(result['shares_data'])
                        except Exception as e:
                            print(f"{colored_text(f'❌ Share thread error: {e}', Colors.RED)}")
                
                # Filter successful shares
                cycle_shares_data = [s for s in cycle_shares_data if s.get('success', False)]
                successful_shares = len(cycle_shares_data)
                
                # Phase 1 Summary
                print(f"\n{colored_text(f'📊 CYCLE {cycle} - PHASE 1 SUMMARY', Colors.BOLD + Colors.CYAN)}")
                print(f"{colored_text(f'✅ Shares completed: {successful_shares}/{expected_accounts * num_shares}', Colors.GREEN)}")
                
                if save_links:
                    # Additional validation for multi-tab mode
                    unique_accounts = set(share.get('account_index') for share in cycle_shares_data)
                    print(f"{colored_text(f'👥 Accounts participated: {len(unique_accounts)}/{expected_accounts}', Colors.CYAN)}")
                    
                    if len(unique_accounts) == expected_accounts:
                        print(f"{colored_text(f'✅ All accounts completed shares for Cycle {cycle}!', Colors.GREEN)}")
                    else:
                        missing = set(range(1, expected_accounts+1)) - unique_accounts
                        print(f"{colored_text(f'⚠️ Missing accounts: {sorted(list(missing))}', Colors.YELLOW)}")
                
                # Debug: Show share data
                print(f"\n{colored_text('🔍 DEBUG: Share data collected:', Colors.YELLOW)}")
                for i, share in enumerate(cycle_shares_data[:5], 1):  # Show first 5
                    account_idx = share.get('account_index', 'Unknown')
                    username = share.get('username', 'Unknown')
                    cast_hash = share.get('cast_hash', 'No hash')[:10] + '...' if share.get('cast_hash') else 'No hash'
                    print(f"  Share {i}: Account {account_idx} (@{username}), Hash: {cast_hash}")
                
                if len(cycle_shares_data) > 5:
                    print(f"  ... and {len(cycle_shares_data) - 5} more shares")
                
                if successful_shares == 0:
                    print(f"{colored_text(f'❌ No shares posted in cycle {cycle}! Continuing to next cycle.', Colors.RED)}")
                else:
                    # Phase 2: Like Phase for this cycle's shares
                    print(f"\n{colored_text(f'👍 CYCLE {cycle} - PHASE 2: CROSS-LIKING', Colors.BOLD + Colors.YELLOW)}")
                    print(f"{colored_text('⏳ Waiting 30 seconds for shares to be indexed and available...', Colors.CYAN)}")
                    
                    # Longer wait for API indexing with countdown
                    for i in range(30, 0, -5):
                        print(f"{colored_text(f'⏰ Waiting {i} seconds...', Colors.CYAN)}")
                        time.sleep(5)
                    
                    like_results_queue = queue.Queue()
                    
                    with ThreadPoolExecutor(max_workers=len(all_bot_instances)) as executor:
                        # Submit like tasks for this cycle's shares
                        like_futures = [
                            executor.submit(process_account_likes, bot, cycle_shares_data, like_delay_range, like_results_queue)
                            for bot in all_bot_instances
                        ]
                        
                        # Wait for all like tasks to complete
                        for future in as_completed(like_futures):
                            try:
                                future.result()
                            except Exception as e:
                                print(f"{colored_text(f'❌ Like thread error: {e}', Colors.RED)}")
                    
                    # Phase 2 Summary
                    like_results = []
                    while not like_results_queue.empty():
                        like_results.append(like_results_queue.get())
                    
                    total_likes_given = sum(r.get('likes_given', 0) for r in like_results)
                    print(f"\n{colored_text(f'📊 CYCLE {cycle} - PHASE 2 SUMMARY', Colors.BOLD + Colors.YELLOW)}")
                    print(f"{colored_text(f'👍 Likes given: {total_likes_given}', Colors.GREEN)}")
                    
                    # Cycle Summary
                    print(f"\n{colored_text(f'🎯 CYCLE {cycle} COMPLETED!', Colors.BOLD + Colors.GREEN)}")
                    print_colored_box(f"CYCLE {cycle} RESULTS", [
                        f"📝 Shares posted: {successful_shares}",
                        f"👍 Likes given: {total_likes_given}",
                        f"🎯 Engagement: {total_likes_given}/{successful_shares * (len(all_bot_instances) - 1) if len(all_bot_instances) > 1 else 0}"
                    ], Colors.GREEN)
                
                cycle += 1
                
                # Check if we should continue (infinite if cycles=999)
                if cycles != 999 and cycle > cycles:
                    break
                
                # Wait before next cycle
                if cycles == 999 or cycle <= cycles:
                    print(f"\n{colored_text(f'⏳ Waiting {cycle_delay//60} minutes before CYCLE {cycle}...', Colors.CYAN)}")
                    print(f"{colored_text('💡 Press Ctrl+C anytime to stop automation', Colors.YELLOW)}")
                    
                    # Countdown with Ctrl+C check
                    for remaining_mins in range(cycle_delay//60, 0, -1):
                        if shutdown_flag.is_set():
                            break
                        print(f"{colored_text(f'⏰ Next cycle in: {remaining_mins} minutes... (Ctrl+C to stop)', Colors.YELLOW)}")
                        time.sleep(60)  # Wait 1 minute
                    
                    if shutdown_flag.is_set():
                        break
                
        except KeyboardInterrupt:
            print(f"\n{colored_text('⚠️  Received interrupt signal. Shutting down gracefully...', Colors.YELLOW)}")
            shutdown_flag.set()
            return
        
        # Final Summary
        print(f"\n{colored_text(f'🎉 AUTOMATION COMPLETED AFTER {cycle-1} CYCLES!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
        # Show final stats for all bots
        print(f"\n{colored_text('👤 FINAL ACCOUNT STATISTICS', Colors.BOLD + Colors.CYAN)}")
        for bot in all_bot_instances:
            print(f"{colored_text(f'Account {bot.account_index} (@{bot.username}):', Colors.WHITE)}")
            print(f"  📝 Total shares: {bot.shares_posted}")
            print(f"  👍 Total likes given: {bot.likes_given}")
            print(f"  🎯 Shares liked: {bot.shares_liked}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Cycle-based automation stopped by user', Colors.RED)}")
        shutdown_flag.set()
    except Exception as e:
        print(f"\n{colored_text(f'❌ Cycle-based automation error: {e}', Colors.RED)}")

# Import clean independent function
try:
    from independent_clean import independent_cycle_automation_clean
    # Replace the problematic function with clean version
    cycle_based_share_like_automation = independent_cycle_automation_clean
    independent_cycle_automation = independent_cycle_automation_clean
    print("✅ Using clean independent automation function")
except Exception as e:
    print(f"⚠️ Could not load clean function: {e}")
    # Fallback to basic function
    def cycle_based_share_like_automation(*args, **kwargs):
        print("❌ Function not available - using fallback")
        return False

def continuous_share_like_automation(account_info_list, cycles=5, cycle_delay=300):
    """Run continuous share + like automation with multiple cycles - LEGACY VERSION"""
    try:
        print(f"\n{colored_text('🔄 CONTINUOUS SHARE + LIKE AUTOMATION', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text(f'🔂 Running {cycles} cycles with {cycle_delay//60} minute intervals', Colors.CYAN)}")
        
        for cycle in range(1, cycles + 1):
            print(f"\n{colored_text(f'🔥 STARTING CYCLE {cycle}/{cycles}', Colors.BOLD + Colors.MAGENTA)}")
            print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
            
            # Run one complete share + like process
            threaded_share_like_process(account_info_list)
            
            # Wait before next cycle (except for last cycle)
            if cycle < cycles:
                print(f"\n{colored_text(f'⏳ Waiting {cycle_delay//60} minutes before next cycle...', Colors.YELLOW)}")
                
                # Countdown timer
                for remaining in range(cycle_delay, 0, -60):
                    mins = remaining // 60
                    print(f"{colored_text(f'⏰ Next cycle in: {mins} minutes...', Colors.CYAN)}")
                    time.sleep(60)
        
        print(f"\n{colored_text(f'🎉 ALL {cycles} CYCLES COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Continuous automation stopped by user', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Continuous automation error: {e}', Colors.RED)}")

# Global flag for graceful shutdown
shutdown_flag = threading.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C signal gracefully"""
    print(f"\n{colored_text('⚠️  Received interrupt signal. Shutting down gracefully...', Colors.YELLOW)}")
    shutdown_flag.set()
    time.sleep(0.5)
    print(f"{colored_text('🛑 Force shutdown initiated!', Colors.RED)}")
    os._exit(0)

def main():
    """Main function with advanced share + like automation"""
    # Clear screen for better presentation
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Animated header
    header_lines = [
        "╔══════════════════════════════════════════════════════════════════╗",
        "║           🚀 FARCASTER AUTO SHARE + LIKE SCRIPT 🚀             ║",
        "║                    ADVANCED MULTI-ACCOUNT EDITION               ║",
        "║                      WITH ANTI-DETECTION SYSTEM                 ║",
        "╠══════════════════════════════════════════════════════════════════╣",
        "║  📝 Auto Share Posts with Custom Text Variations               ║",
        "║  👍 Cross-Account Automatic Liking System                      ║", 
        "║  🧵 Multi-Threading for Maximum Performance                     ║",
        "║  🔄 Continuous Automation with Smart Delays                    ║",
        "║  🛡️ Advanced Anti-Detection & Proxy Support                   ║",
        "╚══════════════════════════════════════════════════════════════════╝"
    ]
    
    for line in header_lines:
        print(colored_text(line, Colors.BOLD + Colors.CYAN))
        time.sleep(0.1)
    
    print(f"\n{colored_text('🔍 Initializing system...', Colors.YELLOW)}")
    
    # Show anti-detection status
    if ANTI_DETECTION_AVAILABLE:
        print(f"{colored_text('🛡️ Anti-Detection System: ENABLED', Colors.GREEN)}")
        try:
            # Initialize anti-detection manager to check proxy status
            from anti_detection import AntiDetectionManager
            temp_manager = AntiDetectionManager()
            proxy_count = len(temp_manager.proxy_manager.proxies)
            if proxy_count > 0:
                print(f"{colored_text(f'🔒 Proxy System: {proxy_count} proxies loaded', Colors.GREEN)}")
            else:
                print(f"{colored_text('⚠️ Proxy System: No proxies loaded (using direct connection)', Colors.YELLOW)}")
        except Exception as e:
            print(f"{colored_text('🔒 Proxy System: Testing...', Colors.CYAN)}")
    else:
        print(f"{colored_text('⚠️ Anti-Detection System: DISABLED', Colors.RED)}")
        print(f"{colored_text('   Install anti_detection.py for stealth features', Colors.YELLOW)}")
    
    # Load all tokens
    print(f"\n{colored_text('📄 Loading authorization tokens...', Colors.BLUE)}")
    auth_tokens = load_authorization_tokens()
    if not auth_tokens:
        print(colored_text("❌ Error: Could not load any authorization tokens!", Colors.RED))
        return
    
    # Create account info list
    account_info = []
    for i, token in enumerate(auth_tokens, 1):
        account_info.append({
            'index': i,
            'token': token
        })
    
    print(f"{colored_text(f'✅ Successfully loaded {len(account_info)} account(s)', Colors.GREEN)}")
    
    # Main menu
    print(f"\n{colored_text('🎛️  SHARE + LIKE CONTROL PANEL', Colors.BOLD + Colors.CYAN)}")
    menu_lines = [
        "┌─────────────────────────────────────────────────────────────────┐",
        "│  1. 🚀 Single Share + Like Process                            │",
        "│  2. 🔄 Infinite Cycle Automation (Ctrl+C to stop)             │",
        "│  3. ⛽ Check Fuel Status All Accounts                         │",
        "│  4. 📊 Test Account Detection                                  │"
    ]
    
    if ANTI_DETECTION_AVAILABLE:
        menu_lines.extend([
            "│  5. 🛡️ Test Anti-Detection System                            │",
            "│  6. 🔒 Check Proxy Status                                     │",
            "│  7. 🚪 Exit                                                    │"
        ])
        max_choice = 7
    else:
        menu_lines.extend([
            "│  5. 🚪 Exit                                                    │"
        ])
        max_choice = 5
    
    menu_lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    for line in menu_lines:
        print(colored_text(line, Colors.BLUE))
    
    choice = input(f"\n{colored_text(f'💫 Choose your action (1-{max_choice}): ', Colors.BOLD + Colors.YELLOW)}").strip()
    
    if choice == "1":
        # Single process configuration
        print(f"\n{colored_text('⚙️  SINGLE PROCESS CONFIGURATION', Colors.BOLD + Colors.MAGENTA)}")
        
        try:
            # Ask about saving link hashes
            while True:
                save_choice = input(f"{colored_text('💾 Save cast link hashes to link_hash.json? (y/n): ', Colors.CYAN)}").strip().lower()
                if save_choice in ['y', 'yes']:
                    save_links = True
                    print(f"{colored_text('✅ Link hash saving: ENABLED', Colors.GREEN)}")
                    break
                elif save_choice in ['n', 'no']:
                    save_links = False
                    print(f"{colored_text('✅ Link hash saving: DISABLED', Colors.YELLOW)}")
                    break
                else:
                    print(f"{colored_text('❌ Please enter y or n', Colors.RED)}")
            
            # Ask about original cast text option
            while True:
                original_choice = input(f"{colored_text('📝 Use ORIGINAL cast text only? (y/n): ', Colors.CYAN)}").strip().lower()
                if original_choice in ['y', 'yes']:
                    use_original_only = True
                    print(f"{colored_text('✅ Will use ORIGINAL cast text only', Colors.GREEN)}")
                    break
                elif original_choice in ['n', 'no']:
                    use_original_only = False
                    print(f"{colored_text('✅ Will use VARIED cast texts', Colors.GREEN)}")
                    break
                else:
                    print(f"{colored_text('❌ Please enter y or n', Colors.RED)}")
            
            num_shares = int(input(f"{colored_text('📝 Number of shares per account: ', Colors.CYAN)}") or "3")
            num_shares = max(1, num_shares)
            
            share_delay_min = int(input(f"{colored_text('⏳ Min delay between shares (seconds): ', Colors.CYAN)}") or "10")
            share_delay_max = int(input(f"{colored_text('⏳ Max delay between shares (seconds): ', Colors.CYAN)}") or "30")
            share_delay_range = (max(1, share_delay_min), max(share_delay_min + 1, share_delay_max))
            
            like_delay_min = int(input(f"{colored_text('👍 Min delay between likes (seconds): ', Colors.CYAN)}") or "2")
            like_delay_max = int(input(f"{colored_text('👍 Max delay between likes (seconds): ', Colors.CYAN)}") or "5")
            like_delay_range = (max(1, like_delay_min), max(like_delay_min + 1, like_delay_max))
            
        except ValueError:
            print(f"{colored_text('⚠️  Invalid input, using defaults', Colors.YELLOW)}")
            save_links = False
            use_original_only = False
            num_shares = 3
            share_delay_range = (10, 30)
            like_delay_range = (2, 5)
        
        print(f"\n{colored_text('✅ CONFIGURATION SUMMARY', Colors.GREEN)}")
        print(f"  � Save link hashes: {'Yes' if save_links else 'No'}")
        print(f"  �📝 Shares per account: {num_shares}")
        print(f"  📝 Original text only: {'Yes' if use_original_only else 'No'}")
        print(f"  ⏳ Share delay: {share_delay_range[0]}-{share_delay_range[1]}s")
        print(f"  👍 Like delay: {like_delay_range[0]}-{like_delay_range[1]}s")
        print(f"  👥 Total accounts: {len(account_info)}")
        
        confirm = input(f"\n{colored_text('Start process? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if confirm in ['y', 'yes', '']:
            threaded_share_like_process(account_info, num_shares, share_delay_range, like_delay_range, use_original_only, save_links)
        
    elif choice == "2":
        # New cycle-based automation configuration
        print(f"\n{colored_text('⚙️  INFINITE CYCLE-BASED AUTOMATION CONFIGURATION', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('💡 Infinite cycles: Share → Like → Complete → Repeat (Ctrl+C to stop)', Colors.CYAN)}")
        
        try:
            # Ask about saving link hashes
            while True:
                save_choice = input(f"{colored_text('💾 Save cast link hashes to link_hash.json? (y/n): ', Colors.CYAN)}").strip().lower()
                if save_choice in ['y', 'yes']:
                    save_links = True
                    print(f"{colored_text('✅ Link hash saving: ENABLED', Colors.GREEN)}")
                    break
                elif save_choice in ['n', 'no']:
                    save_links = False
                    print(f"{colored_text('✅ Link hash saving: DISABLED', Colors.YELLOW)}")
                    break
                else:
                    print(f"{colored_text('❌ Please enter y or n', Colors.RED)}")
            
            # Ask about original cast text option
            while True:
                original_choice = input(f"{colored_text('📝 Use ORIGINAL cast text only? (y/n): ', Colors.CYAN)}").strip().lower()
                if original_choice in ['y', 'yes']:
                    use_original_only = True
                    print(f"{colored_text('✅ Will use ORIGINAL cast text only', Colors.GREEN)}")
                    break
                elif original_choice in ['n', 'no']:
                    use_original_only = False
                    print(f"{colored_text('✅ Will use VARIED cast texts', Colors.GREEN)}")
                    break
                else:
                    print(f"{colored_text('❌ Please enter y or n', Colors.RED)}")
            
            num_shares = int(input(f"{colored_text('📝 Shares per account per cycle: ', Colors.CYAN)}") or "3")
            num_shares = max(1, num_shares)
            
            share_delay_min = int(input(f"{colored_text('⏳ Min delay between shares (seconds): ', Colors.CYAN)}") or "10")
            share_delay_max = int(input(f"{colored_text('⏳ Max delay between shares (seconds): ', Colors.CYAN)}") or "30")
            share_delay_range = (max(1, share_delay_min), max(share_delay_min + 1, share_delay_max))
            
            like_delay_min = int(input(f"{colored_text('👍 Min delay between likes (seconds): ', Colors.CYAN)}") or "2")
            like_delay_max = int(input(f"{colored_text('👍 Max delay between likes (seconds): ', Colors.CYAN)}") or "5")
            like_delay_range = (max(1, like_delay_min), max(like_delay_min + 1, like_delay_max))
            
            cycle_delay_mins = int(input(f"{colored_text('⏰ Delay between cycles (minutes): ', Colors.CYAN)}") or "15")
            cycle_delay = max(60, cycle_delay_mins * 60)
            
        except ValueError:
            print(f"{colored_text('⚠️  Invalid input, using defaults', Colors.YELLOW)}")
            save_links = False
            use_original_only = False
            num_shares = 3
            share_delay_range = (10, 30)
            like_delay_range = (2, 5)
            cycle_delay = 900  # 15 minutes
        
        print(f"\n{colored_text('✅ INFINITE CYCLE AUTOMATION SUMMARY', Colors.GREEN)}")
        print(f"  � Save link hashes: {'Yes' if save_links else 'No'}")
        print(f"  �📝 Shares per cycle: {num_shares} per account")
        print(f"  📝 Original text only: {'Yes' if use_original_only else 'No'}")
        print(f"  ⏳ Share delay: {share_delay_range[0]}-{share_delay_range[1]}s")
        print(f"  👍 Like delay: {like_delay_range[0]}-{like_delay_range[1]}s")
        print(f"  � Cycles: INFINITE (until Ctrl+C)")
        print(f"  ⏰ Cycle interval: {cycle_delay//60} minutes")
        print(f"  👥 Total accounts: {len(account_info)}")
        print(f"  ⛔ Stop method: Press Ctrl+C anytime")
        
        confirm = input(f"\n{colored_text('Start infinite cycle automation? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if confirm in ['y', 'yes', '']:
            cycle_based_share_like_automation(account_info, num_shares, share_delay_range, like_delay_range, 999, cycle_delay, use_original_only, save_links)  # cycles=999 as placeholder, will be infinite
        
    elif choice == "3":
        # Check fuel status
        print(f"\n{colored_text('⛽ CHECKING FUEL STATUS FOR ALL ACCOUNTS', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
        total_fuel = 0
        for i, acc_info in enumerate(account_info, 1):
            try:
                bot = FarcasterAutoShareLike(acc_info['token'], i)
                fuel = bot.check_fuel_status()
                total_fuel += fuel
                time.sleep(1)  # Small delay between checks
            except Exception as e:
                print(f"{colored_text(f'❌ Account {i}: Error checking fuel: {e}', Colors.RED)}")
        
        print(f"\n{colored_text(f'💰 TOTAL FUEL ACROSS ALL ACCOUNTS: {total_fuel}', Colors.BOLD + Colors.GREEN)}")
        
    elif choice == "4":
        # Test account detection
        print(f"\n{colored_text('📊 TESTING ACCOUNT DETECTION', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        
        for i, acc_info in enumerate(account_info, 1):
            try:
                print(f"\n{colored_text(f'Testing Account {i}...', Colors.CYAN)}")
                bot = FarcasterAutoShareLike(acc_info['token'], i)
                if bot.user_id:
                    fuel = bot.check_fuel_status()
                    print(f"  ✅ Detection successful")
                    print(f"  👤 Username: @{bot.username}")
                    print(f"  🆔 FID: {bot.user_id}")
                    print(f"  📝 Display Name: {bot.display_name}")
                    print(f"  ⛽ Fuel: {fuel}")
                else:
                    print(f"  ❌ Detection failed")
                
                time.sleep(1)
            except Exception as e:
                print(f"{colored_text(f'❌ Account {i}: Error: {e}', Colors.RED)}")
        
    elif choice == "5" and ANTI_DETECTION_AVAILABLE:
        # Test anti-detection system
        print(f"\n{colored_text('🛡️ TESTING ANTI-DETECTION SYSTEM', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
        try:
            from anti_detection import test_proxy_setup
            result = test_proxy_setup()
            print(f"\n{colored_text('📊 Anti-Detection Test Completed', Colors.GREEN)}")
        except Exception as e:
            print(f"{colored_text(f'❌ Anti-detection test failed: {e}', Colors.RED)}")
        
    elif choice == "6" and ANTI_DETECTION_AVAILABLE:
        # Check proxy status
        print(f"\n{colored_text('🔒 PROXY STATUS CHECK', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
        try:
            stats = get_anti_detection_stats()
            proxy_stats = stats.get('proxy_stats', {})
            
            print(f"{colored_text('� PROXY STATISTICS', Colors.BOLD + Colors.CYAN)}")
            print(f"  Total Proxies: {proxy_stats.get('total_proxies', 0)}")
            print(f"  Working Proxies: {proxy_stats.get('working_proxies', 0)}")
            print(f"  Failed Proxies: {proxy_stats.get('failed_proxies', 0)}")
            print(f"  Active Sessions: {stats.get('active_sessions', 0)}")
            
        except Exception as e:
            print(f"{colored_text(f'❌ Proxy status check failed: {e}', Colors.RED)}")
        
    elif choice == str(max_choice):
        print(f"\n{colored_text('═' * 70, Colors.MAGENTA)}")
        print(f"{colored_text('👋 Thank you for using Farcaster Auto Share + Like!', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('💫 See you next time!', Colors.YELLOW)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
    elif choice == "5" and not ANTI_DETECTION_AVAILABLE:
        print(f"\n{colored_text('═' * 70, Colors.MAGENTA)}")
        print(f"{colored_text('�👋 Thank you for using Farcaster Auto Share + Like!', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('💫 See you next time!', Colors.YELLOW)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
    else:
        print(f"{colored_text(f'❌ Invalid choice! Please select 1-{max_choice}.', Colors.RED)}")

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()

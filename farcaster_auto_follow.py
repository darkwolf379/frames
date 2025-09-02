#!/usr/bin/env python3
"""
Farcaster Auto Follow Script - Advanced Multi-Account Edition with Anti-Detection
Script untuk otomatisasi follow antar account dan follow target FID range dengan sistem anti-deteksi
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

class FarcasterAutoFollow:
    def __init__(self, authorization_token, account_index=1):
        self.authorization_token = authorization_token
        self.account_index = account_index
        self.user_id = None
        self.username = None
        self.display_name = None
        
        # Initialize anti-detection session
        if ANTI_DETECTION_AVAILABLE:
            self.stealth_session = create_anti_detection_session(account_index, authorization_token)
            print(f"🛡️ Account {account_index}: Anti-detection session initialized")
        else:
            self.stealth_session = None
        
        # Detect user info from token
        self.detect_user_info()
        
        # Follow tracking
        self.follows_made = 0
        self.follows_skipped = 0
        self.follows_failed = 0
        
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
            api_type = "farcaster"
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

    def get_user_info_by_fid(self, target_fid):
        """Get user info by FID"""
        try:
            url = f"https://client.warpcast.com/v2/user?fid={target_fid}"
            
            # Add specific headers to prevent compression and ensure proper response
            extra_headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'identity',  # Prevent compression
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.make_request('GET', url, headers=extra_headers)
            
            if response.status_code == 200:
                # Check content encoding
                content_encoding = response.headers.get('content-encoding', 'none')
                if content_encoding != 'none':
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: Compressed response detected for FID {target_fid}: {content_encoding}', Colors.YELLOW)}")
                
                # Debug: check response content
                response_text = response.text.strip()
                if not response_text:
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: Empty response for FID {target_fid}', Colors.YELLOW)}")
                    return None
                
                # Check if response starts with valid JSON
                if not response_text.startswith('{'):
                    # Check for binary/compressed data
                    if any(ord(c) < 32 or ord(c) > 126 for c in response_text[:10]):
                        print(f"{colored_text(f'⚠️ Account {self.account_index}: Binary/compressed response for FID {target_fid} (encoding: {content_encoding})', Colors.YELLOW)}")
                    else:
                        print(f"{colored_text(f'⚠️ Account {self.account_index}: Invalid JSON response for FID {target_fid}: {response_text[:50]}...', Colors.YELLOW)}")
                    return None
                
                try:
                    data = response.json()
                except ValueError as json_error:
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: JSON parse error for FID {target_fid}: {json_error}', Colors.YELLOW)}")
                    print(f"{colored_text(f'   Raw response: {response_text[:100]}...', Colors.WHITE)}")
                    return None
                
                user_data = data.get('result', {}).get('user', {})
                
                if user_data:
                    return {
                        'fid': user_data.get('fid'),
                        'username': user_data.get('username', 'Unknown'),
                        'display_name': user_data.get('displayName', 'Unknown'),
                        'follower_count': user_data.get('followerCount', 0),
                        'following_count': user_data.get('followingCount', 0)
                    }
            else:
                print(f"{colored_text(f'⚠️ Account {self.account_index}: HTTP {response.status_code} for FID {target_fid}', Colors.YELLOW)}")
            
            return None
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error getting user info for FID {target_fid}: {e}', Colors.RED)}")
            return None

    def check_if_following(self, target_fid):
        """Check if already following a user"""
        try:
            url = f"https://client.warpcast.com/v2/following-status?targetFid={target_fid}"
            
            # Add specific headers to prevent compression
            extra_headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'identity',  # Prevent compression
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.make_request('GET', url, headers=extra_headers)
            
            if response.status_code == 200:
                # Check for valid JSON response
                response_text = response.text.strip()
                if not response_text or not response_text.startswith('{'):
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: Invalid follow status response for FID {target_fid}', Colors.YELLOW)}")
                    return False
                
                try:
                    data = response.json()
                    result = data.get('result', {})
                    return result.get('following', False)
                except ValueError as json_error:
                    print(f"{colored_text(f'⚠️ Account {self.account_index}: JSON parse error in follow status for FID {target_fid}: {json_error}', Colors.YELLOW)}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error checking follow status for FID {target_fid}: {e}', Colors.RED)}")
            return False

    def follow_user(self, target_fid, target_info=None):
        """Follow a user by FID"""
        try:
            # Check if already following
            if self.check_if_following(target_fid):
                self.follows_skipped += 1
                target_name = f"@{target_info['username']}" if target_info else f"FID {target_fid}"
                print(f"{colored_text(f'⏭️  Account {self.account_index}: Already following {target_name}', Colors.YELLOW)}")
                return True
            
            url = "https://client.farcaster.xyz/v2/follows"
            
            payload = {
                "targetFid": target_fid
            }
            
            target_name = f"@{target_info['username']}" if target_info else f"FID {target_fid}"
            print(f"{colored_text(f'👥 Account {self.account_index}: Following {target_name}...', Colors.CYAN)}")
            
            # Use stealth request with additional headers for Farcaster
            extra_headers = {
                "idempotency-key": str(uuid.uuid4()),
                "fc-amplitude-device-id": str(uuid.uuid4())[:20],
                "fc-amplitude-session-id": str(int(time.time() * 1000)),
            }
            
            response = self.make_request('PUT', url, json=payload, headers=extra_headers)
            
            print(f"{colored_text(f'🔍 Follow response: Status {response.status_code}', Colors.WHITE)}")
            
            if response.status_code in [200, 201]:
                self.follows_made += 1
                print(f"{colored_text(f'✅ Account {self.account_index}: Successfully followed {target_name}! Total: {self.follows_made}', Colors.GREEN)}")
                return True
            else:
                self.follows_failed += 1
                try:
                    error_data = response.json()
                    print(f"{colored_text(f'❌ Account {self.account_index}: Follow failed (Status: {response.status_code})', Colors.RED)}")
                    print(f"{colored_text(f'   Error details: {error_data}', Colors.RED)}")
                except:
                    print(f"{colored_text(f'❌ Account {self.account_index}: Follow failed (Status: {response.status_code}) - No JSON response', Colors.RED)}")
                return False
                
        except Exception as e:
            self.follows_failed += 1
            print(f"{colored_text(f'❌ Account {self.account_index}: Error following user: {e}', Colors.RED)}")
            return False

    def follow_accounts_from_list(self, other_accounts_data, delay_range=(2, 5), max_follows=None):
        """Follow accounts from the account list with optional limit"""
        try:
            followed_count = 0
            processed_count = 0
            
            # Filter out own account and invalid accounts
            valid_accounts = [
                acc for acc in other_accounts_data 
                if acc.get('account_index') != self.account_index and acc.get('user_id')
            ]
            
            print(f"{colored_text(f'🔍 Account {self.account_index}: Starting to follow other accounts...', Colors.CYAN)}")
            print(f"{colored_text(f'   📊 Valid accounts available: {len(valid_accounts)}', Colors.WHITE)}")
            
            if max_follows:
                print(f"{colored_text(f'   � Max follows limit: {max_follows}', Colors.WHITE)}")
                # Shuffle the list to randomize selection
                random.shuffle(valid_accounts)
                # Limit to max_follows
                valid_accounts = valid_accounts[:max_follows]
                print(f"{colored_text(f'   📊 Will process: {len(valid_accounts)} accounts', Colors.WHITE)}")
            
            for i, account_data in enumerate(valid_accounts):
                if shutdown_flag.is_set():
                    break
                    
                processed_count += 1
                print(f"{colored_text(f'   🔄 Processing account {processed_count}/{len(valid_accounts)}...', Colors.CYAN)}")
                
                target_fid = account_data.get('user_id')
                target_info = {
                    'username': account_data.get('username', 'Unknown'),
                    'fid': target_fid
                }
                
                print(f"{colored_text(f'   👥 Attempting to follow Account {account_data.get('account_index')} (@{target_info['username']}, FID: {target_fid})', Colors.CYAN)}")
                
                # Follow the account
                if self.follow_user(target_fid, target_info):
                    followed_count += 1
                    print(f"{colored_text(f'   ✅ Follow successful! Total follows: {followed_count}', Colors.GREEN)}")
                    
                    # Random delay between follows
                    delay = random.uniform(delay_range[0], delay_range[1])
                    print(f"{colored_text(f'   ⏳ Waiting {delay:.1f}s before next follow...', Colors.CYAN)}")
                    time.sleep(delay)
                else:
                    print(f"{colored_text(f'   ❌ Follow failed for Account {account_data.get('account_index')}', Colors.RED)}")
                    # Small delay even on failure
                    time.sleep(1)
            
            print(f"{colored_text(f'📊 Account {self.account_index}: Followed {followed_count}/{processed_count} accounts from list', Colors.MAGENTA)}")
            return followed_count
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error in follow_accounts_from_list: {e}', Colors.RED)}")
            return 0

    def follow_fid_range(self, start_fid, end_fid, delay_range=(3, 8), max_follows=None):
        """Follow users in FID range"""
        try:
            followed_count = 0
            processed_count = 0
            
            print(f"{colored_text(f'🎯 Account {self.account_index}: Following FID range {start_fid}-{end_fid}', Colors.CYAN)}")
            if max_follows:
                print(f"{colored_text(f'   📊 Max follows limit: {max_follows}', Colors.WHITE)}")
            
            # Generate random FID list from range
            fid_list = list(range(start_fid, end_fid + 1))
            random.shuffle(fid_list)  # Randomize order to avoid pattern
            
            for target_fid in fid_list:
                if shutdown_flag.is_set():
                    break
                    
                if max_follows and followed_count >= max_follows:
                    print(f"{colored_text(f'📊 Account {self.account_index}: Max follows limit ({max_follows}) reached', Colors.YELLOW)}")
                    break
                
                processed_count += 1
                print(f"{colored_text(f'   🔄 Processing FID {target_fid} ({processed_count}/{len(fid_list)})...', Colors.CYAN)}")
                
                # Skip own FID
                if target_fid == self.user_id:
                    print(f"{colored_text(f'   ⏭️  Skipping own FID ({target_fid})', Colors.YELLOW)}")
                    continue
                
                # Get user info first
                target_info = self.get_user_info_by_fid(target_fid)
                if not target_info:
                    print(f"{colored_text(f'   ⏭️  Skipping invalid FID {target_fid} (user not found)', Colors.YELLOW)}")
                    continue
                
                print(f"{colored_text(f'   👤 Found user: @{target_info['username']} (Followers: {target_info['follower_count']})', Colors.WHITE)}")
                
                # Follow the user
                if self.follow_user(target_fid, target_info):
                    followed_count += 1
                    print(f"{colored_text(f'   ✅ Follow successful! Total follows: {followed_count}', Colors.GREEN)}")
                    
                    # Random delay between follows
                    delay = random.uniform(delay_range[0], delay_range[1])
                    print(f"{colored_text(f'   ⏳ Waiting {delay:.1f}s before next follow...', Colors.CYAN)}")
                    time.sleep(delay)
                else:
                    print(f"{colored_text(f'   ❌ Follow failed for FID {target_fid}', Colors.RED)}")
                    # Small delay even on failure
                    time.sleep(2)
                
                # Show progress every 10 follows
                if followed_count > 0 and followed_count % 10 == 0:
                    print(f"{colored_text(f'📈 Account {self.account_index}: Progress - {followed_count} follows completed', Colors.MAGENTA)}")
            
            print(f"{colored_text(f'📊 Account {self.account_index}: FID range follow completed - {followed_count} new follows', Colors.MAGENTA)}")
            return followed_count
            
        except Exception as e:
            print(f"{colored_text(f'❌ Account {self.account_index}: Error in follow_fid_range: {e}', Colors.RED)}")
            return 0

    def get_follow_stats(self):
        """Get follow statistics"""
        return {
            'account_index': self.account_index,
            'username': self.username,
            'follows_made': self.follows_made,
            'follows_skipped': self.follows_skipped,
            'follows_failed': self.follows_failed,
            'total_processed': self.follows_made + self.follows_skipped + self.follows_failed
        }

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

def initialize_all_accounts(account_info_list):
    """Initialize all bot instances and get account data"""
    try:
        print(f"\n{colored_text('🔍 INITIALIZING ALL ACCOUNTS...', Colors.BOLD + Colors.YELLOW)}")
        print(f"{colored_text('═' * 70, Colors.YELLOW)}")
        
        all_accounts_data = []
        
        for i, acc_info in enumerate(account_info_list, 1):
            try:
                print(f"\n{colored_text(f'🔄 Initializing Account {i}...', Colors.CYAN)}")
                bot = FarcasterAutoFollow(acc_info['token'], i)
                
                if bot.user_id:
                    account_data = {
                        'bot_instance': bot,
                        'account_index': i,
                        'user_id': bot.user_id,
                        'username': bot.username,
                        'display_name': bot.display_name,
                        'token': acc_info['token']
                    }
                    all_accounts_data.append(account_data)
                    print(f"{colored_text(f'✅ Account {i} initialized: @{bot.username} (FID: {bot.user_id})', Colors.GREEN)}")
                else:
                    print(f"{colored_text(f'❌ Account {i} failed to initialize', Colors.RED)}")
                    
                time.sleep(1)  # Small delay between initializations
                
            except Exception as e:
                print(f"{colored_text(f'❌ Account {i} error: {e}', Colors.RED)}")
        
        print(f"\n{colored_text(f'✅ Initialized {len(all_accounts_data)}/{len(account_info_list)} accounts successfully', Colors.GREEN)}")
        return all_accounts_data
        
    except Exception as e:
        print(f"{colored_text(f'❌ Error initializing accounts: {e}', Colors.RED)}")
        return []

def process_account_mutual_follows(bot_instance, all_accounts_data, delay_range, max_follows, results_queue):
    """Process mutual follows for a single account in thread"""
    try:
        account_index = bot_instance.account_index
        
        print(f"{colored_text(f'🔄 [Thread-{account_index}] Starting mutual follow process...', Colors.CYAN)}")
        
        # Follow other accounts with limit
        follows_made = bot_instance.follow_accounts_from_list(all_accounts_data, delay_range, max_follows)
        
        result = {
            'account_index': account_index,
            'follows_made': follows_made,
            'success': follows_made > 0,
            'stats': bot_instance.get_follow_stats()
        }
        
        results_queue.put(result)
        print(f"{colored_text(f'✅ [Thread-{account_index}] Mutual follow process completed ({follows_made} follows)', Colors.GREEN)}")
        
        return result
        
    except Exception as e:
        error_result = {
            'account_index': bot_instance.account_index,
            'success': False,
            'error': str(e),
            'follows_made': 0
        }
        results_queue.put(error_result)
        print(f"{colored_text(f'❌ [Thread-{bot_instance.account_index}] Error: {e}', Colors.RED)}")
        return error_result

def process_account_fid_follows(bot_instance, start_fid, end_fid, delay_range, max_follows, results_queue):
    """Process FID range follows for a single account in thread"""
    try:
        account_index = bot_instance.account_index
        
        print(f"{colored_text(f'🔄 [Thread-{account_index}] Starting FID range follow process...', Colors.CYAN)}")
        
        # Follow FID range
        follows_made = bot_instance.follow_fid_range(start_fid, end_fid, delay_range, max_follows)
        
        result = {
            'account_index': account_index,
            'follows_made': follows_made,
            'success': follows_made > 0,
            'stats': bot_instance.get_follow_stats()
        }
        
        results_queue.put(result)
        print(f"{colored_text(f'✅ [Thread-{account_index}] FID range follow process completed ({follows_made} follows)', Colors.GREEN)}")
        
        return result
        
    except Exception as e:
        error_result = {
            'account_index': bot_instance.account_index,
            'success': False,
            'error': str(e),
            'follows_made': 0
        }
        results_queue.put(error_result)
        print(f"{colored_text(f'❌ [Thread-{bot_instance.account_index}] Error: {e}', Colors.RED)}")
        return error_result

def threaded_mutual_follow_process_with_range(all_accounts_data, delay_range=(3, 8), follow_config=None):
    """Main threaded process for mutual follow automation with random range support"""
    try:
        print(f"\n{colored_text('🚀 STARTING THREADED MUTUAL FOLLOW PROCESS (RANDOM RANGE)', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        
        if follow_config['type'] == 'range':
            print(f"{colored_text(f'🎯 Random follow range: {follow_config['min']}-{follow_config['max']} per account', Colors.MAGENTA)}")
        
        print(f"{colored_text(f'🧵 Starting {len(all_accounts_data)} mutual follow threads...', Colors.MAGENTA)}")
        
        results_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=len(all_accounts_data)) as executor:
            # Submit mutual follow tasks with random counts
            futures = []
            for acc_data in all_accounts_data:
                # Generate random follow count for this account
                if follow_config['type'] == 'range':
                    random_follow_count = random.randint(follow_config['min'], follow_config['max'])
                    print(f"{colored_text(f'🎲 Account {acc_data['account_index']}: Will follow {random_follow_count} random accounts', Colors.CYAN)}")
                else:
                    random_follow_count = follow_config.get('count', None)
                
                future = executor.submit(
                    process_account_mutual_follows, 
                    acc_data['bot_instance'], 
                    all_accounts_data, 
                    delay_range, 
                    random_follow_count, 
                    results_queue
                )
                futures.append(future)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{colored_text(f'❌ Mutual follow thread error: {e}', Colors.RED)}")
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Summary
        total_follows = sum(r.get('follows_made', 0) for r in results)
        successful_accounts = len([r for r in results if r.get('success', False)])
        
        print(f"\n{colored_text('📊 RANDOM RANGE MUTUAL FOLLOW SUMMARY', Colors.BOLD + Colors.GREEN)}")
        summary_lines = [
            f"👥 Total follows made: {total_follows}",
            f"✅ Successful accounts: {successful_accounts}/{len(all_accounts_data)}",
            f"🎯 Average follows per account: {total_follows / len(all_accounts_data) if all_accounts_data else 0:.1f}"
        ]
        if follow_config['type'] == 'range':
            summary_lines.append(f"🎲 Random range: {follow_config['min']}-{follow_config['max']} per account")
        
        print_colored_box("RANDOM MUTUAL FOLLOW RESULTS", summary_lines, Colors.GREEN)
        
        # Individual account summary
        print(f"\n{colored_text('👤 INDIVIDUAL ACCOUNT SUMMARY', Colors.BOLD + Colors.CYAN)}")
        for result in results:
            stats = result.get('stats', {})
            print(f"{colored_text(f'Account {result.get('account_index')} (@{stats.get('username', 'Unknown')}):', Colors.WHITE)}")
            print(f"  👥 Follows made: {stats.get('follows_made', 0)}")
            print(f"  ⏭️  Follows skipped: {stats.get('follows_skipped', 0)}")
            print(f"  ❌ Follows failed: {stats.get('follows_failed', 0)}")
        
        print(f"\n{colored_text('🎉 RANDOM RANGE MUTUAL FOLLOW AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Process stopped by user', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Unexpected error: {e}', Colors.RED)}")

def threaded_mutual_follow_process(all_accounts_data, delay_range=(3, 8), max_follows_per_account=None):
    """Main threaded process for mutual follow automation"""
    try:
        print(f"\n{colored_text('🚀 STARTING THREADED MUTUAL FOLLOW PROCESS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        
        print(f"{colored_text(f'🧵 Starting {len(all_accounts_data)} mutual follow threads...', Colors.MAGENTA)}")
        if max_follows_per_account:
            print(f"{colored_text(f'📊 Max follows per account: {max_follows_per_account}', Colors.MAGENTA)}")
        
        results_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=len(all_accounts_data)) as executor:
            # Submit mutual follow tasks
            futures = [
                executor.submit(process_account_mutual_follows, acc_data['bot_instance'], all_accounts_data, delay_range, max_follows_per_account, results_queue)
                for acc_data in all_accounts_data
            ]
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{colored_text(f'❌ Mutual follow thread error: {e}', Colors.RED)}")
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Summary
        total_follows = sum(r.get('follows_made', 0) for r in results)
        successful_accounts = len([r for r in results if r.get('success', False)])
        
        print(f"\n{colored_text('📊 MUTUAL FOLLOW SUMMARY', Colors.BOLD + Colors.GREEN)}")
        summary_lines = [
            f"👥 Total follows made: {total_follows}",
            f"✅ Successful accounts: {successful_accounts}/{len(all_accounts_data)}",
            f"🎯 Average follows per account: {total_follows / len(all_accounts_data) if all_accounts_data else 0:.1f}"
        ]
        if max_follows_per_account:
            summary_lines.append(f"📊 Max follows per account: {max_follows_per_account}")
        
        print_colored_box("MUTUAL FOLLOW RESULTS", summary_lines, Colors.GREEN)
        
        # Individual account summary
        print(f"\n{colored_text('👤 INDIVIDUAL ACCOUNT SUMMARY', Colors.BOLD + Colors.CYAN)}")
        for result in results:
            stats = result.get('stats', {})
            print(f"{colored_text(f'Account {result.get('account_index')} (@{stats.get('username', 'Unknown')}):', Colors.WHITE)}")
            print(f"  👥 Follows made: {stats.get('follows_made', 0)}")
            print(f"  ⏭️  Follows skipped: {stats.get('follows_skipped', 0)}")
            print(f"  ❌ Follows failed: {stats.get('follows_failed', 0)}")
        
        print(f"\n{colored_text('🎉 MUTUAL FOLLOW AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Process stopped by user', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Unexpected error: {e}', Colors.RED)}")

def threaded_fid_follow_process_with_range(all_accounts_data, start_fid, end_fid, delay_range=(3, 8), follow_limit_config=None):
    """Main threaded process for FID range follow automation with random range support"""
    try:
        print(f"\n{colored_text('🚀 STARTING THREADED FID RANGE FOLLOW PROCESS (RANDOM RANGE)', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        
        print(f"{colored_text(f'🎯 Target FID range: {start_fid} - {end_fid}', Colors.MAGENTA)}")
        
        if follow_limit_config['type'] == 'range':
            print(f"{colored_text(f'🎲 Random follow range: {follow_limit_config['min']}-{follow_limit_config['max']} per account', Colors.MAGENTA)}")
        
        print(f"{colored_text(f'🧵 Starting {len(all_accounts_data)} FID follow threads...', Colors.MAGENTA)}")
        
        results_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=len(all_accounts_data)) as executor:
            # Submit FID follow tasks with random counts
            futures = []
            for acc_data in all_accounts_data:
                # Generate random follow count for this account
                if follow_limit_config['type'] == 'range':
                    random_follow_count = random.randint(follow_limit_config['min'], follow_limit_config['max'])
                    print(f"{colored_text(f'🎲 Account {acc_data['account_index']}: Will follow {random_follow_count} random FIDs', Colors.CYAN)}")
                else:
                    random_follow_count = follow_limit_config.get('count', None)
                
                future = executor.submit(
                    process_account_fid_follows, 
                    acc_data['bot_instance'], 
                    start_fid, 
                    end_fid, 
                    delay_range, 
                    random_follow_count, 
                    results_queue
                )
                futures.append(future)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{colored_text(f'❌ FID follow thread error: {e}', Colors.RED)}")
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Summary
        total_follows = sum(r.get('follows_made', 0) for r in results)
        successful_accounts = len([r for r in results if r.get('success', False)])
        
        print(f"\n{colored_text('📊 RANDOM RANGE FID FOLLOW SUMMARY', Colors.BOLD + Colors.GREEN)}")
        summary_lines = [
            f"🎯 Target range: FID {start_fid} - {end_fid}",
            f"👥 Total follows made: {total_follows}",
            f"✅ Successful accounts: {successful_accounts}/{len(all_accounts_data)}",
            f"📊 Average follows per account: {total_follows / len(all_accounts_data) if all_accounts_data else 0:.1f}"
        ]
        if follow_limit_config['type'] == 'range':
            summary_lines.append(f"🎲 Random range: {follow_limit_config['min']}-{follow_limit_config['max']} per account")
        
        print_colored_box("RANDOM FID FOLLOW RESULTS", summary_lines, Colors.GREEN)
        
        # Individual account summary
        print(f"\n{colored_text('👤 INDIVIDUAL ACCOUNT SUMMARY', Colors.BOLD + Colors.CYAN)}")
        for result in results:
            stats = result.get('stats', {})
            print(f"{colored_text(f'Account {result.get('account_index')} (@{stats.get('username', 'Unknown')}):', Colors.WHITE)}")
            print(f"  👥 Follows made: {stats.get('follows_made', 0)}")
            print(f"  ⏭️  Follows skipped: {stats.get('follows_skipped', 0)}")
            print(f"  ❌ Follows failed: {stats.get('follows_failed', 0)}")
        
        print(f"\n{colored_text('🎉 RANDOM RANGE FID FOLLOW AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Process stopped by user', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Unexpected error: {e}', Colors.RED)}")

def threaded_fid_follow_process(all_accounts_data, start_fid, end_fid, delay_range=(3, 8), max_follows_per_account=None):
    """Main threaded process for FID range follow automation"""
    try:
        print(f"\n{colored_text('🚀 STARTING THREADED FID RANGE FOLLOW PROCESS', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('═' * 70, Colors.CYAN)}")
        
        print(f"{colored_text(f'🎯 Target FID range: {start_fid} - {end_fid}', Colors.MAGENTA)}")
        print(f"{colored_text(f'🧵 Starting {len(all_accounts_data)} FID follow threads...', Colors.MAGENTA)}")
        if max_follows_per_account:
            print(f"{colored_text(f'📊 Max follows per account: {max_follows_per_account}', Colors.MAGENTA)}")
        
        results_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=len(all_accounts_data)) as executor:
            # Submit FID follow tasks
            futures = [
                executor.submit(process_account_fid_follows, acc_data['bot_instance'], start_fid, end_fid, delay_range, max_follows_per_account, results_queue)
                for acc_data in all_accounts_data
            ]
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"{colored_text(f'❌ FID follow thread error: {e}', Colors.RED)}")
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Summary
        total_follows = sum(r.get('follows_made', 0) for r in results)
        successful_accounts = len([r for r in results if r.get('success', False)])
        
        print(f"\n{colored_text('📊 FID RANGE FOLLOW SUMMARY', Colors.BOLD + Colors.GREEN)}")
        print_colored_box("FID FOLLOW RESULTS", [
            f"🎯 Target range: FID {start_fid} - {end_fid}",
            f"👥 Total follows made: {total_follows}",
            f"✅ Successful accounts: {successful_accounts}/{len(all_accounts_data)}",
            f"📊 Average follows per account: {total_follows / len(all_accounts_data) if all_accounts_data else 0:.1f}"
        ], Colors.GREEN)
        
        # Individual account summary
        print(f"\n{colored_text('👤 INDIVIDUAL ACCOUNT SUMMARY', Colors.BOLD + Colors.CYAN)}")
        for result in results:
            stats = result.get('stats', {})
            print(f"{colored_text(f'Account {result.get('account_index')} (@{stats.get('username', 'Unknown')}):', Colors.WHITE)}")
            print(f"  👥 Follows made: {stats.get('follows_made', 0)}")
            print(f"  ⏭️  Follows skipped: {stats.get('follows_skipped', 0)}")
            print(f"  ❌ Follows failed: {stats.get('follows_failed', 0)}")
        
        print(f"\n{colored_text('🎉 FID RANGE FOLLOW AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text('⛔ Process stopped by user', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Unexpected error: {e}', Colors.RED)}")

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
    """Main function with advanced follow automation"""
    # Clear screen for better presentation
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Animated header
    header_lines = [
        "╔══════════════════════════════════════════════════════════════════╗",
        "║           🚀 FARCASTER AUTO FOLLOW SCRIPT 🚀                   ║",
        "║                    ADVANCED MULTI-ACCOUNT EDITION               ║",
        "║                      WITH ANTI-DETECTION SYSTEM                 ║",
        "╠══════════════════════════════════════════════════════════════════╣",
        "║  👥 Auto Mutual Follow Between Accounts                        ║",
        "║  🎯 Auto Follow Target FID Range (e.g., 1-1000)               ║", 
        "║  🧵 Multi-Threading for Maximum Performance                     ║",
        "║  🔄 Smart Follow Detection & Skip Already Followed             ║",
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
    
    # Main menu BEFORE initializing accounts
    print(f"\n{colored_text('🎛️  AUTO FOLLOW CONTROL PANEL', Colors.BOLD + Colors.CYAN)}")
    menu_lines = [
        "┌─────────────────────────────────────────────────────────────────┐",
        "│  1. 👥 Mutual Follow (Accounts follow each other)              │",
        "│  2. 🎯 Follow FID Range (e.g., 1-1000)                        │",
        "│  3. 🔄 Combined Follow (Mutual + FID Range)                    │",
        "│  4. 📊 Check Follow Status for All Accounts                   │"
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
        # Mutual follow configuration FIRST - before initializing accounts
        print(f"\n{colored_text('⚙️  MUTUAL FOLLOW CONFIGURATION', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('💡 Accounts will follow each other based on your settings', Colors.CYAN)}")
        print(f"{colored_text(f'📊 Total accounts available: {len(account_info)}', Colors.WHITE)}")
        
        # Ask if user wants to proceed
        proceed = input(f"\n{colored_text('Do you want to proceed with mutual follow? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if proceed not in ['y', 'yes']:
            print(f"{colored_text('❌ Mutual follow cancelled by user', Colors.YELLOW)}")
            return
        
        try:
            # Ask for custom follow range
            max_accounts = len(account_info) - 1  # Exclude self
            print(f"\n{colored_text('👥 FOLLOW COUNT CONFIGURATION', Colors.BOLD + Colors.CYAN)}")
            print(f"{colored_text(f'   � Total accounts loaded: {len(account_info)}', Colors.WHITE)}")
            print(f"{colored_text(f'   📊 Max possible follows per account: {max_accounts}', Colors.WHITE)}")
            
            # Ask for random follow range
            follow_range_input = input(f"{colored_text('👥 Enter follow range per account (e.g., 40-50, or just 30 for exact): ', Colors.CYAN)}").strip()
            
            if '-' in follow_range_input:
                # Range format like "40-50"
                min_follows, max_follows = map(int, follow_range_input.split('-'))
                min_follows = max(1, min(min_follows, max_accounts))
                max_follows = max(min_follows, min(max_follows, max_accounts))
                follow_config = {'type': 'range', 'min': min_follows, 'max': max_follows}
                print(f"{colored_text(f'✅ Each account will follow: {min_follows}-{max_follows} random accounts', Colors.GREEN)}")
            elif follow_range_input.isdigit():
                # Exact number like "30"
                exact_follows = max(1, min(int(follow_range_input), max_accounts))
                follow_config = {'type': 'exact', 'count': exact_follows}
                print(f"{colored_text(f'✅ Each account will follow exactly: {exact_follows} accounts', Colors.GREEN)}")
            else:
                # Default to all
                follow_config = {'type': 'all'}
                print(f"{colored_text(f'✅ Each account will follow: ALL other accounts ({max_accounts})', Colors.GREEN)}")
            
            delay_min = int(input(f"{colored_text('⏳ Min delay between follows (seconds): ', Colors.CYAN)}") or "3")
            delay_max = int(input(f"{colored_text('⏳ Max delay between follows (seconds): ', Colors.CYAN)}") or "8")
            delay_range = (max(1, delay_min), max(delay_min + 1, delay_max))
            
        except ValueError:
            print(f"{colored_text('⚠️  Invalid input, using defaults', Colors.YELLOW)}")
            follow_config = {'type': 'all'}
            delay_range = (3, 8)
        
        # Show configuration summary
        print(f"\n{colored_text('✅ MUTUAL FOLLOW CONFIGURATION SUMMARY', Colors.GREEN)}")
        print(f"  👥 Total accounts: {len(account_info)}")
        if follow_config['type'] == 'range':
            print(f"  📊 Each account will follow: {follow_config['min']}-{follow_config['max']} random accounts")
            expected_avg = (follow_config['min'] + follow_config['max']) / 2
            print(f"  📊 Expected total follows: ~{len(account_info) * expected_avg:.0f}")
        elif follow_config['type'] == 'exact':
            print(f"  📊 Each account will follow: exactly {follow_config['count']} accounts")
            print(f"  📊 Expected total follows: {len(account_info) * follow_config['count']}")
        else:
            print(f"  📊 Each account will follow: ALL other accounts ({max_accounts} each)")
            print(f"  📊 Expected total follows: {len(account_info) * max_accounts}")
        print(f"  ⏳ Delay range: {delay_range[0]}-{delay_range[1]}s")
        
        confirm = input(f"\n{colored_text('Start mutual follow process? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if confirm not in ['y', 'yes', '']:
            print(f"{colored_text('❌ Mutual follow cancelled by user', Colors.YELLOW)}")
            return
            
        # NOW initialize accounts after configuration is confirmed
        all_accounts_data = initialize_all_accounts(account_info)
        if not all_accounts_data:
            print(colored_text("❌ Error: No accounts initialized successfully!", Colors.RED))
            return
        
        # Convert follow_config to max_follows_per_account for the function
        if follow_config['type'] == 'range':
            # Pass the range info to the threaded function
            threaded_mutual_follow_process_with_range(all_accounts_data, delay_range, follow_config)
        elif follow_config['type'] == 'exact':
            threaded_mutual_follow_process(all_accounts_data, delay_range, follow_config['count'])
        else:
            threaded_mutual_follow_process(all_accounts_data, delay_range, None)
            
    elif choice == "2":
        # FID range follow configuration FIRST - before initializing accounts
        print(f"\n{colored_text('⚙️  FID RANGE FOLLOW CONFIGURATION', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('🎯 Follow users in custom FID range (unlimited flexibility)', Colors.CYAN)}")
        print(f"{colored_text('💡 Examples: 1-100, 500-900, 1-10000, etc.', Colors.WHITE)}")
        
        # Ask if user wants to proceed
        proceed = input(f"\n{colored_text('Do you want to proceed with FID range follow? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if proceed not in ['y', 'yes']:
            print(f"{colored_text('❌ FID range follow cancelled by user', Colors.YELLOW)}")
            return
        
        try:
            start_fid = int(input(f"{colored_text('🎯 Start FID (minimum 1): ', Colors.CYAN)}") or "1")
            end_fid = int(input(f"{colored_text('🎯 End FID (e.g., 100, 500, 1000, 10000): ', Colors.CYAN)}") or "1000")
            
            # Validate FID range
            if start_fid < 1:
                print(f"{colored_text('⚠️  Start FID must be at least 1. Setting to 1.', Colors.YELLOW)}")
                start_fid = 1
            
            if end_fid < start_fid:
                print(f"{colored_text('⚠️  End FID must be greater than Start FID. Swapping values.', Colors.YELLOW)}")
                start_fid, end_fid = end_fid, start_fid
            
            # Ask for custom follow range per account
            total_fids = end_fid - start_fid + 1
            print(f"\n{colored_text('📊 FOLLOW LIMIT CONFIGURATION', Colors.BOLD + Colors.CYAN)}")
            print(f"{colored_text(f'   🎯 Total FIDs in range: {total_fids}', Colors.WHITE)}")
            print(f"{colored_text(f'   👥 Total accounts: {len(account_info)}', Colors.WHITE)}")
            
            # Ask for random follow range per account
            follow_limit_input = input(f"{colored_text('📊 Max follows per account (e.g., 90-100 for random, or just 50 for exact, enter for unlimited): ', Colors.CYAN)}").strip()
            
            if '-' in follow_limit_input:
                # Range format like "90-100"
                min_follows, max_follows = map(int, follow_limit_input.split('-'))
                min_follows = max(1, min_follows)
                max_follows = max(min_follows, max_follows)
                follow_limit_config = {'type': 'range', 'min': min_follows, 'max': max_follows}
                print(f"{colored_text(f'✅ Each account will follow: {min_follows}-{max_follows} random FIDs', Colors.GREEN)}")
            elif follow_limit_input.isdigit():
                # Exact number like "50"
                exact_follows = max(1, int(follow_limit_input))
                follow_limit_config = {'type': 'exact', 'count': exact_follows}
                print(f"{colored_text(f'✅ Each account will follow exactly: {exact_follows} FIDs', Colors.GREEN)}")
            else:
                # Default to unlimited
                follow_limit_config = {'type': 'unlimited'}
                print(f"{colored_text('✅ Each account will follow: UNLIMITED FIDs in range', Colors.GREEN)}")
            
            delay_min = int(input(f"{colored_text('⏳ Min delay between follows (seconds): ', Colors.CYAN)}") or "3")
            delay_max = int(input(f"{colored_text('⏳ Max delay between follows (seconds): ', Colors.CYAN)}") or "8")
            delay_range = (max(1, delay_min), max(delay_min + 1, delay_max))
            
        except ValueError:
            print(f"{colored_text('⚠️  Invalid input, using defaults', Colors.YELLOW)}")
            start_fid, end_fid = 1, 1000
            follow_limit_config = {'type': 'unlimited'}
            delay_range = (3, 8)
        
        # Show configuration summary
        print(f"\n{colored_text('✅ FID RANGE FOLLOW CONFIGURATION', Colors.GREEN)}")
        print(f"  🎯 FID range: {start_fid} - {end_fid} ({end_fid - start_fid + 1} total FIDs)")
        print(f"  👥 Accounts: {len(account_info)}")
        
        if follow_limit_config['type'] == 'range':
            print(f"  📊 Each account will follow: {follow_limit_config['min']}-{follow_limit_config['max']} random FIDs")
            expected_avg = (follow_limit_config['min'] + follow_limit_config['max']) / 2
            print(f"  📊 Expected total follows: ~{len(account_info) * expected_avg:.0f}")
        elif follow_limit_config['type'] == 'exact':
            print(f"  📊 Each account will follow: exactly {follow_limit_config['count']} FIDs")
            print(f"  📊 Expected total follows: {len(account_info) * follow_limit_config['count']}")
        else:
            print(f"  📊 Max follows per account: Unlimited")
            print(f"  📊 Expected total follows: Depends on execution")
        
        print(f"  ⏳ Delay range: {delay_range[0]}-{delay_range[1]}s")
        
        confirm = input(f"\n{colored_text('Start FID range follow process? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if confirm not in ['y', 'yes', '']:
            print(f"{colored_text('❌ FID range follow cancelled by user', Colors.YELLOW)}")
            return
            
        # NOW initialize accounts after configuration is confirmed
        all_accounts_data = initialize_all_accounts(account_info)
        if not all_accounts_data:
            print(colored_text("❌ Error: No accounts initialized successfully!", Colors.RED))
            return
        
        # Convert follow_limit_config and start FID range follow process
        if follow_limit_config['type'] == 'range':
            # Pass the range info to the new threaded function
            threaded_fid_follow_process_with_range(all_accounts_data, start_fid, end_fid, delay_range, follow_limit_config)
        elif follow_limit_config['type'] == 'exact':
            threaded_fid_follow_process(all_accounts_data, start_fid, end_fid, delay_range, follow_limit_config['count'])
        else:
            threaded_fid_follow_process(all_accounts_data, start_fid, end_fid, delay_range, None)
        
    elif choice == "3":
        # Combined follow process configuration FIRST - before initializing accounts
        print(f"\n{colored_text('⚙️  COMBINED FOLLOW CONFIGURATION', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('🔄 First: Mutual follow, Then: FID range follow', Colors.CYAN)}")
        
        # Ask if user wants to proceed
        proceed = input(f"\n{colored_text('Do you want to proceed with combined follow process? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if proceed not in ['y', 'yes']:
            print(f"{colored_text('❌ Combined follow cancelled by user', Colors.YELLOW)}")
            return
        
        try:
            # Mutual follow settings
            print(f"\n{colored_text('👥 PHASE 1: MUTUAL FOLLOW SETTINGS', Colors.BOLD + Colors.CYAN)}")
            max_accounts = len(account_info) - 1
            print(f"{colored_text(f'   👥 Total accounts loaded: {len(account_info)}', Colors.WHITE)}")
            print(f"{colored_text(f'   � Max possible follows per account: {max_accounts}', Colors.WHITE)}")
            
            # Ask for random follow range (same as option 1)
            mutual_follow_range_input = input(f"{colored_text('👥 Enter follow range per account (e.g., 40-50, or just 30 for exact): ', Colors.CYAN)}").strip()
            
            if '-' in mutual_follow_range_input:
                # Range format like "40-50"
                min_follows, max_follows = map(int, mutual_follow_range_input.split('-'))
                min_follows = max(1, min(min_follows, max_accounts))
                max_follows = max(min_follows, min(max_follows, max_accounts))
                mutual_follow_config = {'type': 'range', 'min': min_follows, 'max': max_follows}
                print(f"{colored_text(f'✅ Each account will follow: {min_follows}-{max_follows} random accounts', Colors.GREEN)}")
                mutual_max_follows = None  # Will be handled by the range function
            elif mutual_follow_range_input.isdigit():
                # Exact number like "30"
                exact_follows = max(1, min(int(mutual_follow_range_input), max_accounts))
                mutual_follow_config = {'type': 'exact', 'count': exact_follows}
                mutual_max_follows = exact_follows
                print(f"{colored_text(f'✅ Each account will follow exactly: {exact_follows} accounts', Colors.GREEN)}")
            else:
                # Default to all
                mutual_follow_config = {'type': 'all'}
                mutual_max_follows = None
                print(f"{colored_text(f'✅ Each account will follow: ALL other accounts ({max_accounts})', Colors.GREEN)}")
            
            mutual_delay_min = int(input(f"{colored_text('👥 Mutual follow - Min delay (seconds): ', Colors.CYAN)}") or "3")
            mutual_delay_max = int(input(f"{colored_text('👥 Mutual follow - Max delay (seconds): ', Colors.CYAN)}") or "8")
            mutual_delay_range = (max(1, mutual_delay_min), max(mutual_delay_min + 1, mutual_delay_max))
            
            # FID range settings
            print(f"\n{colored_text('🎯 PHASE 2: FID RANGE FOLLOW SETTINGS', Colors.BOLD + Colors.CYAN)}")
            start_fid = int(input(f"{colored_text('🎯 Start FID (minimum 1): ', Colors.CYAN)}") or "1")
            end_fid = int(input(f"{colored_text('🎯 End FID (e.g., 100, 500, 1000, 10000): ', Colors.CYAN)}") or "1000")
            
            # Validate FID range
            if start_fid < 1:
                print(f"{colored_text('⚠️  Start FID must be at least 1. Setting to 1.', Colors.YELLOW)}")
                start_fid = 1
            
            if end_fid < start_fid:
                print(f"{colored_text('⚠️  End FID must be greater than Start FID. Swapping values.', Colors.YELLOW)}")
                start_fid, end_fid = end_fid, start_fid
            
            # Ask for custom follow range per account (same as option 2)
            total_fids = end_fid - start_fid + 1
            print(f"{colored_text(f'   🎯 Total FIDs in range: {total_fids}', Colors.WHITE)}")
            print(f"{colored_text(f'   👥 Total accounts: {len(account_info)}', Colors.WHITE)}")
            
            # Ask for random follow range per account
            fid_follow_limit_input = input(f"{colored_text('📊 FID range - Max follows per account (e.g., 90-100 for random, or just 50 for exact, enter for unlimited): ', Colors.CYAN)}").strip()
            
            if '-' in fid_follow_limit_input:
                # Range format like "90-100"
                min_follows, max_follows = map(int, fid_follow_limit_input.split('-'))
                min_follows = max(1, min_follows)
                max_follows = max(min_follows, max_follows)
                fid_follow_limit_config = {'type': 'range', 'min': min_follows, 'max': max_follows}
                print(f"{colored_text(f'✅ Each account will follow: {min_follows}-{max_follows} random FIDs', Colors.GREEN)}")
            elif fid_follow_limit_input.isdigit():
                # Exact number like "50"
                exact_follows = max(1, int(fid_follow_limit_input))
                fid_follow_limit_config = {'type': 'exact', 'count': exact_follows}
                print(f"{colored_text(f'✅ Each account will follow exactly: {exact_follows} FIDs', Colors.GREEN)}")
            else:
                # Default to unlimited
                fid_follow_limit_config = {'type': 'unlimited'}
                print(f"{colored_text('✅ Each account will follow: UNLIMITED FIDs in range', Colors.GREEN)}")
            
            # Keep the old max_follows for backward compatibility
            max_follows = fid_follow_limit_config.get('count', None) if fid_follow_limit_config['type'] == 'exact' else None
            
            fid_delay_min = int(input(f"{colored_text('🎯 FID range - Min delay (seconds): ', Colors.CYAN)}") or "3")
            fid_delay_max = int(input(f"{colored_text('🎯 FID range - Max delay (seconds): ', Colors.CYAN)}") or "8")
            fid_delay_range = (max(1, fid_delay_min), max(fid_delay_min + 1, fid_delay_max))
            
        except ValueError:
            print(f"{colored_text('⚠️  Invalid input, using defaults', Colors.YELLOW)}")
            mutual_follow_config = {'type': 'all'}
            mutual_max_follows = None
            mutual_delay_range = (3, 8)
            start_fid, end_fid = 1, 1000
            fid_follow_limit_config = {'type': 'unlimited'}
            max_follows = None
            fid_delay_range = (3, 8)
        
        print(f"\n{colored_text('✅ COMBINED FOLLOW CONFIGURATION', Colors.GREEN)}")
        print(f"  Phase 1 - Mutual Follow:")
        print(f"    👥 Accounts: {len(account_info)}")
        
        if mutual_follow_config['type'] == 'range':
            print(f"    📊 Each account will follow: {mutual_follow_config['min']}-{mutual_follow_config['max']} random accounts")
            expected_avg = (mutual_follow_config['min'] + mutual_follow_config['max']) / 2
            print(f"    📊 Expected total follows: ~{len(account_info) * expected_avg:.0f}")
        elif mutual_follow_config['type'] == 'exact':
            print(f"    📊 Each account will follow: exactly {mutual_follow_config['count']} accounts")
            print(f"    📊 Expected total follows: {len(account_info) * mutual_follow_config['count']}")
        else:
            print(f"    📊 Each follows: ALL others ({max_accounts})")
            print(f"    📊 Expected total follows: {len(account_info) * max_accounts}")
        
        print(f"    ⏳ Delay: {mutual_delay_range[0]}-{mutual_delay_range[1]}s")
        print(f"  Phase 2 - FID Range Follow:")
        print(f"    🎯 Range: {start_fid}-{end_fid}")
        
        if fid_follow_limit_config['type'] == 'range':
            print(f"    📊 Each account will follow: {fid_follow_limit_config['min']}-{fid_follow_limit_config['max']} random FIDs")
            expected_avg = (fid_follow_limit_config['min'] + fid_follow_limit_config['max']) / 2
            print(f"    📊 Expected total follows: ~{len(account_info) * expected_avg:.0f}")
        elif fid_follow_limit_config['type'] == 'exact':
            print(f"    📊 Each account will follow: exactly {fid_follow_limit_config['count']} FIDs")
            print(f"    📊 Expected total follows: {len(account_info) * fid_follow_limit_config['count']}")
        else:
            print(f"    📊 Max per account: Unlimited")
            print(f"    📊 Expected total follows: Depends on execution")
        
        print(f"    ⏳ Delay: {fid_delay_range[0]}-{fid_delay_range[1]}s")
        
        confirm = input(f"\n{colored_text('Start combined follow process? (y/n): ', Colors.BOLD + Colors.YELLOW)}").strip().lower()
        if confirm not in ['y', 'yes', '']:
            print(f"{colored_text('❌ Combined follow cancelled by user', Colors.YELLOW)}")
            return
            
        # NOW initialize accounts after configuration is confirmed
        all_accounts_data = initialize_all_accounts(account_info)
        if not all_accounts_data:
            print(colored_text("❌ Error: No accounts initialized successfully!", Colors.RED))
            return
            
        # Phase 1: Mutual Follow
        print(f"\n{colored_text('🔄 PHASE 1: MUTUAL FOLLOW', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
        # Use the appropriate threaded function based on mutual_follow_config
        if mutual_follow_config['type'] == 'range':
            # Pass the range info to the threaded function with range support
            threaded_mutual_follow_process_with_range(all_accounts_data, mutual_delay_range, mutual_follow_config)
        elif mutual_follow_config['type'] == 'exact':
            threaded_mutual_follow_process(all_accounts_data, mutual_delay_range, mutual_follow_config['count'])
        else:
            threaded_mutual_follow_process(all_accounts_data, mutual_delay_range, None)
        
        # Ensure Phase 1 is completely finished before starting Phase 2
        print(f"\n{colored_text('✅ PHASE 1 COMPLETED! Waiting 10 seconds before Phase 2...', Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        time.sleep(10)
        
        # Phase 2: FID Range Follow
        print(f"\n{colored_text('🔄 PHASE 2: FID RANGE FOLLOW', Colors.BOLD + Colors.MAGENTA)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
        # Use the new threaded function with range support
        if fid_follow_limit_config['type'] == 'range':
            # Pass the range info to the new threaded function
            threaded_fid_follow_process_with_range(all_accounts_data, start_fid, end_fid, fid_delay_range, fid_follow_limit_config)
        elif fid_follow_limit_config['type'] == 'exact':
            threaded_fid_follow_process(all_accounts_data, start_fid, end_fid, fid_delay_range, fid_follow_limit_config['count'])
        else:
            threaded_fid_follow_process(all_accounts_data, start_fid, end_fid, fid_delay_range, None)
        
        # Final completion message
        print(f"\n{colored_text('🎉 COMBINED FOLLOW AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('✅ Both Phase 1 (Mutual) and Phase 2 (FID Range) are finished!', Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
    elif choice == "4":
        # Initialize accounts for status check
        all_accounts_data = initialize_all_accounts(account_info)
        if not all_accounts_data:
            print(colored_text("❌ Error: No accounts initialized successfully!", Colors.RED))
            return
            
        # Check follow status
        print(f"\n{colored_text('📊 CHECKING FOLLOW STATUS FOR ALL ACCOUNTS', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text('═' * 70, Colors.GREEN)}")
        
        for acc_data in all_accounts_data:
            bot = acc_data['bot_instance']
            stats = bot.get_follow_stats()
            
            print(f"\n{colored_text(f'Account {acc_data['account_index']} (@{acc_data['username']}):', Colors.CYAN)}")
            print(f"  🆔 FID: {acc_data['user_id']}")
            print(f"  📝 Display Name: {acc_data['display_name']}")
            print(f"  👥 Session follows made: {stats['follows_made']}")
            print(f"  ⏭️  Session follows skipped: {stats['follows_skipped']}")
            print(f"  ❌ Session follows failed: {stats['follows_failed']}")
            
            time.sleep(0.5)
        
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
            
            print(f"{colored_text('📊 PROXY STATISTICS', Colors.BOLD + Colors.CYAN)}")
            print(f"  Total Proxies: {proxy_stats.get('total_proxies', 0)}")
            print(f"  Working Proxies: {proxy_stats.get('working_proxies', 0)}")
            print(f"  Failed Proxies: {proxy_stats.get('failed_proxies', 0)}")
            print(f"  Active Sessions: {stats.get('active_sessions', 0)}")
            
        except Exception as e:
            print(f"{colored_text(f'❌ Proxy status check failed: {e}', Colors.RED)}")
        
    elif choice == str(max_choice):
        print(f"\n{colored_text('═' * 70, Colors.MAGENTA)}")
        print(f"{colored_text('👋 Thank you for using Farcaster Auto Follow!', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('💫 See you next time!', Colors.YELLOW)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
    elif choice == "5" and not ANTI_DETECTION_AVAILABLE:
        print(f"\n{colored_text('═' * 70, Colors.MAGENTA)}")
        print(f"{colored_text('👋 Thank you for using Farcaster Auto Follow!', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text('💫 See you next time!', Colors.YELLOW)}")
        print(f"{colored_text('═' * 70, Colors.MAGENTA)}")
        
    else:
        print(f"{colored_text(f'❌ Invalid choice! Please select 1-{max_choice}.', Colors.RED)}")

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()

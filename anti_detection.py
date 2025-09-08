#!/usr/bin/env python3
"""
Advanced Anti-Detection System for Farcaster Automation
Enhanced with TLS-Client, Session Persistence, Dynamic UA, Canvas Noise, and Behavioral Patterns
Maximum stealth for Farcaster automation
"""

import random
import time
import json
import base64
import hashlib
import uuid
import pickle
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import queue
import os

# Enhanced anti-detection imports
try:
    import tls_client
    TLS_CLIENT_AVAILABLE = True
    print("🔥 TLS-Client loaded - Maximum stealth enabled")
except ImportError:
    TLS_CLIENT_AVAILABLE = False
    print("⚠️ TLS-Client not available - install with: pip install tls-client")

try:
    import warnings
    warnings.filterwarnings("ignore", message=".*Error occurred during getting browser.*")
    from fake_useragent import UserAgent
    FAKE_UA_AVAILABLE = True
    print("✅ Fake-UserAgent loaded - Dynamic UA enabled")
except ImportError:
    FAKE_UA_AVAILABLE = False
    print("⚠️ Fake-UserAgent not available - install with: pip install fake-useragent")

# Fallback imports
# Fallback imports
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class EnhancedBrowserFingerprint:
    """Advanced browser fingerprints with session persistence and canvas noise"""
    
    # Updated user agents (2025)
    FALLBACK_USER_AGENTS = [
        # Chrome 125+ Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        
        # Chrome macOS latest
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        
        # Firefox latest
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        
        # Safari latest
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        
        # Edge latest  
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    ]
    
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
        (1280, 720), (1600, 900), (2560, 1440), (1920, 1200),
        (1680, 1050), (1280, 1024), (3840, 2160), (2048, 1152)
    ]
    
    LANGUAGES = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,id;q=0.8",
        "en-US,en;q=0.9,es;q=0.8",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.8,fr;q=0.7",
        "en-US,en;q=0.9,de;q=0.8",
        "en-US,en;q=0.9,pt;q=0.8",
        "en-US,en;q=0.9,ja;q=0.8",
        "en-US,en;q=0.9,zh;q=0.8"
    ]
    
    TIMEZONES = [
        "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Europe/Berlin",
        "Asia/Tokyo", "Asia/Shanghai", "Asia/Seoul",
        "Australia/Sydney", "America/Toronto", "America/Denver",
        "Asia/Jakarta", "Asia/Singapore", "Europe/Amsterdam"
    ]
    
    PLATFORMS = [
        "Win32", "MacIntel", "Linux x86_64", "Linux armv7l"
    ]
    
    # Human timing patterns
    HUMAN_PATTERNS = {
        'reading_time': (2, 8),
        'click_delay': (0.3, 1.2),
        'typing_speed': (0.05, 0.15),
        'scroll_pause': (0.5, 2.0),
        'tab_switch': (1, 4),
        'page_load_wait': (1.5, 4.0)
    }
    
    def __init__(self, account_id: str = None, auth_token: str = None):
        self.account_id = account_id or str(uuid.uuid4())
        self.auth_token = auth_token
        self.session_dir = "sessions"
        
        # Use simple filename since account_id already contains token prefix
        self.session_file = os.path.join(self.session_dir, f"{self.account_id}_fingerprint.pkl")
        
        # Initialize fake user agent if available
        if FAKE_UA_AVAILABLE:
            try:
                import sys
                import io
                # Suppress stderr for UserAgent initialization
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                self.ua_generator = UserAgent(browsers=['chrome', 'firefox', 'safari', 'edge'], fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
                sys.stderr = old_stderr
            except Exception as e:
                if 'old_stderr' in locals():
                    sys.stderr = old_stderr
                print(f"⚠️ Warning: UserAgent initialization failed: {e}")
                self.ua_generator = None
        else:
            self.ua_generator = None
        
        self.fingerprint = self._load_or_generate_fingerprint()
    
    def _find_matching_fingerprint_file(self) -> Optional[str]:
        """Find fingerprint file that matches first 10 characters of current token"""
        if not self.auth_token or len(self.auth_token) < 10:
            return None
            
        os.makedirs(self.session_dir, exist_ok=True)
        token_prefix = self.auth_token[:10]
        
        # Look for existing fingerprint files with same token prefix
        target_filename = f"{token_prefix}_fingerprint.pkl"
        target_path = os.path.join(self.session_dir, target_filename)
        
        if os.path.exists(target_path):
            return target_path
        
        # Also check old format files for backward compatibility
        for filename in os.listdir(self.session_dir):
            if filename.endswith("_fingerprint.pkl") and token_prefix[:5].lower() in filename:
                return os.path.join(self.session_dir, filename)
        
        return None
    
    def _load_or_generate_fingerprint(self) -> Dict:
        """Load existing fingerprint or generate new one"""
        os.makedirs(self.session_dir, exist_ok=True)
        
        # First try to find matching fingerprint based on token prefix
        matching_file = self._find_matching_fingerprint_file()
        if matching_file and os.path.exists(matching_file):
            try:
                with open(matching_file, 'rb') as f:
                    fingerprint = pickle.load(f)
                    print(f"📁 Loaded matching fingerprint for {self.account_id} (token: {self.auth_token[:10] if self.auth_token else 'none'})")
                    return fingerprint
            except Exception as e:
                print(f"⚠️ Failed to load matching fingerprint: {e}")
        
        # Try to load exact fingerprint file
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'rb') as f:
                    fingerprint = pickle.load(f)
                    print(f"📁 Loaded persistent fingerprint for {self.account_id}")
                    return fingerprint
            except Exception as e:
                print(f"⚠️ Failed to load fingerprint: {e}")
        
        # Generate new fingerprint
        fingerprint = self._generate_consistent_fingerprint()
        self._save_fingerprint(fingerprint)
        return fingerprint
    
    def _save_fingerprint(self, fingerprint: Dict):
        """Save fingerprint to file"""
        try:
            with open(self.session_file, 'wb') as f:
                pickle.dump(fingerprint, f)
            print(f"💾 Saved fingerprint for {self.account_id}")
        except Exception as e:
            print(f"⚠️ Failed to save fingerprint: {e}")
    
    def _generate_consistent_fingerprint(self) -> Dict:
        """Generate consistent fingerprint for account"""
        # Use account ID as seed for consistency
        seed = int(hashlib.md5(self.account_id.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Get user agent
        if FAKE_UA_AVAILABLE and hasattr(self, 'ua_generator') and self.ua_generator:
            try:
                import sys
                import io
                # Suppress stderr for user agent generation
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                user_agent = self.ua_generator.chrome
                sys.stderr = old_stderr
            except Exception as e:
                if 'old_stderr' in locals():
                    sys.stderr = old_stderr
                try:
                    old_stderr = sys.stderr
                    sys.stderr = io.StringIO()
                    user_agent = self.ua_generator.random
                    sys.stderr = old_stderr
                except Exception as e2:
                    if 'old_stderr' in locals():
                        sys.stderr = old_stderr
                    user_agent = random.choice(self.FALLBACK_USER_AGENTS)
        else:
            user_agent = random.choice(self.FALLBACK_USER_AGENTS)
        
        resolution = random.choice(self.SCREEN_RESOLUTIONS)
        language = random.choice(self.LANGUAGES)
        timezone = random.choice(self.TIMEZONES)
        platform_str = random.choice(self.PLATFORMS)
        
        # Generate consistent device IDs
        device_id = hashlib.sha256(f"{self.account_id}_device".encode()).hexdigest()[:20]
        session_id = str(int(time.time() * 1000) + random.randint(1000, 9999))
        
        # Canvas fingerprint noise
        canvas_noise = self._generate_canvas_fingerprint()
        webgl_params = self._generate_webgl_fingerprint()
        
        fingerprint = {
            "user_agent": user_agent,
            "screen_resolution": resolution,
            "language": language,
            "timezone": timezone,
            "platform": platform_str,
            "device_id": device_id,
            "session_id": session_id,
            "viewport": (resolution[0] - random.randint(0, 100), resolution[1] - random.randint(50, 150)),
            "color_depth": random.choice([24, 32]),
            "pixel_ratio": random.choice([1, 1.25, 1.5, 2]),
            "touch_support": random.choice([True, False]),
            "hardware_concurrency": random.choice([2, 4, 6, 8, 12, 16]),
            "memory": random.choice([2, 4, 8, 16, 32]),
            "webgl_vendor": random.choice(["Google Inc.", "NVIDIA Corporation", "AMD", "Intel Inc."]),
            "webgl_renderer": random.choice([
                "ANGLE (NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)",
                "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
                "ANGLE (Intel HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
                "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"
            ]),
            
            # Enhanced fingerprinting
            "canvas_fingerprint": canvas_noise,
            "webgl_fingerprint": webgl_params,
            "audio_fingerprint": hashlib.md5(f"{self.account_id}_audio".encode()).hexdigest()[:16],
            "fonts_fingerprint": self._generate_fonts_list(),
            "plugins_fingerprint": self._generate_plugins_list(),
            
            # Farcaster specific
            "fc_device_id": hashlib.sha256(f"fc_{self.account_id}".encode()).hexdigest()[:32],
            "fc_session_id": str(uuid.uuid4()),
            "fc_client_version": "1.0.0",
            "fc_platform": "web",
            "fc_build_id": "production-" + hashlib.md5(f"{self.account_id}_build".encode()).hexdigest()[:12],
            
            # Timing patterns for this account
            "timing_profile": {
                'base_delay': random.uniform(0.5, 2.0),
                'variance': random.uniform(0.2, 0.8),
                'peak_hours': random.sample(range(6, 23), k=random.randint(3, 6))
            }
        }
        
        # Reset random seed
        random.seed()
        return fingerprint
    
    def _generate_canvas_fingerprint(self) -> str:
        """Generate unique canvas fingerprint"""
        # Simulate canvas rendering differences
        base_hash = hashlib.md5(f"{self.account_id}_canvas".encode()).hexdigest()
        noise_factor = random.randint(1, 1000)
        return hashlib.sha256(f"{base_hash}_{noise_factor}".encode()).hexdigest()[:32]
    
    def _generate_webgl_fingerprint(self) -> Dict:
        """Generate WebGL parameters"""
        return {
            "webgl_version": random.choice(["WebGL 1.0", "WebGL 2.0"]),
            "shading_language_version": random.choice([
                "WebGL GLSL ES 1.0", "WebGL GLSL ES 3.00"
            ]),
            "max_texture_size": random.choice([4096, 8192, 16384]),
            "max_viewport_dims": random.choice([[4096, 4096], [8192, 8192]]),
            "aliased_line_width_range": [1, random.randint(1, 10)],
            "webgl_hash": hashlib.md5(f"{self.account_id}_webgl".encode()).hexdigest()[:16]
        }
    
    def _generate_fonts_list(self) -> List[str]:
        """Generate realistic fonts list"""
        base_fonts = [
            "Arial", "Times New Roman", "Helvetica", "Courier New", "Verdana",
            "Georgia", "Palatino", "Garamond", "Bookman", "Comic Sans MS",
            "Trebuchet MS", "Arial Black", "Impact", "Lucida Console",
            "Tahoma", "Monaco", "Lucida Grande", "Century Gothic"
        ]
        
        # Randomly select fonts based on account
        seed = int(hashlib.md5(f"{self.account_id}_fonts".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        selected_fonts = random.sample(base_fonts, k=random.randint(12, len(base_fonts)))
        random.seed()
        return sorted(selected_fonts)
    
    def _generate_plugins_list(self) -> List[str]:
        """Generate realistic plugins list"""
        common_plugins = [
            "Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client",
            "Widevine Content Decryption Module", "Microsoft Edge PDF Plugin"
        ]
        
        seed = int(hashlib.md5(f"{self.account_id}_plugins".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        selected_plugins = random.sample(common_plugins, k=random.randint(2, len(common_plugins)))
        random.seed()
        return selected_plugins
    
    def get_fresh_user_agent(self) -> str:
        """Get fresh user agent (updates periodically)"""
        if FAKE_UA_AVAILABLE and hasattr(self, 'ua_generator') and self.ua_generator:
            try:
                import sys
                import io
                # Suppress stderr for user agent generation
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                user_agent = self.ua_generator.random
                sys.stderr = old_stderr
                return user_agent
            except Exception as e:
                if 'old_stderr' in locals():
                    sys.stderr = old_stderr
                return self.fingerprint["user_agent"]
        return self.fingerprint["user_agent"]
    
    def simulate_human_timing(self, action_type: str = "default") -> float:
        """Generate human-like timing delays"""
        base_delay = self.fingerprint["timing_profile"]["base_delay"]
        variance = self.fingerprint["timing_profile"]["variance"]
        
        if action_type in self.HUMAN_PATTERNS:
            min_delay, max_delay = self.HUMAN_PATTERNS[action_type]
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = base_delay + random.uniform(-variance, variance)
        
        return max(0.1, delay)  # Minimum 0.1 seconds
    
    def get_headers(self, referer: str = None, extra_headers: Dict = None) -> Dict:
        """Generate realistic headers"""
        headers = {
            "User-Agent": self.fingerprint["user_agent"],
            "Accept": "*/*",
            "Accept-Language": self.fingerprint["language"],
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1"
        }
        
        if referer:
            headers["Referer"] = referer
        
        # Add browser-specific headers
        if "Chrome" in self.fingerprint["user_agent"]:
            headers.update({
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="125", "Google Chrome";v="125"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": f'"{self.fingerprint["platform"]}"',
                "sec-ch-ua-arch": random.choice(['"x86"', '"arm"']),
                "sec-ch-ua-bitness": '"64"',
                "sec-ch-ua-full-version-list": '"Not_A Brand";v="8.0.0.0", "Chromium";v="125.0.6422.142", "Google Chrome";v="125.0.6422.142"'
            })
        elif "Firefox" in self.fingerprint["user_agent"]:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            headers["Sec-Fetch-Mode"] = "navigate"
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    def get_farcaster_headers(self, auth_token: str, api_type: str = "farcaster") -> Dict:
        """Generate Farcaster-specific headers"""
        base_headers = self.get_headers()
        
        if api_type == "farcaster":
            base_headers.update({
                "authorization": f"Bearer {auth_token}",
                "content-type": "application/json",
                "accept": "application/json",
                "idempotency-key": str(uuid.uuid4()),
                "fc-amplitude-device-id": self.fingerprint["fc_device_id"],
                "fc-amplitude-session-id": self.fingerprint["fc_session_id"],
                "x-farcaster-client": "warpcast-web",
                "x-farcaster-client-version": self.fingerprint["fc_client_version"],
                "x-farcaster-device-id": self.fingerprint["fc_device_id"],
                "x-farcaster-session-id": self.fingerprint["fc_session_id"],
                "x-farcaster-build-id": self.fingerprint["fc_build_id"],
                "origin": "https://warpcast.com",
                "referer": "https://warpcast.com/"
            })
        elif api_type == "wreck":
            base_headers.update({
                "authorization": f"Bearer {auth_token}",
                "content-type": "application/json",
                "accept": "application/json",
                "origin": "https://versus.wreckleague.xyz",
                "referer": "https://versus.wreckleague.xyz/"
            })
        elif api_type == "neynar":
            base_headers.update({
                "api_key": auth_token,
                "content-type": "application/json",
                "accept": "application/json",
                "origin": "https://warpcast.com",
                "referer": "https://warpcast.com/"
            })
        
        return base_headers

class ProxyManager:
    """Advanced proxy management with rotation and health checks"""
    
    def __init__(self, proxy_file: str = "proxy.txt"):
        self.proxy_file = proxy_file
        self.proxies = []
        self.proxy_stats = {}
        self.proxy_lock = threading.Lock()
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            proxy = self._parse_proxy(line)
                            if proxy:
                                self.proxies.append(proxy)
                                self.proxy_stats[proxy['url']] = {
                                    'success_count': 0,
                                    'error_count': 0,
                                    'errors': 0,  # Added for improved proxy handling
                                    'last_used': None,
                                    'avg_response_time': 0,
                                    'is_working': True
                                }
            
            print(f"✅ Loaded {len(self.proxies)} proxies")
            
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            self.proxies = []
    
    def _parse_proxy(self, proxy_line: str) -> Optional[Dict]:
        """Parse proxy from various formats"""
        try:
            # Support formats:
            # ip:port
            # ip:port:username:password
            # username:password@ip:port (common format)
            # http://ip:port
            # http://username:password@ip:port
            # socks5://username:password@ip:port
            
            if '://' in proxy_line:
                # URL format
                if '@' in proxy_line:
                    # With auth
                    protocol, rest = proxy_line.split('://', 1)
                    auth_part, host_part = rest.split('@', 1)
                    username, password = auth_part.split(':', 1)
                    host, port = host_part.split(':', 1)
                else:
                    # Without auth
                    protocol, rest = proxy_line.split('://', 1)
                    host, port = rest.split(':', 1)
                    username = password = None
            elif '@' in proxy_line:
                # Format: username:password@host:port
                auth_part, host_part = proxy_line.split('@', 1)
                username, password = auth_part.split(':', 1)
                host, port = host_part.split(':', 1)
                protocol = 'http'
            else:
                # Simple format
                parts = proxy_line.split(':')
                if len(parts) == 2:
                    host, port = parts
                    username = password = None
                    protocol = 'http'
                elif len(parts) == 4:
                    host, port, username, password = parts
                    protocol = 'http'
                else:
                    return None
            
            proxy_dict = {
                'host': host.strip(),
                'port': int(port.strip()),
                'username': username.strip() if username else None,
                'password': password.strip() if password else None,
                'protocol': protocol.strip().lower()
            }
            
            # Create proxy URL
            if proxy_dict['username'] and proxy_dict['password']:
                proxy_dict['url'] = f"{proxy_dict['protocol']}://{proxy_dict['username']}:{proxy_dict['password']}@{proxy_dict['host']}:{proxy_dict['port']}"
            else:
                proxy_dict['url'] = f"{proxy_dict['protocol']}://{proxy_dict['host']}:{proxy_dict['port']}"
            
            return proxy_dict
            
        except Exception as e:
            print(f"⚠️ Invalid proxy format: {proxy_line} - {e}")
            return None
    
    def get_proxy_for_account(self, account_id: str) -> Optional[Dict]:
        """Get consistent proxy for account with smart failover"""
        if not self.proxies:
            return None
        
        with self.proxy_lock:
            # First, try to get working proxies
            working_proxies = [p for p in self.proxies if self.proxy_stats[p['url']]['is_working']]
            
            # If less than 50% proxies working, reset failed ones for retry
            if len(working_proxies) < len(self.proxies) * 0.5:
                print(f"🔄 Resetting failed proxies for retry ({len(working_proxies)}/{len(self.proxies)} working)")
                for url in self.proxy_stats:
                    if not self.proxy_stats[url]['is_working']:
                        self.proxy_stats[url]['is_working'] = True
                        self.proxy_stats[url]['errors'] = 0
                working_proxies = self.proxies
            
            if working_proxies:
                # Use account ID for consistent proxy assignment
                proxy_index = hash(account_id) % len(working_proxies)
                selected_proxy = working_proxies[proxy_index]
                
                # If this specific proxy has too many recent errors, try next one
                if self.proxy_stats[selected_proxy['url']]['errors'] >= 3:
                    # Try next proxy in rotation
                    proxy_index = (proxy_index + 1) % len(working_proxies)
                    selected_proxy = working_proxies[proxy_index]
                
                return selected_proxy
        
        return None
    
    def test_proxy(self, proxy: Dict, timeout: int = 8) -> bool:
        """Test if proxy is working with faster timeout"""
        try:
            proxy_dict = {
                'http': proxy['url'],
                'https': proxy['url']
            }
            
            start_time = time.time()
            # Use faster endpoint and shorter timeout
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout,
                verify=False,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                with self.proxy_lock:
                    stats = self.proxy_stats[proxy['url']]
                    stats['success_count'] += 1
                    stats['last_used'] = datetime.now()
                    stats['avg_response_time'] = (stats['avg_response_time'] + response_time) / 2
                    stats['is_working'] = True
                return True
                
        except Exception as e:
            with self.proxy_lock:
                stats = self.proxy_stats[proxy['url']]
                stats['error_count'] += 1
                if stats['error_count'] > 3:
                    stats['is_working'] = False
        
        return False
    
    def mark_proxy_error(self, proxy: Dict):
        """Mark proxy as having an error"""
        if proxy and proxy['url'] in self.proxy_stats:
            with self.proxy_lock:
                self.proxy_stats[proxy['url']]['error_count'] += 1
                self.proxy_stats[proxy['url']]['errors'] += 1  # Update errors counter
                if self.proxy_stats[proxy['url']]['error_count'] > 5:
                    self.proxy_stats[proxy['url']]['is_working'] = False
    
    def get_proxy_stats(self) -> Dict:
        """Get proxy statistics"""
        with self.proxy_lock:
            working = sum(1 for stats in self.proxy_stats.values() if stats['is_working'])
            total = len(self.proxy_stats)
            return {
                'total_proxies': total,
                'working_proxies': working,
                'failed_proxies': total - working,
                'stats': dict(self.proxy_stats)
            }

class SessionManager:
    """Advanced session persistence and cookie management"""
    
    def __init__(self, account_id: str, auth_token: str = None):
        self.account_id = account_id
        self.auth_token = auth_token
        self.session_dir = "sessions"
        
        # Use simple filename since account_id already contains token prefix
        self.cookies_file = os.path.join(self.session_dir, f"{account_id}_cookies.pkl")
        self.session_data_file = os.path.join(self.session_dir, f"{account_id}_session.pkl")
        
        os.makedirs(self.session_dir, exist_ok=True)
    
    def save_cookies(self, cookies_dict: dict):
        """Save cookies to file with duplicate filtering"""
        try:
            # Filter out duplicate cookies (like _cfuvid from Cloudflare)
            filtered_cookies = {}
            for name, value in cookies_dict.items():
                # Only keep the last occurrence of duplicate cookie names
                filtered_cookies[name] = value
            
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(filtered_cookies, f)
            # Suppress success message to reduce noise
        except Exception as e:
            # Suppress cookie save errors to avoid spam
            pass
    
    def _find_matching_cookies_file(self) -> Optional[str]:
        """Find cookies file that matches first 10 characters of current token"""
        if not self.auth_token or len(self.auth_token) < 10:
            return None
            
        os.makedirs(self.session_dir, exist_ok=True)
        token_prefix = self.auth_token[:10]
        
        # Look for existing cookies files with same token prefix
        target_filename = f"{token_prefix}_cookies.pkl"
        target_path = os.path.join(self.session_dir, target_filename)
        
        if os.path.exists(target_path):
            return target_path
        
        # Also check old format files for backward compatibility
        for filename in os.listdir(self.session_dir):
            if filename.endswith("_cookies.pkl") and token_prefix[:5].lower() in filename:
                return os.path.join(self.session_dir, filename)
        
        return None
    
    def load_cookies(self) -> dict:
        """Load cookies from file"""
        try:
            # First try to find matching cookies based on token prefix
            matching_file = self._find_matching_cookies_file()
            if matching_file and os.path.exists(matching_file):
                try:
                    with open(matching_file, 'rb') as f:
                        cookies = pickle.load(f)
                        print(f"🍪 Loaded matching cookies for {self.account_id} (token: {self.auth_token[:10] if self.auth_token else 'none'})")
                        return cookies
                except Exception as e:
                    print(f"⚠️ Failed to load matching cookies: {e}")
            
            # Try to load exact cookies file
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                print(f"🍪 Loaded cookies for {self.account_id}")
                return cookies
        except Exception as e:
            print(f"⚠️ Failed to load cookies: {e}")
        return {}
    
    def save_session_data(self, session_data: dict):
        """Save session state data"""
        try:
            session_data['last_save'] = time.time()
            with open(self.session_data_file, 'wb') as f:
                pickle.dump(session_data, f)
            print(f"💾 Saved session data for {self.account_id}")
        except Exception as e:
            print(f"⚠️ Failed to save session data: {e}")
    
    def load_session_data(self) -> dict:
        """Load session state data"""
        try:
            if os.path.exists(self.session_data_file):
                with open(self.session_data_file, 'rb') as f:
                    session_data = pickle.load(f)
                
                # Check if session is too old (expire after 24 hours)
                if time.time() - session_data.get('last_save', 0) < 86400:
                    print(f"💾 Loaded session data for {self.account_id}")
                    return session_data
                else:
                    print(f"⏰ Session data expired for {self.account_id}")
        except Exception as e:
            print(f"⚠️ Failed to load session data: {e}")
        return {}
    
    def clear_session(self):
        """Clear all session data"""
        try:
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
            if os.path.exists(self.session_data_file):
                os.remove(self.session_data_file)
            print(f"🗑️ Cleared session for {self.account_id}")
        except Exception as e:
            print(f"⚠️ Failed to clear session: {e}")

class BehaviorSimulator:
    """Simulate human-like browsing behavior"""
    
    def __init__(self, fingerprint: 'EnhancedBrowserFingerprint'):
        self.fingerprint = fingerprint
        self.last_action_time = time.time()
        self.action_count = 0
        self.peak_hours = fingerprint.fingerprint["timing_profile"]["peak_hours"]
    
    def should_take_break(self) -> bool:
        """Determine if should take a longer break"""
        self.action_count += 1
        
        # Take break every 50-100 actions
        if self.action_count % random.randint(50, 100) == 0:
            return True
        
        # Take break during non-peak hours
        current_hour = datetime.now().hour
        if current_hour not in self.peak_hours and random.random() < 0.3:
            return True
        
        return False
    
    def get_action_delay(self, action_type: str = "default") -> float:
        """Get delay for specific action type"""
        delay = self.fingerprint.simulate_human_timing(action_type)
        
        # Add context-based modifications
        if self.should_take_break():
            delay += random.uniform(10, 60)  # Longer break
            print(f"⏸️ Taking human-like break: {delay:.1f}s")
        
        # Slower during off-peak hours
        current_hour = datetime.now().hour
        if current_hour not in self.peak_hours:
            delay *= random.uniform(1.2, 2.0)
        
        return delay
    
    def simulate_reading_content(self, content_length: int = 100) -> float:
        """Simulate time to read content"""
        # Average reading speed: 200-300 words per minute
        words_estimate = content_length / 5  # Rough word estimate
        reading_time = (words_estimate / 250) * 60  # seconds
        
        # Add randomness
        reading_time *= random.uniform(0.7, 1.5)
        return max(2.0, reading_time)  # Minimum 2 seconds
    
    def simulate_typing_delay(self, text_length: int) -> float:
        """Simulate typing delays"""
        base_delay = self.fingerprint.HUMAN_PATTERNS["typing_speed"][0]
        max_delay = self.fingerprint.HUMAN_PATTERNS["typing_speed"][1]
        
        total_delay = 0
        for i in range(text_length):
            char_delay = random.uniform(base_delay, max_delay)
            
            # Longer pauses for spaces (thinking)
            if i % 10 == 0:  # Every 10 characters
                char_delay += random.uniform(0.1, 0.5)
            
            total_delay += char_delay
        
        return total_delay
    
    def get_realistic_browsing_requests(self, base_url: str) -> List[str]:
        """Generate additional requests to simulate real browsing"""
        domain = base_url.split('/')[2] if '://' in base_url else base_url
        
        realistic_requests = []
        
        # Common resource requests
        if 'warpcast.com' in domain:
            realistic_requests.extend([
                f"https://{domain}/favicon.ico",
                f"https://{domain}/manifest.json",
                f"https://{domain}/_next/static/css/app.css",
                f"https://{domain}/_next/static/js/app.js",
                f"https://{domain}/api/health"
            ])
        
        # Randomly select subset
        return random.sample(realistic_requests, k=random.randint(1, min(3, len(realistic_requests))))

class AdvancedRateLimiter:
    """Enhanced rate limiting with behavioral patterns"""
    
    def __init__(self):
        self.last_request_times = {}
        self.request_counts = {}
        self.behavior_simulators = {}
        self.lock = threading.Lock()
    
    def wait_if_needed(self, account_id: str, action_type: str = "default", 
                      min_delay: float = 1.0, max_delay: float = 5.0):
        """Advanced rate limiting with behavioral simulation"""
        with self.lock:
            current_time = time.time()
            
            # Initialize behavior simulator if needed
            if account_id not in self.behavior_simulators:
                # We'll need fingerprint reference, for now use basic delay
                basic_delay = random.uniform(min_delay, max_delay)
                time.sleep(basic_delay)
                self.last_request_times[account_id] = time.time()
                return
            
            behavior_sim = self.behavior_simulators[account_id]
            
            # Get context-aware delay
            delay = behavior_sim.get_action_delay(action_type)
            
            # Check last request time
            if account_id in self.last_request_times:
                time_since_last = current_time - self.last_request_times[account_id]
                
                if time_since_last < delay:
                    sleep_time = delay - time_since_last
                    print(f"⏳ Account {account_id}: Behavioral delay {sleep_time:.2f}s ({action_type})")
                    time.sleep(sleep_time)
            else:
                print(f"⏳ Account {account_id}: Initial delay {delay:.2f}s")
                time.sleep(delay)
            
            self.last_request_times[account_id] = time.time()
            
            # Track request counts
            if account_id not in self.request_counts:
                self.request_counts[account_id] = 0
            self.request_counts[account_id] += 1
    
    def register_behavior_simulator(self, account_id: str, simulator: BehaviorSimulator):
        """Register behavior simulator for account"""
        self.behavior_simulators[account_id] = simulator
    
    def add_exponential_backoff(self, account_id: str, attempt: int):
        """Enhanced exponential backoff"""
        backoff_time = min(300, (2 ** attempt) + random.uniform(0, 2))
        
        # Add extra delay during peak detection times
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            backoff_time *= random.uniform(1.5, 2.0)
        
        print(f"⏳ Account {account_id}: Enhanced backoff {backoff_time:.2f}s (attempt {attempt})")
        time.sleep(backoff_time)

class StealthSession:
    """Ultra-stealth HTTP session with TLS-Client and advanced anti-detection"""
    
    def __init__(self, account_id: str, proxy_manager: 'ProxyManager' = None, auth_token: str = None):
        self.account_id = account_id
        self.auth_token = auth_token
        self.fingerprint = EnhancedBrowserFingerprint(account_id, auth_token)
        self.session_manager = SessionManager(account_id, auth_token)
        self.behavior_simulator = BehaviorSimulator(self.fingerprint)
        self.proxy_manager = proxy_manager
        self.rate_limiter = AdvancedRateLimiter()
        self.proxy = None
        
        # Register behavior simulator with rate limiter
        self.rate_limiter.register_behavior_simulator(account_id, self.behavior_simulator)
        
        # Create session (TLS-Client or fallback)
        if TLS_CLIENT_AVAILABLE:
            self.session = self._create_tls_session()
            self.session_type = "TLS-Client"
        else:
            self.session = self._create_fallback_session()
            self.session_type = "Requests"
        
        # Configure proxy
        if self.proxy_manager:
            self.proxy = self.proxy_manager.get_proxy_for_account(account_id)
            if self.proxy:
                self._configure_proxy()
        
        # Load saved cookies
        self._load_saved_cookies()
        
        print(f"🛡️ StealthSession created for {account_id} using {self.session_type}")
    
    def _create_tls_session(self):
        """Create TLS session with realistic browser fingerprint"""
        # Determine browser type from user agent
        user_agent = self.fingerprint.fingerprint["user_agent"]
        
        if "Chrome" in user_agent:
            if "125" in user_agent or "124" in user_agent or "123" in user_agent:
                client_id = "chrome_124"
            else:
                client_id = "chrome_120"
        elif "Firefox" in user_agent:
            client_id = "firefox_120"
        elif "Safari" in user_agent and "Version" in user_agent:
            client_id = "safari_ios_16_0"
        else:
            client_id = "chrome_124"  # Default to latest Chrome
        
        session = tls_client.Session(
            client_identifier=client_id,
            random_tls_extension_order=True
        )
        
        # Set realistic headers
        session.headers.update(self.fingerprint.get_headers())
        
        # Configure timeouts
        session.timeout_seconds = 30
        
        return session
    
    def _create_fallback_session(self) -> requests.Session:
        """Enhanced fallback session using requests"""
        session = requests.Session()
        
        # Enhanced retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 524],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=50
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update(self.fingerprint.get_headers())
        
        # Disable SSL warnings
        requests.packages.urllib3.disable_warnings()
        session.verify = False
        
        return session
    
    def _configure_proxy(self):
        """Configure proxy for session"""
        if not self.proxy:
            return
        
        proxy_url = self.proxy['url']
        proxy_dict = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        if TLS_CLIENT_AVAILABLE and hasattr(self.session, 'proxies'):
            # TLS-Client proxy configuration
            self.session.proxies = proxy_dict
        elif hasattr(self.session, 'proxies'):
            # Requests proxy configuration
            self.session.proxies.update(proxy_dict)
        
        print(f"🔒 Account {self.account_id}: Using proxy {self.proxy['host']}:{self.proxy['port']}")
    
    def _load_saved_cookies(self):
        """Load saved cookies into session"""
        cookies = self.session_manager.load_cookies()
        if cookies and hasattr(self.session, 'cookies'):
            try:
                if TLS_CLIENT_AVAILABLE:
                    # TLS-Client cookie format
                    for name, value in cookies.items():
                        self.session.cookies[name] = value
                else:
                    # Requests cookie format
                    self.session.cookies.update(cookies)
                print(f"🍪 Loaded {len(cookies)} cookies for {self.account_id}")
            except Exception as e:
                print(f"⚠️ Failed to load cookies: {e}")
    
    def _save_current_cookies(self):
        """Save current session cookies with duplicate handling"""
        try:
            if hasattr(self.session, 'cookies'):
                cookies_dict = {}
                
                if TLS_CLIENT_AVAILABLE:
                    # TLS-Client cookies - handle duplicates
                    if hasattr(self.session.cookies, 'jar'):
                        # Access cookie jar if available
                        for cookie in self.session.cookies.jar:
                            cookies_dict[cookie.name] = cookie.value
                    else:
                        # Fallback to direct conversion
                        try:
                            cookies_dict = dict(self.session.cookies)
                        except Exception:
                            # Handle duplicate cookie names
                            for cookie in self.session.cookies:
                                if hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                                    cookies_dict[cookie.name] = cookie.value
                else:
                    # Requests cookies - filter duplicates
                    seen_cookies = set()
                    for cookie in self.session.cookies:
                        if cookie.name not in seen_cookies:
                            cookies_dict[cookie.name] = cookie.value
                            seen_cookies.add(cookie.name)
                
                if cookies_dict:
                    self.session_manager.save_cookies(cookies_dict)
        except Exception as e:
            # Suppress cookie save errors to avoid spam
            pass
    
    def _make_realistic_pre_requests(self, target_url: str):
        """Make realistic requests before main request"""
        try:
            realistic_urls = self.behavior_simulator.get_realistic_browsing_requests(target_url)
            
            for url in realistic_urls[:2]:  # Limit to 2 requests
                try:
                    if TLS_CLIENT_AVAILABLE:
                        self.session.execute_request("GET", url, timeout=10)
                    else:
                        self.session.get(url, timeout=10)
                    
                    # Small delay between requests
                    time.sleep(random.uniform(0.2, 0.8))
                except:
                    pass  # Ignore failures for realistic requests
        except Exception:
            pass  # Don't let pre-requests fail main request
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make ultra-stealth request with all anti-detection features"""
        
        # Determine action type for behavioral simulation
        action_type = "default"
        if "like" in url.lower():
            action_type = "click_delay"
        elif "follow" in url.lower():
            action_type = "click_delay"
        elif "post" in url.lower() or "cast" in url.lower():
            action_type = "typing_speed"
        elif method.upper() == "GET":
            action_type = "reading_time"
        
        # Apply behavioral rate limiting
        self.rate_limiter.wait_if_needed(self.account_id, action_type)
        
        # Make realistic pre-requests (occasionally)
        if random.random() < 0.1:  # 10% chance
            self._make_realistic_pre_requests(url)
        
        # Prepare headers
        headers = kwargs.get('headers', {})
        
        # For Farcaster API calls, use specialized headers
        if any(domain in url for domain in ['warpcast.com', 'api.farcaster.xyz', 'neynar.com']):
            # Will be set by make_stealth_request function
            pass
        else:
            # Use base headers for other requests
            base_headers = self.fingerprint.get_headers()
            base_headers.update(headers)
            headers = base_headers
        
        kwargs['headers'] = headers
        
        # Set timeout if not specified
        if 'timeout' not in kwargs:
            if TLS_CLIENT_AVAILABLE:
                # TLS-Client uses timeout_seconds as integer
                kwargs['timeout_seconds'] = random.randint(15, 30)
            else:
                kwargs['timeout'] = random.uniform(15, 30)
        elif 'timeout' in kwargs and TLS_CLIENT_AVAILABLE:
            # Convert timeout to timeout_seconds for TLS-Client (must be integer)
            timeout_val = kwargs.pop('timeout')
            kwargs['timeout_seconds'] = int(timeout_val) if isinstance(timeout_val, (int, float)) else 30
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add random jitter before request
                jitter = random.uniform(0.1, 0.8)
                time.sleep(jitter)
                
                # Make the request
                if TLS_CLIENT_AVAILABLE:
                    response = self.session.execute_request(method, url, **kwargs)
                else:
                    response = self.session.request(method, url, **kwargs)
                
                # Save cookies after successful request
                if response.status_code < 400:
                    self._save_current_cookies()
                
                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = random.uniform(30, 120)
                    print(f"🚫 Rate limited, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                
                # Log successful request
                print(f"✅ Account {self.account_id}: {method} {url} -> {response.status_code}")
                
                return response
                
            except Exception as e:
                print(f"❌ Account {self.account_id}: Request failed (attempt {attempt + 1}): {e}")
                
                # Mark proxy as problematic
                if self.proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_error(self.proxy)
                
                if attempt < max_retries - 1:
                    # Enhanced exponential backoff
                    self.rate_limiter.add_exponential_backoff(self.account_id, attempt)
                    
                    # Try different proxy on retry
                    if self.proxy_manager and attempt == 1:
                        new_proxy = self.proxy_manager.get_proxy_for_account(f"{self.account_id}_retry_{attempt}")
                        if new_proxy and new_proxy != self.proxy:
                            self.proxy = new_proxy
                            self._configure_proxy()
                            print(f"🔄 Account {self.account_id}: Switching to backup proxy")
                else:
                    raise e
        
        raise Exception(f"All retry attempts failed for {self.account_id}")
    
    def get_farcaster_headers(self, auth_token: str, api_type: str = "farcaster") -> Dict:
        """Get Farcaster-specific headers with enhanced stealth"""
        return self.fingerprint.get_farcaster_headers(auth_token, api_type)
    
    def close(self):
        """Clean up session"""
        try:
            if hasattr(self.session, 'close'):
                self.session.close()
            self._save_current_cookies()
            print(f"🔒 Closed session for {self.account_id}")
        except Exception as e:
            print(f"⚠️ Error closing session: {e}")

class AntiDetectionManager:
    """Enhanced anti-detection manager with comprehensive features"""
    
    def __init__(self, proxy_file: str = "proxy.txt"):
        self.proxy_manager = ProxyManager(proxy_file)
        self.sessions = {}
        self.session_lock = threading.Lock()
        self.stats = {
            'sessions_created': 0,
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxy_switches': 0
        }
        
        print(f"🛡️ Enhanced Anti-Detection Manager initialized")
        if self.proxy_manager.proxies:
            print(f"🔒 Proxy support enabled with {len(self.proxy_manager.proxies)} proxies")
        else:
            print(f"⚠️ No proxies loaded, using direct connection")
        
        if TLS_CLIENT_AVAILABLE:
            print(f"🔥 TLS-Client enabled for maximum stealth")
        else:
            print(f"⚠️ TLS-Client not available, using enhanced requests")
    
    def get_session(self, account_id: str, auth_token: str = None) -> StealthSession:
        """Get or create enhanced stealth session for account"""
        with self.session_lock:
            if account_id not in self.sessions:
                self.sessions[account_id] = StealthSession(
                    account_id, 
                    self.proxy_manager if self.proxy_manager.proxies else None,
                    auth_token
                )
                self.stats['sessions_created'] += 1
            return self.sessions[account_id]
    
    def make_request(self, account_id: str, method: str, url: str, **kwargs):
        """Make request through anti-detection session"""
        session = self.get_session(account_id)
        
        try:
            self.stats['requests_made'] += 1
            response = session.request(method, url, **kwargs)
            
            if response.status_code < 400:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
                
            return response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            raise e
    
    def test_all_proxies(self) -> Dict:
        """Test all proxies and return comprehensive statistics"""
        if not self.proxy_manager.proxies:
            return {"message": "No proxies to test"}
        
        print(f"🧪 Testing {len(self.proxy_manager.proxies)} proxies...")
        
        working_count = 0
        test_results = []
        
        for i, proxy in enumerate(self.proxy_manager.proxies):
            print(f"Testing proxy {i+1}/{len(self.proxy_manager.proxies)}: {proxy['host']}:{proxy['port']}")
            
            start_time = time.time()
            is_working = self.proxy_manager.test_proxy(proxy, timeout=15)
            test_time = time.time() - start_time
            
            result = {
                'proxy': f"{proxy['host']}:{proxy['port']}",
                'working': is_working,
                'response_time': test_time,
                'status': "✅ Working" if is_working else "❌ Failed"
            }
            
            test_results.append(result)
            print(f"   {result['proxy']} - {result['status']} ({test_time:.2f}s)")
            
            if is_working:
                working_count += 1
        
        stats = self.proxy_manager.get_proxy_stats()
        stats['test_results'] = test_results
        stats['test_summary'] = f"{working_count}/{len(self.proxy_manager.proxies)} proxies working"
        
        print(f"\n📊 Proxy Test Results:")
        print(f"   Working: {working_count}/{len(self.proxy_manager.proxies)}")
        print(f"   Success Rate: {(working_count/len(self.proxy_manager.proxies)*100):.1f}%")
        
        return stats
    
    def get_stats(self) -> Dict:
        """Get comprehensive anti-detection statistics"""
        proxy_stats = self.proxy_manager.get_proxy_stats()
        
        session_details = {}
        for account_id, session in self.sessions.items():
            session_details[account_id] = {
                'session_type': session.session_type,
                'has_proxy': session.proxy is not None,
                'proxy_host': session.proxy['host'] if session.proxy else None,
                'fingerprint_loaded': True
            }
        
        return {
            "system_stats": self.stats,
            "active_sessions": len(self.sessions),
            "session_details": session_details,
            "proxy_stats": proxy_stats,
            "tls_client_available": TLS_CLIENT_AVAILABLE,
            "fake_ua_available": FAKE_UA_AVAILABLE,
            "features_enabled": {
                "tls_fingerprinting": TLS_CLIENT_AVAILABLE,
                "dynamic_user_agents": FAKE_UA_AVAILABLE,
                "session_persistence": True,
                "behavioral_simulation": True,
                "canvas_fingerprinting": True,
                "advanced_rate_limiting": True
            }
        }
    
    def cleanup_session(self, account_id: str):
        """Clean up session for account"""
        with self.session_lock:
            if account_id in self.sessions:
                try:
                    self.sessions[account_id].close()
                    del self.sessions[account_id]
                    print(f"🧹 Cleaned up session for account {account_id}")
                except Exception as e:
                    print(f"⚠️ Error cleaning up session: {e}")
    
    def cleanup_all_sessions(self):
        """Clean up all sessions"""
        with self.session_lock:
            for account_id in list(self.sessions.keys()):
                try:
                    self.sessions[account_id].close()
                except Exception as e:
                    print(f"⚠️ Error closing session {account_id}: {e}")
            
            self.sessions.clear()
            print(f"🧹 Cleaned up all sessions")
    
    def rotate_user_agents(self):
        """Rotate user agents for all active sessions"""
        if not FAKE_UA_AVAILABLE:
            print("⚠️ fake-useragent not available for rotation")
            return
        
        rotated_count = 0
        for account_id, session in self.sessions.items():
            try:
                new_ua = session.fingerprint.get_fresh_user_agent()
                session.fingerprint.fingerprint["user_agent"] = new_ua
                
                # Update session headers
                if hasattr(session.session, 'headers'):
                    session.session.headers["User-Agent"] = new_ua
                
                rotated_count += 1
                print(f"🔄 Rotated UA for {account_id}")
                
            except Exception as e:
                print(f"⚠️ Failed to rotate UA for {account_id}: {e}")
        
        print(f"🔄 Rotated user agents for {rotated_count} sessions")

# Integration functions for existing scripts

def create_anti_detection_session(account_index: int, auth_token: str = None) -> StealthSession:
    """Create enhanced anti-detection session for account"""
    global _anti_detection_manager
    
    if '_anti_detection_manager' not in globals():
        _anti_detection_manager = AntiDetectionManager()
    
    # Use first 10 characters of token as unique identifier if token provided
    if auth_token and len(auth_token) >= 10:
        token_prefix = auth_token[:10]
        account_id = token_prefix
    else:
        # Fallback to account index if no token
        account_id = f"account_{account_index}"
    
    return _anti_detection_manager.get_session(account_id, auth_token)

def make_stealth_request(session: StealthSession, method: str, url: str, auth_token: str = None, api_type: str = "farcaster", **kwargs):
    """Make enhanced stealth request with proper headers"""
    if auth_token:
        # Use Farcaster-specific headers
        headers = session.get_farcaster_headers(auth_token, api_type)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
    
    # Add behavioral context
    if 'min_delay' in kwargs:
        kwargs.pop('min_delay')  # Remove old rate limiting params
    if 'max_delay' in kwargs:
        kwargs.pop('max_delay')
    
    return session.request(method, url, **kwargs)

def get_anti_detection_stats() -> Dict:
    """Get enhanced anti-detection statistics"""
    if '_anti_detection_manager' in globals():
        return _anti_detection_manager.get_stats()
    return {"message": "Anti-detection manager not initialized"}

def test_proxy_setup() -> Dict:
    """Test proxy setup with enhanced diagnostics"""
    manager = AntiDetectionManager()
    return manager.test_all_proxies()

def rotate_all_user_agents():
    """Rotate user agents for all active sessions"""
    if '_anti_detection_manager' in globals():
        _anti_detection_manager.rotate_user_agents()
    else:
        print("⚠️ Anti-detection manager not initialized")

def cleanup_all_sessions():
    """Clean up all active sessions"""
    if '_anti_detection_manager' in globals():
        _anti_detection_manager.cleanup_all_sessions()

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    def test_enhanced_anti_detection():
        """Test enhanced anti-detection system"""
        print("🧪 Testing Enhanced Anti-Detection System")
        print("=" * 60)
        
        # Initialize manager
        manager = AntiDetectionManager()
        
        # Test proxy setup
        print("\n1. Testing Proxy Setup:")
        proxy_stats = manager.test_all_proxies()
        
        # Test enhanced fingerprint generation
        print("\n2. Testing Enhanced Browser Fingerprints:")
        for i in range(3):
            account_id = f"test_account_{i}"
            session = manager.get_session(account_id)
            fp = session.fingerprint.fingerprint
            
            print(f"   Account {i}:")
            print(f"     User-Agent: {fp['user_agent'][:80]}...")
            print(f"     Resolution: {fp['screen_resolution']}")
            print(f"     Canvas Hash: {fp['canvas_fingerprint'][:16]}...")
            print(f"     WebGL Hash: {fp['webgl_fingerprint']['webgl_hash']}")
            print(f"     Session Type: {session.session_type}")
        
        # Test behavioral timing
        print("\n3. Testing Behavioral Patterns:")
        test_session = manager.get_session("test_behavior")
        behavior = test_session.behavior_simulator
        
        for action in ['click_delay', 'reading_time', 'typing_speed']:
            delay = behavior.get_action_delay(action)
            print(f"   {action}: {delay:.2f}s")
        
        # Test stealth request
        print("\n4. Testing Enhanced Stealth Requests:")
        test_session = manager.get_session("test_request")
        try:
            response = test_session.request("GET", "https://httpbin.org/user-agent")
            if response.status_code == 200:
                print("   ✅ Test request successful")
                try:
                    data = response.json()
                    print(f"   User-Agent sent: {data.get('user-agent', 'N/A')[:60]}...")
                except:
                    print("   Response received but not JSON")
            else:
                print(f"   ❌ Test request failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Test request error: {e}")
        
        # Test session persistence
        print("\n5. Testing Session Persistence:")
        persistent_session = manager.get_session("test_persistence")
        session_data = {'test_key': 'test_value', 'timestamp': time.time()}
        persistent_session.session_manager.save_session_data(session_data)
        
        loaded_data = persistent_session.session_manager.load_session_data()
        if loaded_data.get('test_key') == 'test_value':
            print("   ✅ Session persistence working")
        else:
            print("   ❌ Session persistence failed")
        
        # Show final enhanced stats
        print("\n6. Final Enhanced Statistics:")
        stats = manager.get_stats()
        print(f"   Active sessions: {stats['active_sessions']}")
        print(f"   Proxies loaded: {stats['proxy_stats']['total_proxies']}")
        print(f"   Working proxies: {stats['proxy_stats']['working_proxies']}")
        print(f"   TLS-Client enabled: {stats['tls_client_available']}")
        print(f"   Fake-UserAgent enabled: {stats['fake_ua_available']}")
        
        print("\n   Features enabled:")
        for feature, enabled in stats['features_enabled'].items():
            status = "✅" if enabled else "❌"
            print(f"     {status} {feature}")
        
        print("\n✅ Enhanced Anti-Detection System Test Completed!")
        
        # Cleanup
        manager.cleanup_all_sessions()
    
    def show_help():
        """Show help information"""
        print("🛡️ Enhanced Anti-Detection Module")
        print("=" * 50)
        print("Available commands:")
        print("  python anti_detection.py test     - Run comprehensive tests")
        print("  python anti_detection.py proxy    - Test proxy setup only")
        print("  python anti_detection.py stats    - Show current statistics")
        print("  python anti_detection.py help     - Show this help")
        print("")
        print("Required dependencies:")
        print("  pip install tls-client fake-useragent")
        print("")
        print("Features:")
        print("  🔥 TLS-Client for perfect browser fingerprinting")
        print("  🔄 Dynamic user-agent rotation with fake-useragent")
        print("  💾 Session persistence with cookie management")
        print("  🎭 Behavioral simulation with human-like timing")
        print("  🎨 Canvas and WebGL fingerprint noise")
        print("  🔒 Advanced proxy rotation with health checks")
        print("  ⏱️ Intelligent rate limiting with context awareness")
    
    # Command line interface
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            test_enhanced_anti_detection()
        elif command == "proxy":
            stats = test_proxy_setup()
            print(f"\nProxy test completed: {stats.get('test_summary', 'No summary available')}")
        elif command == "stats":
            stats = get_anti_detection_stats()
            print("\n� Current Statistics:")
            print(json.dumps(stats, indent=2))
        elif command == "help":
            show_help()
        else:
            print(f"❌ Unknown command: {command}")
            show_help()
    else:
        print("�🛡️ Enhanced Anti-Detection Module Loaded")
        print("Usage: python anti_detection.py [test|proxy|stats|help]")
        print("")
        print("🔥 Enhanced Features Available:")
        if TLS_CLIENT_AVAILABLE:
            print("  ✅ TLS-Client - Maximum stealth fingerprinting")
        else:
            print("  ❌ TLS-Client - Install with: pip install tls-client")
        
        if FAKE_UA_AVAILABLE:
            print("  ✅ Fake-UserAgent - Dynamic user agent rotation")
        else:
            print("  ❌ Fake-UserAgent - Install with: pip install fake-useragent")
        
        print("  ✅ Session Persistence - Cookie and state management")
        print("  ✅ Behavioral Simulation - Human-like timing patterns")
        print("  ✅ Canvas Fingerprinting - Unique device signatures")
        print("  ✅ Advanced Rate Limiting - Context-aware delays")

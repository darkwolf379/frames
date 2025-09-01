#!/usr/bin/env python3
"""
Advanced Anti-Detection System for Farcaster Automation
Provides browser fingerprinting, proxy rotation, and stealth capabilities
"""

import random
import time
import json
import base64
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import queue
import os

class BrowserFingerprint:
    """Generate realistic browser fingerprints"""
    
    # Real browser user agents with versions
    USER_AGENTS = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        
        # Chrome macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        
        # Safari macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        
        # Edge Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    ]
    
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
        (1280, 720), (1600, 900), (2560, 1440), (1920, 1200),
        (1680, 1050), (1280, 1024), (1024, 768), (2048, 1152)
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
        "Australia/Sydney", "America/Toronto", "America/Denver"
    ]
    
    PLATFORMS = [
        "Win32", "MacIntel", "Linux x86_64", "Linux armv7l"
    ]
    
    def __init__(self, account_id: str = None):
        self.account_id = account_id or str(uuid.uuid4())
        self.fingerprint = self._generate_consistent_fingerprint()
    
    def _generate_consistent_fingerprint(self) -> Dict:
        """Generate consistent fingerprint for account"""
        # Use account ID as seed for consistency
        seed = int(hashlib.md5(self.account_id.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        user_agent = random.choice(self.USER_AGENTS)
        resolution = random.choice(self.SCREEN_RESOLUTIONS)
        language = random.choice(self.LANGUAGES)
        timezone = random.choice(self.TIMEZONES)
        platform = random.choice(self.PLATFORMS)
        
        # Generate consistent device IDs
        device_id = hashlib.sha256(f"{self.account_id}_device".encode()).hexdigest()[:20]
        session_id = str(int(time.time() * 1000) + random.randint(1000, 9999))
        
        fingerprint = {
            "user_agent": user_agent,
            "screen_resolution": resolution,
            "language": language,
            "timezone": timezone,
            "platform": platform,
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
                "ANGLE (Intel HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"
            ])
        }
        
        # Reset random seed
        random.seed()
        return fingerprint
    
    def get_headers(self, referer: str = None, extra_headers: Dict = None) -> Dict:
        """Generate realistic headers"""
        headers = {
            "User-Agent": self.fingerprint["user_agent"],
            "Accept": "*/*",
            "Accept-Language": self.fingerprint["language"],
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        if referer:
            headers["Referer"] = referer
        
        # Add browser-specific headers
        if "Chrome" in self.fingerprint["user_agent"]:
            headers.update({
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": f'"{self.fingerprint["platform"]}"'
            })
        elif "Firefox" in self.fingerprint["user_agent"]:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        
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
                "idempotency-key": str(uuid.uuid4()),
                "fc-amplitude-device-id": self.fingerprint["device_id"],
                "fc-amplitude-session-id": self.fingerprint["session_id"],
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
        """Get consistent proxy for account"""
        if not self.proxies:
            return None
        
        with self.proxy_lock:
            # Use account ID to get consistent proxy
            proxy_index = hash(account_id) % len(self.proxies)
            working_proxies = [p for p in self.proxies if self.proxy_stats[p['url']]['is_working']]
            
            if not working_proxies:
                # All proxies failed, reset and try again
                for url in self.proxy_stats:
                    self.proxy_stats[url]['is_working'] = True
                working_proxies = self.proxies
            
            if working_proxies:
                proxy_index = hash(account_id) % len(working_proxies)
                return working_proxies[proxy_index]
        
        return None
    
    def test_proxy(self, proxy: Dict, timeout: int = 10) -> bool:
        """Test if proxy is working"""
        try:
            proxy_dict = {
                'http': proxy['url'],
                'https': proxy['url']
            }
            
            start_time = time.time()
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout,
                verify=False
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

class RateLimiter:
    """Advanced rate limiting with jitter and backoff"""
    
    def __init__(self):
        self.last_request_times = {}
        self.request_counts = {}
        self.lock = threading.Lock()
    
    def wait_if_needed(self, account_id: str, min_delay: float = 1.0, max_delay: float = 5.0):
        """Wait if needed to avoid rate limiting"""
        with self.lock:
            current_time = time.time()
            
            # Check last request time
            if account_id in self.last_request_times:
                time_since_last = current_time - self.last_request_times[account_id]
                min_interval = random.uniform(min_delay, max_delay)
                
                if time_since_last < min_interval:
                    sleep_time = min_interval - time_since_last
                    # Add jitter
                    sleep_time += random.uniform(0, 0.5)
                    
                    print(f"⏳ Account {account_id}: Rate limiting, waiting {sleep_time:.2f}s")
                    time.sleep(sleep_time)
            
            self.last_request_times[account_id] = time.time()
    
    def add_exponential_backoff(self, account_id: str, attempt: int):
        """Add exponential backoff for failed requests"""
        backoff_time = min(300, (2 ** attempt) + random.uniform(0, 1))
        print(f"⏳ Account {account_id}: Exponential backoff, waiting {backoff_time:.2f}s (attempt {attempt})")
        time.sleep(backoff_time)

class StealthSession:
    """Stealth HTTP session with anti-detection features"""
    
    def __init__(self, account_id: str, proxy_manager: ProxyManager = None):
        self.account_id = account_id
        self.fingerprint = BrowserFingerprint(account_id)
        self.proxy_manager = proxy_manager
        self.rate_limiter = RateLimiter()
        self.session = self._create_session()
        self.proxy = None
        
        if self.proxy_manager:
            self.proxy = self.proxy_manager.get_proxy_for_account(account_id)
            if self.proxy:
                self._configure_proxy()
    
    def _create_session(self) -> requests.Session:
        """Create session with stealth features"""
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Disable SSL warnings
        requests.packages.urllib3.disable_warnings()
        session.verify = False
        
        return session
    
    def _configure_proxy(self):
        """Configure proxy for session"""
        if self.proxy:
            proxy_dict = {
                'http': self.proxy['url'],
                'https': self.proxy['url']
            }
            self.session.proxies.update(proxy_dict)
            print(f"🔒 Account {self.account_id}: Using proxy {self.proxy['host']}:{self.proxy['port']}")
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make stealth request with anti-detection"""
        # Apply rate limiting
        min_delay = kwargs.pop('min_delay', 1.0)
        max_delay = kwargs.pop('max_delay', 3.0)
        self.rate_limiter.wait_if_needed(self.account_id, min_delay, max_delay)
        
        # Add realistic headers
        headers = kwargs.get('headers', {})
        stealth_headers = self.fingerprint.get_headers()
        stealth_headers.update(headers)
        kwargs['headers'] = stealth_headers
        
        # Add timeout if not specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = random.uniform(10, 20)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add random jitter before request
                jitter = random.uniform(0.1, 0.5)
                time.sleep(jitter)
                
                response = self.session.request(method, url, **kwargs)
                
                # Log successful request
                print(f"✅ Account {self.account_id}: {method} {url} -> {response.status_code}")
                
                return response
                
            except Exception as e:
                print(f"❌ Account {self.account_id}: Request failed (attempt {attempt + 1}): {e}")
                
                # Mark proxy as problematic
                if self.proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_error(self.proxy)
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    self.rate_limiter.add_exponential_backoff(self.account_id, attempt)
                    
                    # Try different proxy on retry
                    if self.proxy_manager and attempt == 1:
                        new_proxy = self.proxy_manager.get_proxy_for_account(f"{self.account_id}_retry")
                        if new_proxy and new_proxy != self.proxy:
                            self.proxy = new_proxy
                            self._configure_proxy()
                            print(f"🔄 Account {self.account_id}: Switching to backup proxy")
                else:
                    raise e
        
        raise Exception(f"All retry attempts failed for {self.account_id}")
    
    def get_farcaster_headers(self, auth_token: str, api_type: str = "farcaster") -> Dict:
        """Get Farcaster-specific headers"""
        return self.fingerprint.get_farcaster_headers(auth_token, api_type)

class AntiDetectionManager:
    """Main anti-detection manager"""
    
    def __init__(self, proxy_file: str = "proxy.txt"):
        self.proxy_manager = ProxyManager(proxy_file)
        self.sessions = {}
        self.session_lock = threading.Lock()
        
        print(f"🛡️ Anti-Detection Manager initialized")
        if self.proxy_manager.proxies:
            print(f"🔒 Proxy support enabled with {len(self.proxy_manager.proxies)} proxies")
        else:
            print(f"⚠️ No proxies loaded, using direct connection")
    
    def get_session(self, account_id: str) -> StealthSession:
        """Get or create stealth session for account"""
        with self.session_lock:
            if account_id not in self.sessions:
                self.sessions[account_id] = StealthSession(
                    account_id, 
                    self.proxy_manager if self.proxy_manager.proxies else None
                )
            return self.sessions[account_id]
    
    def test_all_proxies(self) -> Dict:
        """Test all proxies and return statistics"""
        if not self.proxy_manager.proxies:
            return {"message": "No proxies to test"}
        
        print(f"🧪 Testing {len(self.proxy_manager.proxies)} proxies...")
        
        working_count = 0
        for proxy in self.proxy_manager.proxies:
            is_working = self.proxy_manager.test_proxy(proxy)
            status = "✅ Working" if is_working else "❌ Failed"
            print(f"   {proxy['host']}:{proxy['port']} - {status}")
            if is_working:
                working_count += 1
        
        stats = self.proxy_manager.get_proxy_stats()
        print(f"\n📊 Proxy Test Results:")
        print(f"   Working: {working_count}/{len(self.proxy_manager.proxies)}")
        
        return stats
    
    def get_stats(self) -> Dict:
        """Get comprehensive anti-detection statistics"""
        proxy_stats = self.proxy_manager.get_proxy_stats()
        
        return {
            "active_sessions": len(self.sessions),
            "proxy_stats": proxy_stats,
            "fingerprints_generated": len(self.sessions)
        }
    
    def cleanup_session(self, account_id: str):
        """Clean up session for account"""
        with self.session_lock:
            if account_id in self.sessions:
                self.sessions[account_id].session.close()
                del self.sessions[account_id]
                print(f"🧹 Cleaned up session for account {account_id}")

# Integration functions for existing scripts

def create_anti_detection_session(account_index: int, auth_token: str = None) -> StealthSession:
    """Create anti-detection session for account"""
    global _anti_detection_manager
    
    if '_anti_detection_manager' not in globals():
        _anti_detection_manager = AntiDetectionManager()
    
    account_id = f"account_{account_index}"
    return _anti_detection_manager.get_session(account_id)

def make_stealth_request(session: StealthSession, method: str, url: str, auth_token: str = None, api_type: str = "farcaster", **kwargs):
    """Make stealth request with proper headers"""
    if auth_token:
        # Use Farcaster-specific headers
        headers = session.get_farcaster_headers(auth_token, api_type)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
    
    return session.request(method, url, **kwargs)

def get_anti_detection_stats() -> Dict:
    """Get anti-detection statistics"""
    if '_anti_detection_manager' in globals():
        return _anti_detection_manager.get_stats()
    return {"message": "Anti-detection manager not initialized"}

def test_proxy_setup() -> Dict:
    """Test proxy setup"""
    manager = AntiDetectionManager()
    return manager.test_all_proxies()

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    def test_anti_detection():
        """Test anti-detection system"""
        print("🧪 Testing Anti-Detection System")
        print("=" * 50)
        
        # Initialize manager
        manager = AntiDetectionManager()
        
        # Test proxy setup
        print("\n1. Testing Proxy Setup:")
        proxy_stats = manager.test_all_proxies()
        
        # Test fingerprint generation
        print("\n2. Testing Browser Fingerprints:")
        for i in range(3):
            account_id = f"test_account_{i}"
            session = manager.get_session(account_id)
            print(f"   Account {i}: User-Agent: {session.fingerprint.fingerprint['user_agent'][:60]}...")
            print(f"   Account {i}: Resolution: {session.fingerprint.fingerprint['screen_resolution']}")
            print(f"   Account {i}: Device ID: {session.fingerprint.fingerprint['device_id']}")
        
        # Test request making
        print("\n3. Testing Stealth Requests:")
        test_session = manager.get_session("test_request")
        try:
            response = test_session.request("GET", "https://httpbin.org/user-agent")
            if response.status_code == 200:
                print("   ✅ Test request successful")
                data = response.json()
                print(f"   User-Agent sent: {data.get('user-agent', 'N/A')[:60]}...")
            else:
                print(f"   ❌ Test request failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Test request error: {e}")
        
        # Show final stats
        print("\n4. Final Statistics:")
        stats = manager.get_stats()
        print(f"   Active sessions: {stats['active_sessions']}")
        print(f"   Proxies loaded: {stats['proxy_stats']['total_proxies']}")
        print(f"   Working proxies: {stats['proxy_stats']['working_proxies']}")
        
        print("\n✅ Anti-Detection System Test Completed!")
    
    # Run test if called directly
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_anti_detection()
    else:
        print("🛡️ Anti-Detection Module Loaded")
        print("Usage: python anti_detection.py test")

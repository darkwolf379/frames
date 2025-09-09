@echo off
setlocal EnableDelayedExpansion

echo.
echo ================================================================================
echo                    🚀 FARCASTER MULTI-TAB CMD LAUNCHER 🚀
echo                         Simple Batch File Approach
echo ================================================================================
echo.

REM Check if required files exist
if not exist "config.toml" (
    echo ❌ config.toml not found!
    pause
    exit /b 1
)

if not exist "account.txt" (
    echo ❌ account.txt not found!
    pause
    exit /b 1
)

if not exist "farcaster_auto_share_like.py" (
    echo ❌ farcaster_auto_share_like.py not found!
    pause
    exit /b 1
)

echo ✅ All required files found
echo.

REM Clean up link_hash.json from previous sessions
if exist "link_hash.json" (
    echo 🧹 Cleaning up previous session data.
    del "link_hash.json" >nul 2>&1
)

REM Create temp directory
if not exist "temp_accounts" mkdir temp_accounts

REM First pass: Count total valid accounts
set TOTAL_ACCOUNTS=0
for /f "usebackq tokens=*" %%a in ("account.txt") do (
    set TOKEN=%%a
    REM Skip empty lines and comments
    if not "!TOKEN!"=="" if not "!TOKEN:~0,1!"=="#" (
        set /a TOTAL_ACCOUNTS+=1
    )
)

echo 📊 Total valid accounts detected: !TOTAL_ACCOUNTS!
echo.

REM Second pass: Read tokens from account.txt and launch tabs
set ACCOUNT_NUM=1

for /f "usebackq tokens=*" %%a in ("account.txt") do (
    set TOKEN=%%a
    REM Skip empty lines and comments
    if not "!TOKEN!"=="" if not "!TOKEN:~0,1!"=="#" (
        echo 🔧 Setting up Account !ACCOUNT_NUM!.
        
        REM Create individual account file
        echo !TOKEN! > "temp_accounts\account_!ACCOUNT_NUM!.txt"
        
        REM Create launcher script for this account with total accounts info
        call :CREATE_LAUNCHER !ACCOUNT_NUM! !TOTAL_ACCOUNTS!
        
        REM Launch CMD tab
        echo ✅ Launching CMD tab for Account !ACCOUNT_NUM!.
        start "Farcaster Account !ACCOUNT_NUM!" cmd /k "cd /d "%CD%" & title Farcaster Account !ACCOUNT_NUM! & mode con cols=120 lines=30 & color 0A & python temp_accounts\launcher_account_!ACCOUNT_NUM!.py"
        
        REM Wait between launches
        timeout /t 3 /nobreak >nul
        
        set /a ACCOUNT_NUM+=1
    )
)

echo.
echo ✅ Successfully launched CMD tabs!
echo.
echo 📋 INSTRUCTIONS:
echo   • Each CMD tab runs independently
echo   • All tabs share the same link_hash.json for coordination
echo   • Press Ctrl+C in any tab to stop that specific account
echo   • Close this window or press any key to exit launcher
echo.
pause
goto :EOF

:CREATE_LAUNCHER
set ACC_NUM=%1
set TOTAL_ACCOUNTS=%2

REM Create Python launcher script for this account
(
echo #!/usr/bin/env python3
echo """
echo Auto-generated launcher for Account %ACC_NUM% of %TOTAL_ACCOUNTS%
echo """
echo.
echo import os
echo import sys
echo import time
echo import json
echo import toml
echo from pathlib import Path
echo.
echo # Change to the correct directory
echo os.chdir^(r"%CD%"^)
echo.
echo # Add parent directory to Python path
echo sys.path.insert^(0, r"%CD%"^)
echo.
echo # Import the main script
echo try:
echo     from farcaster_auto_share_like import *
echo     print^("✅ Successfully imported farcaster_auto_share_like"^)
echo except ImportError as e:
echo     print^(f"❌ Import error: {e}"^)
echo     input^("Press Enter to exit."^)
echo     sys.exit^(1^)
echo.
echo def load_single_token^(^):
echo     """Load token for this account"""
echo     try:
echo         with open^(r"temp_accounts\account_%ACC_NUM%.txt", 'r', encoding='utf-8'^) as f:
echo             token = f.read^(^).strip^(^)
echo         return token
echo     except Exception as e:
echo         print^(f"❌ Error loading token: {e}"^)
echo         return None
echo.
echo def main^(^):
echo     """Main launcher function"""
echo     print^(f"🚀 ACCOUNT %ACC_NUM% - FARCASTER AUTO SHARE + LIKE"^)
echo     print^(f"{'='*60}"^)
echo.
echo     # Load config from config.toml
echo     try:
echo         with open^('config.toml', 'r', encoding='utf-8'^) as f:
echo             config = toml.load^(f^)
echo         shares_per_cycle = config['sharing']['num_shares']
echo         share_delay_min = config['sharing']['share_delay_min']
echo         share_delay_max = config['sharing']['share_delay_max']
echo         like_delay_min = config['liking']['like_delay_min']
echo         like_delay_max = config['liking']['like_delay_max']
echo         cycle_delay = config['cycle']['cycle_delay_minutes'] * 60
echo         print^(f"✅ Loaded config from config.toml"^)
echo     except Exception as e:
echo         print^(f"❌ Error loading config.toml: {e}"^)
echo         shares_per_cycle = 1
echo         share_delay_min = 10
echo         share_delay_max = 30
echo         like_delay_min = 2
echo         like_delay_max = 5
echo         cycle_delay = 900
echo.    
echo     # Load token
echo     token = load_single_token^(^)
echo     if not token:
echo         print^("❌ Failed to load token!"^)
echo         input^("Press Enter to exit."^)
echo         return
echo.
echo     # Create account info
echo     account_info = [{'index': %ACC_NUM%, 'token': token}]
echo.
echo     try:
echo         # Initialize bot to get user info
echo         print^(f"🔍 Initializing Account %ACC_NUM%."^)
echo         bot = FarcasterAutoShareLike^(token, %ACC_NUM%, True^)
echo.        
echo         if not bot.user_id:
echo             print^(f"❌ Account %ACC_NUM%: Failed to detect user info!"^)
echo             input^("Press Enter to exit."^)
echo             return
echo.        
echo         print^(f"✅ Account %ACC_NUM%: @{bot.username} ^(ID: {bot.user_id}^)"^)
echo.        
echo         # Check fuel
echo         print^(f"⛽ Checking fuel status."^)
echo         fuel = bot.check_fuel_status^(^)
echo         print^(f"💰 Current fuel: {fuel}"^)
echo.        
echo         # Show configuration from config.toml
echo         print^(f"\n📋 CONFIGURATION FROM CONFIG.TOML:"^)
echo         print^(f"   Mode: infinite"^)
echo         print^(f"   Save links: True"^)
echo         print^(f"   Original text only: False"^)
echo         print^(f"   Shares per cycle: {shares_per_cycle}"^)
echo         print^(f"   Share delay: {share_delay_min}-{share_delay_max}s"^)
echo         print^(f"   Like delay: {like_delay_min}-{like_delay_max}s"^)
echo         print^(f"   Cycle delay: {cycle_delay//60} minutes"^)
echo.
echo         # Import the clean independent automation function with auto-detection
echo         from independent_clean import independent_cycle_automation_clean
echo.
echo         # Start infinite cycle automation with auto-detection link_hash.json
echo         print^(f"\n🔄 Starting automation with auto-detection link_hash.json."^)
echo         print^(f"⛔ Press Ctrl+C to stop anytime"^)
echo         independent_cycle_automation_clean^(
echo             account_info,
echo             shares_per_cycle,
echo             ^(share_delay_min, share_delay_max^),
echo             ^(like_delay_min, like_delay_max^),
echo             999,
echo             cycle_delay,
echo             False,
echo             True,
echo             %TOTAL_ACCOUNTS%
echo         ^)
echo.        
echo     except KeyboardInterrupt:
echo         print^(f"\n⛔ Account %ACC_NUM%: Stopped by user"^)
echo         # Cleanup link_hash.json on manual stop
echo         try:
echo             import os
echo             if os.path.exists^("link_hash.json"^):
echo                 os.remove^("link_hash.json"^)
echo                 print^(f"🧹 Cleaned up link_hash.json"^)
echo         except:
echo             pass
echo     except Exception as e:
echo         print^(f"\n❌ Account %ACC_NUM%: Error - {e}"^)
echo     finally:
echo         print^(f"\n🏁 Account %ACC_NUM%: Session ended"^)
echo         input^("Press Enter to close this window."^)
echo.
echo if __name__ == "__main__":
echo     main^(^)
) > "temp_accounts\launcher_account_%ACC_NUM%.py" 2>nul

goto :EOF

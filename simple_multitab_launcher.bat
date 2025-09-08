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

REM Create temp directory
if not exist "temp_accounts" mkdir temp_accounts

REM Read tokens from account.txt and launch tabs
set ACCOUNT_NUM=1

for /f "usebackq tokens=*" %%a in ("account.txt") do (
    set TOKEN=%%a
    REM Skip empty lines and comments
    if not "!TOKEN!"=="" if not "!TOKEN:~0,1!"=="#" (
        echo 🔧 Setting up Account !ACCOUNT_NUM!...
        
        REM Create individual account file
        echo !TOKEN! > "temp_accounts\account_!ACCOUNT_NUM!.txt"
        
        REM Create launcher script for this account
        call :CREATE_LAUNCHER !ACCOUNT_NUM!
        
        REM Launch CMD tab
        echo ✅ Launching CMD tab for Account !ACCOUNT_NUM!...
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

REM Create Python launcher script for this account
(
echo #!/usr/bin/env python3
echo """
echo Auto-generated launcher for Account %ACC_NUM%
echo """
echo.
echo import os
echo import sys
echo import time
echo import json
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
echo     input^("Press Enter to exit..."^)
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
echo     # Load token
echo     token = load_single_token^(^)
echo     if not token:
echo         print^("❌ Failed to load token!"^)
echo         input^("Press Enter to exit..."^)
echo         return
echo.
echo     # Create account info
echo     account_info = [{'index': %ACC_NUM%, 'token': token}]
echo.
echo     try:
echo         # Initialize bot to get user info
echo         print^(f"🔍 Initializing Account %ACC_NUM%..."^)
echo         bot = FarcasterAutoShareLike^(token, %ACC_NUM%, True^)
echo.        
echo         if not bot.user_id:
echo             print^(f"❌ Account %ACC_NUM%: Failed to detect user info!"^)
echo             input^("Press Enter to exit..."^)
echo             return
echo.        
echo         print^(f"✅ Account %ACC_NUM%: @{bot.username} ^(ID: {bot.user_id}^)"^)
echo.        
echo         # Check fuel
echo         print^(f"⛽ Checking fuel status..."^)
echo         fuel = bot.check_fuel_status^(^)
echo         print^(f"💰 Current fuel: {fuel}"^)
echo.        
echo         # Show configuration
echo         print^(f"\n📋 CONFIGURATION:"^)
echo         print^(f"   Mode: infinite"^)
echo         print^(f"   Save links: True"^)
echo         print^(f"   Original text only: False"^)
echo         print^(f"   Shares per cycle: 3"^)
echo         print^(f"   Share delay: 10-30s"^)
echo         print^(f"   Like delay: 2-5s"^)
echo         print^(f"   Cycle delay: 15 minutes"^)
echo.        
echo         # Start infinite cycle automation
echo         print^(f"\n🔄 Starting infinite cycle automation..."^)
echo         print^(f"⛔ Press Ctrl+C to stop anytime"^)
echo         cycle_based_share_like_automation^(
echo             account_info,
echo             3,
echo             ^(10, 30^),
echo             ^(2, 5^),
echo             999,
echo             900,
echo             False,
echo             True,
echo             3
echo         ^)
echo.        
echo     except KeyboardInterrupt:
echo         print^(f"\n⛔ Account %ACC_NUM%: Stopped by user"^)
echo     except Exception as e:
echo         print^(f"\n❌ Account %ACC_NUM%: Error - {e}"^)
echo     finally:
echo         print^(f"\n🏁 Account %ACC_NUM%: Session ended"^)
echo         input^("Press Enter to close this window..."^)
echo.
echo if __name__ == "__main__":
echo     main^(^)
) > "temp_accounts\launcher_account_%ACC_NUM%.py" 2>nul

goto :EOF

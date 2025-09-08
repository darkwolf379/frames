#!/usr/bin/env python3
"""
Independent Cycle Automation - Clean implementation
"""

def independent_cycle_automation_clean(account_info_list, num_shares=5, share_delay_range=(10, 30), like_delay_range=(2, 5), cycles=5, cycle_delay=300, use_original_only=False, save_links=False, expected_accounts=None):
    """Run FULLY INDEPENDENT cycle automation - each tab works independently, only checks link_hash.json"""
    try:
        # Import required modules (local imports to avoid conflicts)
        import time
        from farcaster_auto_share_like import (
            FarcasterAutoShareLike, colored_text, Colors, 
            wait_for_cycle_completion, get_cycle_shares_for_likes, 
            print_colored_box
        )
        
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
        
        print(f"\n{colored_text(f'🔄 INDEPENDENT CYCLE AUTOMATION - ACCOUNT {account_index}', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored_text(f'📝 Mode: FULLY INDEPENDENT (no inter-tab communication)', Colors.CYAN)}")
        print(f"{colored_text(f'👥 Expected total accounts: {expected_accounts}', Colors.CYAN)}")
        print(f"{colored_text(f'🔂 Running infinite cycles with {cycle_delay//60} minute intervals', Colors.CYAN)}")
        print(f"{colored_text(f'📁 Coordination: File-based only via link_hash.json', Colors.CYAN)}")
        
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
            while True:
                print(f"\n{colored_text(f'🔄 CYCLE {cycle} - ACCOUNT {account_index}', Colors.BOLD + Colors.MAGENTA)}")
                print(f"{colored_text('═' * 60, Colors.MAGENTA)}")
                
                # PHASE 1: POST SHARES (Independent)
                print(f"\n{colored_text(f'📝 PHASE 1: POSTING SHARES (Account {account_index})', Colors.BOLD + Colors.GREEN)}")
                shares_data = bot.run_share_cycle(num_shares, share_delay_range, use_original_only, cycle)
                
                successful_shares = len([s for s in shares_data if s.get('success', False)])
                print(f"{colored_text(f'✅ Account {account_index}: Posted {successful_shares}/{num_shares} shares', Colors.GREEN)}")
                
                if successful_shares == 0:
                    print(f"{colored_text(f'❌ Account {account_index}: No shares posted, skipping like phase', Colors.RED)}")
                else:
                    # PHASE 2: WAIT FOR ALL ACCOUNTS TO COMPLETE (File-based check only)
                    print(f"\n{colored_text(f'⏳ PHASE 2: WAITING FOR ALL ACCOUNTS (Check link_hash.json only)', Colors.BOLD + Colors.YELLOW)}")
                    
                    # Independent wait - only check file, no communication
                    wait_result = wait_for_cycle_completion(cycle, expected_accounts, num_shares, max_wait_minutes=10)
                    
                    if wait_result == True:
                        # All accounts completed - start liking
                        print(f"\n{colored_text(f'👍 PHASE 3: CROSS-LIKING (Account {account_index})', Colors.BOLD + Colors.BLUE)}")
                        
                        # Get shares from link_hash.json for this cycle
                        cycle_shares = get_cycle_shares_for_likes(cycle)
                        
                        if cycle_shares:
                            likes_given = bot.like_shares_from_others(cycle_shares, like_delay_range)
                            print(f"{colored_text(f'✅ Account {account_index}: Liked {likes_given} shares from others', Colors.GREEN)}")
                        else:
                            print(f"{colored_text(f'⚠️ Account {account_index}: No shares found to like', Colors.YELLOW)}")
                            likes_given = 0
                        
                        # Cycle complete
                        print(f"\n{colored_text(f'🎉 CYCLE {cycle} COMPLETED! (Account {account_index})', Colors.BOLD + Colors.GREEN)}")
                        print_colored_box(f"CYCLE {cycle} RESULTS", [
                            f"📝 Shares posted: {successful_shares}",
                            f"👍 Likes given: {likes_given}",
                            f"🎯 Account: {account_index} (@{bot.username})"
                        ], Colors.GREEN)
                        
                    elif wait_result == 'traditional':
                        print(f"{colored_text(f'🔄 Account {account_index}: Switching to traditional mode', Colors.CYAN)}")
                        break
                    else:
                        print(f"{colored_text(f'⚠️ Account {account_index}: Skipping like phase due to timeout', Colors.YELLOW)}")
                
                # Wait before next cycle
                if cycle < cycles:
                    print(f"\n{colored_text(f'⏰ Waiting {cycle_delay//60} minutes before CYCLE {cycle+1}...', Colors.CYAN)}")
                    print(f"{colored_text(f'⛔ Press Ctrl+C to stop Account {account_index}', Colors.YELLOW)}")
                    time.sleep(cycle_delay)
                
                cycle += 1
                
        except KeyboardInterrupt:
            print(f"\n{colored_text(f'⛔ Account {account_index}: Stopped by user', Colors.RED)}")
        
        # Final Summary
        print(f"\n{colored_text(f'🎉 ACCOUNT {account_index} AUTOMATION COMPLETED!', Colors.BOLD + Colors.GREEN)}")
        print(f"{colored_text(f'👤 Final stats - @{bot.username}: {bot.shares_posted} shares, {bot.likes_given} likes', Colors.CYAN)}")
        
    except KeyboardInterrupt:
        print(f"\n{colored_text(f'⛔ Independent automation stopped for Account {account_index}', Colors.RED)}")
    except Exception as e:
        print(f"\n{colored_text(f'❌ Independent automation error for Account {account_index}: {e}', Colors.RED)}")

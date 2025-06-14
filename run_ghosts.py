#!/usr/bin/env python3
"""
LLM-powered Ghost Bot Runner
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

def setup_logging(level: str, log_file: str = None):
    """Set up logging configuration"""
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        print(f"📝 Logging to file: {log_file}")
    
    # Adjust discord.py logging (it's quite verbose)
    if level.upper() != 'DEBUG':
        logging.getLogger('discord').setLevel(logging.WARNING)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
    
    # Adjust litellm logging
    if level.upper() != 'DEBUG':
        logging.getLogger('litellm').setLevel(logging.INFO)
    
    print(f"🔧 Logging level set to: {level.upper()}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="LLM-powered Ghost Bot System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Logging Examples:
  python run_ghosts.py --debug                    # Enable debug logging
  python run_ghosts.py --log-level INFO          # Set specific log level
  python run_ghosts.py --log-file ghosts.log     # Log to file
  python run_ghosts.py --debug --log-file debug.log  # Debug to file

Message Context Examples:
  python run_ghosts.py --message-limit 100       # More context (100 messages)
  python run_ghosts.py -m 20                     # Less context (20 messages)

Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging (shortcut for --log-level DEBUG)'
    )
    
    parser.add_argument(
        '--log-file', '-f',
        type=str,
        help='Log to file (in addition to console)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - only show warnings and errors'
    )
    
    parser.add_argument(
        '--message-limit', '-m',
        type=int,
        default=50,
        metavar='N',
        help='Number of recent messages to include as context (default: 50, max: 200)'
    )
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine log level
    if args.debug:
        log_level = 'DEBUG'
    elif args.quiet:
        log_level = 'WARNING'
    else:
        log_level = args.log_level
    
    # Validate message limit
    if args.message_limit < 1 or args.message_limit > 200:
        print(f"❌ Error: --message-limit must be between 1 and 200 (got {args.message_limit})")
        return
    
    # Set up logging
    setup_logging(log_level, args.log_file)
    
    # Load environment variables
    load_dotenv()
    
    print("🎭 Starting LLM-Powered Ghost Bot System")
    print("=" * 50)
    
    # Check for required environment variables
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ Error: DISCORD_BOT_TOKEN not found in environment variables.")
        print("📝 Please create a .env file with your Discord bot token:")
        print("   DISCORD_BOT_TOKEN=your_bot_token_here")
        return
    
    # Check for LLM API keys (optional, litellm can use different providers)
    llm_keys = {
        'OPENAI_API_KEY': 'OpenAI GPT models',
        'ANTHROPIC_API_KEY': 'Claude models', 
        'COHERE_API_KEY': 'Cohere models'
    }
    
    print("🔑 LLM API Key Status:")
    has_llm_key = False
    for key, description in llm_keys.items():
        if os.getenv(key):
            print(f"  ✅ {key} - {description}")
            has_llm_key = True
        else:
            print(f"  ❌ {key} - {description}")
    
    if not has_llm_key:
        print("\n⚠️  Warning: No LLM API keys found!")
        print("   The ghosts will use fallback responses if they can't connect to LLM services.")
        print("   Add API keys to .env file for full functionality:")
        print("   OPENAI_API_KEY=your_openai_key_here")
    
    print(f"\n📁 Bot configurations will be loaded from: ./bots/")
    print("🎭 Starting ghost system...")
    
    # Log some helpful debug info
    logger = logging.getLogger(__name__)
    logger.debug(f"🔍 Arguments: log_level={log_level}, log_file={args.log_file}")
    logger.debug(f"🔍 Python version: {sys.version}")
    
    try:
        # Import and run the ghost bot
        logger.info("🚀 Importing ghost bot system...")
        from ghosts.ghosts import bot, set_message_limit
        
        # Set the message limit
        set_message_limit(args.message_limit)
        
        logger.info("🤖 Starting Discord bot...")
        bot.run(token)
        
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
        print("\n👻 All ghosts have returned to the spirit realm. Goodbye!")
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies: pip install -e .")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        print(f"❌ Error running ghost bot: {e}")

if __name__ == "__main__":
    main() 
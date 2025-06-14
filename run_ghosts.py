#!/usr/bin/env python3
"""
LLM-powered Ghost Bot Runner
"""

import sys
import os
from dotenv import load_dotenv

def main():
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
    
    try:
        # Import and run the ghost bot
        from ghosts.ghosts import bot
        bot.run(token)
    except KeyboardInterrupt:
        print("\n👻 All ghosts have returned to the spirit realm. Goodbye!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies: pip install -e .")
    except Exception as e:
        print(f"❌ Error running ghost bot: {e}")

if __name__ == "__main__":
    main() 
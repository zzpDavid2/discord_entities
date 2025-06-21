# 👻 Ghosts Discord Bot

A simple Discord bot that replies with a fixed message when tagged.

## Features

- Responds with a spooky message when mentioned in any Discord channel
- Easy to set up and run
- Built with discord.py

## Setup

### 1. Install Dependencies

Make sure you have Python 3.12+ installed, then run:

```bash
pip install -e .
```

### 2. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable the following bot permissions:
   - Send Messages
   - Read Message History
   - Mention Everyone

### 3. Set up Environment Variables

Create a `.env` file in the project root:

```bash
cp env.example .env
```

Edit the `.env` file and add your bot token:

```
DISCORD_BOT_TOKEN=your_actual_bot_token_here
```

### 4. Invite the Bot to Your Server

1. In the Discord Developer Portal, go to OAuth2 > URL Generator
2. Select "bot" scope
3. Select the required permissions (Send Messages, Read Message History, Mention Everyone)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

## Running the Bot

You can run the bot in two ways:

### Option 1: Using the runner script
```bash
python run_bot.py
```

### Option 2: Directly running the bot module
```bash
python -m ghosts.bot
```

## Usage

Once the bot is running and invited to your server:

1. Tag the bot in any channel: `@YourBotName hello!`
2. The bot will reply with: "👻 Boo! You summoned the ghost bot! I'm here to haunt your Discord server. 👻"

## Customization

You can customize the bot's response by editing the `fixed_message` variable in `ghosts/bot.py`:

```python
fixed_message = "Your custom message here!"
```

## LLM-Powered Ghost System

### New: AI-Powered Ghost Personalities

The project now includes an advanced LLM-powered system where each ghost has its own personality, powered by AI models!

#### Running the LLM Ghost System

```bash
python run_ghosts.py
```

#### Ghost Configuration

Create ghost personality files in the `ghost_definitions/` directory:

**Basic Ghost Configuration (YAML):**
```yaml
name: "🦍 Tomas*"
handle: "tomas"
discord_avatar: "https://avatar.iran.liara.run/username?username=T+G"
description: "A first version of Tomas's ghost. Spooky!"
instructions: |
  You are Tomas's ghost, called 🦍 Tomas*, a delightfully eccentric digital ghost who's equal parts brilliant and slightly unhinged.
model: "anthropic/claude-sonnet-4-0"
temperature: 0.7
```

**Ghost with Custom LLM Configuration:**
```yaml
name: "🔮 Custom LLM Ghost"
handle: "custom"
description: "A ghost with custom LLM configuration"
instructions: "You are a ghost with custom LLM configuration."
model: "gpt-4o-mini"
temperature: 0.8
# Optional: Override global API configuration
api_url: "https://api.openai.com/v1"
api_key: "your-custom-api-key-here"
```

**JSON Format Example:**
```json
{
    "name": "🐦‍ Anna*",
    "handle": "anna",
    "description": "Anna's ghost with custom configuration",
    "instructions": "You are Anna's ghost, a brilliantly eccentric digital companion.",
    "model": "gpt-4.1-mini",
    "api_url": "https://api.openai.com/v1",
    "api_key": "your-custom-api-key"
}
```

#### LLM Setup

**Global Configuration (via .env):**
Add API keys to your `.env` file for default configuration:

```bash
# Choose your preferred LLM provider
OPENAI_API_KEY=your_openai_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_key_here  
# OR
COHERE_API_KEY=your_cohere_key_here
```

**Per-Ghost Configuration:**
Each ghost can override the global configuration with its own settings:

- `api_url`: Custom API endpoint (e.g., `https://api.openai.com/v1`)
- `api_key`: Custom API key for this specific ghost
- `model`: LLM model to use (e.g., `gpt-4o-mini`, `anthropic/claude-3-5-sonnet`)
- `temperature`: Response randomness (0.0-2.0)

**Example Use Cases:**
- Different ghosts using different LLM providers
- Self-hosted LLM instances for specific ghosts
- Different API keys for different ghosts
- Overriding global configuration on a per-ghost basis

#### Usage

- `@ghostname hello` - Summon a specific ghost
- `@GhostBot help` - Summon first available ghost
- Reply to any ghost's message - Automatically summon that ghost
- Reply + mention other ghosts - Multiple ghosts respond
- `@ghost1 @ghost2 message` - Tag multiple ghosts at once
- `!list` - List all loaded ghosts with their configurations
- `!status` - Show detailed system status including custom configurations
- `!test-ghost ghostname` - Test a specific ghost
- `!reload` - Reload ghost configurations
- `!ghost-chat` - Start a conversation between all ghosts

#### Features

- **Context Awareness**: Ghosts read recent messages for context
- **Unique Personalities**: Each ghost has its own AI-powered personality
- **Multiple LLM Support**: Works with OpenAI, Anthropic, Cohere, and more
- **Per-Ghost Configuration**: Each ghost can have its own API URL, key, and model
- **Hot Reloading**: Update ghost configs without restarting
- **Webhook Integration**: Ghosts appear as separate users
- **Ghost-to-Ghost Interactions**: Ghosts can tag and respond to each other
- **Enhanced Conversations**: Ghosts can debate, collaborate, and build on each other's ideas

## Troubleshooting

- Make sure your bot token is correct in the `.env` file
- Ensure the bot has the necessary permissions in your Discord server
- Check that the bot is online in your server's member list
- For LLM features, ensure you have valid API keys (global or per-ghost)
- Use `!status` to check system status and ghost configurations
- Check `ghost_definitions_examples/` for configuration examples

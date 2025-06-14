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

Create ghost personality files in the `bots/` directory:

#### LLM Setup

Add API keys to your `.env` file:

```bash
# Choose your preferred LLM provider
OPENAI_API_KEY=your_openai_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_key_here  
# OR
COHERE_API_KEY=your_cohere_key_here
```

#### Usage

- `@mybot hello` - Summon a specific ghost
- `@GhostBot help` - Summon first available ghost
- `!ghosts` - List all loaded ghosts
- `!test-ghost mybot` - Test a specific ghost
- `!reload-ghosts` - Reload ghost configurations

#### Features

- **Context Awareness**: Ghosts read the last 20 messages for context
- **Unique Personalities**: Each ghost has its own AI-powered personality
- **Multiple LLM Support**: Works with OpenAI, Anthropic, Cohere, and more
- **Hot Reloading**: Update ghost configs without restarting
- **Webhook Integration**: Ghosts appear as separate users

## Troubleshooting

- Make sure your bot token is correct in the `.env` file
- Ensure the bot has the necessary permissions in your Discord server
- Check that the bot is online in your server's member list
- For LLM features, ensure you have valid API keys
- Use `!ghost-status` to check system status

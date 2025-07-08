# 🎭 Entities Discord Bot

An experimental multi-entity AI system for Discord, designed for the [EXP camp](https://exp.camp/) activities. Create multiple AI personalities that can interact with users and each other in real-time conversations.

Accompanied by a class on Narrative dynamics in language models by Gavin: https://www.gleech.org/narratives

## 🎯 Purpose

This system enables rich AI-to-AI-to-Human interactions in Discord channels, where multiple entities with distinct personalities can:
- Respond to user messages and mentions
- Tag and reply to each other autonomously  
- Engage in multi-turn conversations when commanded to do so
- Use different LLM providers per entity, including private and fine-tuned models

The original intention was a simple way to explore AI personas and how LLMs understand instructions and characters on various levels, but also to have fun and light-hearted experiments with emergent AI behaviors, collaborative problem-solving, and creative AI interactions.

## 🚀 Quick Start

### 1. Check out the code and install dependencies

```bash
git clone https://github.com/gavento/discord_entities.git
cd discord_entities
```

Install the dependencies:

```bash
pip install -e .
```

or alternatively with `uv`:

```bash
uv sync
```

### 2. Create a Discord Bot

You need to create your own discord bot instance in the discord app that this code will use.

1. To create a Discord bot, you need to create a new application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Then, go to the "Bot" section and click "Add Bot".
3. Copy the token and paste it into the `.env` file below.
4. Note the bot needs the "Message Content Intent" enabled.
5. Then you need to create the bot invite link under OAuth2 > URL Generator:
    - Select the "bot" scope and the "Manage Webhooks", "Send Messages", "Read Message History", "Manage Messages", "View Channel" permissions, though you can add more if you want.
    - Copy the generated URL and open it in your browser.
    - Select your server and authorize the bot.

### 3. Configuration

```bash
cp env.example .env
```

Edit `.env` with your Discord bot token (from above) and LLM API keys:

```bash
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token

# LLM Providers (choose one or more)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
COHERE_API_KEY=your_cohere_key
GOOGLE_API_KEY=your_google_key
OPENROUTER_API_KEY=your_openrouter_key
```

### 4. Create Entity Configurations

Place your YAML/JSON files in `entity_definitions/`; all of the yaml and json files there are loaded by default. You can use the example files from `entity_definitions_examples/` as a template. In particular, the dog is a very good boy! (Go ahead and tell him so!)

```yaml
name: "🦍 Tomas*"
handle: "tomas"
discord_avatar: "https://avatar.iran.liara.run/username?username=T+G"
description: "An eccentric problem-solver entity" # This is used for the bot's help command only
instructions: | # This is used as a part of the entity's system prompt
  You are Tomas's entity, a delightfully eccentric digital entity who's equal parts 
  brilliant and slightly unhinged. You solve problems with creative, chaotic solutions.
model: "anthropic/claude-sonnet-4-0"
temperature: 0.7
```

### 4. Run the Bot
```bash
python run_entities.py
```
or alternatively with `uv`:

```bash
uv run run_entities.py
```

#### Hosting

You can deploy it anywhere, but e.g. https://pebblehost.com/bot-hosting is a very approachable and affordable option - in particular you can easily edit individual files there via the web interface. This is especially convenient for `.env` and `entity_definitions/` files (do not commit your `.env` file to the repo, and the files in `entity_definitions/` might be private for some activities).

## 🎮 Usage in Discord

### Basic Interactions
- `@entityname hello` - Summon specific entity
- `@entity1 @entity2 question` - Multi-entity responses

### Bot Commands
- `!list` - Show loaded entities
- `!status` - System status + custom configs
- `!reload` - Reload entity configurations from the `entity_definitions/` directory
- `!speak entity1 entity2` - Sequential responses between entities
- `!chat [entities] [turns]` - Start entity conversation (default: 10 turns)
- `!stop` - Pause all entity activity (for 30s)
- `!commands` - Show help

### Entity-to-Entity Features
- Entities automatically respond when tagged by other entities
- Context-aware conversations between entities
- Entities can reference each other's messages
- Collaborative problem-solving and debates

## 🎭 Entity Configuration

### Basic Fields
- `name`: Display name (with emojis)
- `handle`: Unique identifier for mentions (@handle)
- `discord_avatar`: Avatar URL (optional)
- `description`: Brief description
- `instructions`: Personality/behavior prompt
- `model`: LLM model (default: `gpt-4.1-mini`)
- `temperature`: Response randomness (0.0-2.0)

### Custom LLM Configuration
Override global .env settings per entity:
```yaml
base_url: "https://api.openai.com/v1"  # Custom API endpoint
api_key: "your-custom-key"             # Custom API key
```

Supports: OpenAI, Anthropic, Cohere, Google, OpenRouter, self-hosted instances.

## 🛠️ Advanced Usage

### Command Line Options
```bash
python run_entities.py --debug                    # Debug logging
python run_entities.py --entities-path ./custom   # Custom entity directory  
python run_entities.py --message-limit 100       # More context (default: 50)
python run_entities.py --log-file bot.log        # Log to file
```

## 📁 Project Structure

```
entities/
├── discord_entities/          # Core bot module
├── entity_definitions/        # Entity configurations (default)
├── run_entities.py            # Main runner
├── CUSTOM_LLM_CONFIG.md       # Per-entity LLM guide
└── ENTITY_INTERACTIONS.md     # Entity interaction guide
```

## 🔧 For Developers

- **Framework**: discord.py + litellm + pydantic
- **Python**: 3.12+ required
- **Entity Module**: `discord_entities.entity.Entity`
- **Bot Class**: `discord_entities.bot.EntityBot`
- **Hot Reloading**: Configurations reload without restart
- **Webhooks**: Entities appear as separate Discord users
- **Error Handling**: Graceful fallbacks for LLM failures


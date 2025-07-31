# 🎭 Entities Discord Bot

An experimental multi-entity AI system for Discord, designed for the [EXP camp](https://exp.camp/) activities. Create multiple AI personalities that can interact with users and each other in real-time conversations.

Accompanied by a class on Narrative dynamics in language models by Gavin: https://www.gleech.org/narratives

## 🎯 Purpose

This system enables rich AI-to-AI-to-Human interactions in Discord channels, where multiple entities with distinct personalities can:
- Respond to user messages and mentions
- Tag and reply to each other autonomously  
- Engage in multi-turn conversations when commanded to do so
- Use different LLM providers per entity, including private and fine-tuned models
- **Load new entities directly from Discord file uploads** 🆕

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

### 2. Create a Discord Bot Application

You need to create your own Discord bot instance that this code will use.

#### Step 1: Create Application
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Give your bot a name (e.g., "My Entity Bot")
4. Click **"Create"**

#### Step 2: Create Bot User
1. In the left sidebar, click **"Bot"**
2. Click **"Add Bot"** (or **"Reset Token"** if bot already exists)
3. **Copy the bot token** - you'll need this for your `.env` file
4. ⚠️ **Keep this token secret!** Never share it publicly

#### Step 3: Enable Required Permissions
Still in the **"Bot"** section, scroll down to **"Privileged Gateway Intents"**:

✅ **Enable these intents:**
- **MESSAGE CONTENT INTENT** - Required for reading messages, file uploads, and entity mentions

#### Step 4: Generate Invite Link
1. In the left sidebar, click **"OAuth2"** → **"URL Generator"**
2. **Select Scopes:**
   - ✅ `bot` (required)
3. **Select Bot Permissions:**
   - ✅ **Send Messages** - Basic messaging functionality
   - ✅ **Read Message History** - Read conversation context for entities
   - ✅ **Manage Messages** - Bot management features
   - ✅ **View Channels** - See channels to respond in
   - ✅ **Manage Webhooks** - **IMPORTANT:** Create entity personas with custom names/avatars
   - ✅ **Attach Files** - Process uploaded entity configuration files
   - ✅ **Use Slash Commands** (optional but recommended)

4. **Copy the generated URL** at the bottom of the page

#### Step 5: Add Bot to Your Server
1. **Open the invite URL** in your browser
2. **Select your Discord server** from the dropdown
3. **Click "Authorize"** to add the bot to your server
4. The bot will appear in your server's member list (offline until you start it)

### 3. Configuration

```bash
cp env.example .env
```

Edit `.env` with your Discord bot token (from step 2.3 above) and LLM API keys:

```bash
# Required - Discord Bot Token from Developer Portal
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# LLM Providers (choose one or more)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
COHERE_API_KEY=your_cohere_key
GOOGLE_API_KEY=your_google_key
OPENROUTER_API_KEY=your_openrouter_key
```

### 4. Create Entity Configurations

**Option A: Upload Files to Discord** 🆕
- Drag and drop `.json` or `.yaml` entity files into any Discord channel
- The bot automatically loads them and saves to `entity_definitions/`
- No commands needed - instant loading!

**Option B: Manual File Placement**
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

### 5. Run the Bot
```bash
python run_entities.py
```
or alternatively with `uv`:

```bash
uv run run_entities.py
```

### 6. Test Your Bot
1. **Check bot status:** Type `!status` in your Discord server
2. **List entities:** Type `!list` to see loaded entities
3. **Try an entity:** `@dog hello!` (if you have the example dog entity)
4. **Upload a new entity:** Drag a `.json` or `.yaml` file into Discord

## 🔧 Troubleshooting

### Common Issues:

**"PrivilegedIntentsRequired" Error:**
- ✅ Go to Discord Developer Portal → Your App → Bot
- ✅ Enable "MESSAGE CONTENT INTENT" under Privileged Gateway Intents
- ✅ Save changes and restart your bot

**Bot appears offline:**
- ✅ Check your `DISCORD_BOT_TOKEN` in `.env`
- ✅ Ensure the token hasn't been regenerated
- ✅ Check console for error messages

**"Forbidden" webhook errors:**
- ✅ Ensure bot has "Manage Webhooks" permission
- ✅ Re-invite bot with correct permissions using OAuth2 URL Generator

**File uploads not working:**
- ✅ Check bot has "Attach Files" and "Read Message History" permissions
- ✅ Ensure "MESSAGE CONTENT INTENT" is enabled

#### Hosting

You can deploy it anywhere, but e.g. https://pebblehost.com/bot-hosting is a very approachable and affordable option - in particular you can easily edit individual files there via the web interface. This is especially convenient for `.env` and `entity_definitions/` files (do not commit your `.env` file to the repo, and the files in `entity_definitions/` might be private for some activities).

## 🎮 Usage in Discord

### Basic Interactions
- `@entityname [message]` - Summon specific entity
- `@entity1 @entity2 [question]` - Multi-entity responses
- **Drag & drop `.json`/`.yaml` files** - Instantly load new entities 🆕

### Bot Commands
- `!list` - Show loaded entities
- `!status` - System status + custom configs
- `!reload` - Reload entity configurations from the `entity_definitions/` directory
- `!speak entity1 entity2` - Sequential responses between entities
- `!chat [entities] [turns]` - Start entity conversation (default: 10 turns)
- `!stop` - Pause all entity activity (for 30s)
- `!commands` - Show help

### Entity Loading Methods 🆕
1. **Discord Upload**: Drag `.json`/`.yaml` files into Discord - instant loading!
2. **File System**: Place files in `entity_definitions/` and use `!reload`
3. **Examples**: Copy from `entity_definitions_examples/` folder

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

### Example Entity File (JSON)
```json
{
    "name": "🐕 Buddy",
    "handle": "buddy",
    "discord_avatar": "https://example.com/dog.jpg",
    "description": "A friendly golden retriever",
    "instructions": "You are a friendly golden retriever with human-level intelligence. You're curious, loyal, and love to help!",
    "model": "gpt-4.1-mini",
    "temperature": 0.8
}
```

### Example Entity File (YAML)
```yaml
name: "🤖 Assistant"
handle: "helper"
description: "A helpful AI assistant"
instructions: |
  You are a helpful AI assistant who loves to solve problems
  and help users with their questions.
model: "gpt-4.1-mini"
temperature: 0.5
```

## 🛠️ Advanced Usage

### Command Line Options
```bash
python run_entities.py --debug                    # Debug logging
python run_entities.py --entities-path ./custom   # Custom entity directory  
python run_entities.py --message-limit 100       # More context (default: 50)
python run_entities.py --log-file bot.log        # Log to file
```

### File Upload Features 🆕
- **Automatic Processing**: Files are processed immediately upon upload
- **Format Support**: Both JSON and YAML formats supported
- **Validation**: Full entity validation with helpful error messages  
- **Conflict Handling**: Warns if entity handle already exists
- **Auto-Save**: Successfully uploaded entities are saved to `entity_definitions/`
- **Instant Usage**: New entities are immediately available for interaction

## 📁 Project Structure

```
entities/
├── discord_entities/          # Core bot module
├── entity_definitions/        # Entity configurations (default)
├── entity_definitions_examples/ # Example entity files
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
- **File Upload**: Automatic processing of JSON/YAML attachments


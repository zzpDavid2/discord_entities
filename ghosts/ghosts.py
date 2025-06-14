import discord
from discord.ext import commands
import os
import re
import asyncio
import logging
from dotenv import load_dotenv
from typing import Dict, List, Optional
from .ghost import Ghost, load_ghosts_from_directory

# Set up logging for this module
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global storage for ghosts and webhooks
GHOSTS: Dict[str, Ghost] = {}
channel_webhooks = {}
MESSAGE_LIMIT = 50  # Default, will be overridden by CLI args

def set_message_limit(limit: int):
    """Set the global message limit for all ghosts"""
    global MESSAGE_LIMIT
    MESSAGE_LIMIT = limit
    logger.info(f"📝 Message limit set to {MESSAGE_LIMIT}")

async def get_or_create_webhook(channel):
    """Get existing webhook for channel or create new one"""
    if channel.id in channel_webhooks:
        return channel_webhooks[channel.id]
    
    # Check if webhook already exists
    webhooks = await channel.webhooks()
    webhook = None
    
    for wh in webhooks:
        if wh.name == "GhostBot LLM":
            webhook = wh
            break
    
    # Create webhook if it doesn't exist
    if not webhook:
        try:
            webhook = await channel.create_webhook(name="GhostBot LLM")
        except discord.Forbidden:
            return None
    
    channel_webhooks[channel.id] = webhook
    return webhook

async def get_recent_messages(channel, limit: int = 50) -> List[discord.Message]:
    """Get recent messages from channel for context"""
    messages = []
    async for message in channel.history(limit=limit):
        messages.append(message)
    
    # Return in chronological order (oldest first)
    return list(reversed(messages))

def find_ghost_by_mention(message_content: str) -> Optional[Ghost]:
    """Find which ghost is being mentioned in the message"""
    message_lower = message_content.lower()
    
    # Check for pseudo-mentions like "@tomas", "@anna"
    pseudo_mention_pattern = r'@(\w+)'
    pseudo_mentions = re.findall(pseudo_mention_pattern, message_lower)
    
    # Check direct mentions first
    for mention in pseudo_mentions:
        if mention in GHOSTS:
            return GHOSTS[mention]
    
    # Check aliases
    for ghost in GHOSTS.values():
        for alias in ghost.get_aliases():
            if alias in message_lower:
                return ghost
    
    return None

@bot.event
async def on_ready():
    global GHOSTS
    logger.info(f'🤖 {bot.user} has connected to Discord!')
    
    # Load ghosts from bots directory
    bots_dir = os.path.join(os.path.dirname(__file__), '..', 'bots')
    logger.info(f'📁 Looking for ghost configs in: {bots_dir}')
    
    GHOSTS = load_ghosts_from_directory(bots_dir)
    
    if GHOSTS:
        logger.info(f'🎭 Ghost system ready with {len(GHOSTS)} ghosts:')
        for handle, ghost in GHOSTS.items():
            logger.info(f'  👻 {ghost.name} (@{handle}) using {ghost.model}')
    else:
        logger.warning('⚠️  No ghosts loaded! Check your bots directory.')
    
    logger.info('🚀 Bot is ready to receive ghost summons!')

@bot.event
async def on_message(message):
    # Don't respond to bot messages
    if message.author.bot:
        return
    
    selected_ghost = None
    is_direct_mention = False
    
    # Check for direct bot mention
    if bot.user.mentioned_in(message):
        is_direct_mention = True
        logger.debug(f"🔔 Direct bot mention from {message.author.display_name} in #{message.channel.name}")
        # Look for specific ghost in the message
        selected_ghost = find_ghost_by_mention(message.content)
        if selected_ghost:
            logger.debug(f"🎯 Specific ghost requested: {selected_ghost.name}")
    
    # Check for pseudo-mentions like "@tomas", "@anna"
    if not is_direct_mention:
        selected_ghost = find_ghost_by_mention(message.content)
        if selected_ghost:
            logger.debug(f"👻 Pseudo-mention detected for {selected_ghost.name} from {message.author.display_name}")
    
    if selected_ghost or is_direct_mention:
        # If no specific ghost selected and it's a direct mention, pick first available
        if not selected_ghost and is_direct_mention and GHOSTS:
            selected_ghost = list(GHOSTS.values())[0]
            logger.debug(f"🎲 No specific ghost requested, using default: {selected_ghost.name}")
        
        if selected_ghost:
            logger.info(f"👻 Summoning {selected_ghost.name} for {message.author.display_name} in #{message.channel.name}")
            await handle_ghost_response(message, selected_ghost)
        else:
            logger.warning(f"⚠️  Ghost summon failed - no ghosts available for {message.author.display_name}")
    
    # Process commands
    await bot.process_commands(message)

async def handle_ghost_response(message: discord.Message, ghost: Ghost):
    """Handle generating and sending a ghost's response"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info(f"🎬 {ghost.name} starting response generation for {message.author.display_name}")
        
        # Show typing indicator
        async with message.channel.typing():
            # Get recent messages for context  
            logger.debug(f"📚 {ghost.name} gathering message history from #{message.channel.name} (limit: {MESSAGE_LIMIT})")
            recent_messages = await get_recent_messages(message.channel, limit=MESSAGE_LIMIT)
            
            # Format messages for LLM
            llm_messages = ghost.format_discord_messages_for_llm(recent_messages, message_limit=MESSAGE_LIMIT)
            logger.debug(f"💬 {ghost.name} formatted {len(llm_messages)} messages for context")
            
            # Generate response using the ghost's LLM
            response = await ghost.call_llm(llm_messages, max_tokens=400)
            
            # Try to send via webhook for better appearance
            webhook = await get_or_create_webhook(message.channel)
            
            if webhook:
                try:
                    logger.debug(f"📤 {ghost.name} sending response via webhook")
                    await webhook.send(
                        content=response,
                        username=ghost.discord_username,
                        avatar_url=str(ghost.discord_avatar)
                    )
                    
                    elapsed = asyncio.get_event_loop().time() - start_time
                    logger.info(f"✅ {ghost.name} response sent via webhook in {elapsed:.2f}s")
                    return
                except Exception as e:
                    logger.error(f"❌ {ghost.name} webhook error: {type(e).__name__}: {e}")
                    logger.debug(f"🔍 Webhook error details for {ghost.name}", exc_info=True)
            
            # Fallback to regular reply
            logger.debug(f"🔄 {ghost.name} falling back to regular reply")
            await message.reply(f"**{ghost.discord_username}**: {response}")
            
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ {ghost.name} response sent via fallback in {elapsed:.2f}s")
            
    except Exception as e:
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ {ghost.name} response generation failed after {elapsed:.2f}s: {type(e).__name__}: {e}")
        logger.debug(f"🔍 Ghost response error details for {ghost.name}", exc_info=True)
        
        error_msg = f"*{ghost.name} flickers and fades* Something went wrong in the spirit realm... ({str(e)[:100]})"
        try:
            await message.reply(error_msg)
            logger.warning(f"🔄 {ghost.name} sent error message to user")
        except Exception as reply_error:
            logger.error(f"❌ {ghost.name} failed to send error message: {reply_error}")

@bot.command(name='ghosts')
async def list_ghosts(ctx):
    """List all loaded ghosts"""
    if not GHOSTS:
        await ctx.send("👻 No ghosts are currently loaded! Check the bots directory.")
        return
    
    message = "👻 **Loaded Ghosts:**\n\n"
    
    for handle, ghost in GHOSTS.items():
        aliases = ghost.get_aliases()
        alias_str = ', '.join([f"`@{alias}`" for alias in aliases])
        message += f"**{ghost.discord_username}**\n"
        message += f"  • Handle: `@{handle}`\n"
        message += f"  • Aliases: {alias_str}\n"
        message += f"  • Model: `{ghost.model}` (temp: {ghost.temperature})\n"
        message += f"  • Description: {ghost.description}\n\n"
    
    message += "**Usage:**\n"
    message += f"• `@{list(GHOSTS.keys())[0]} hello` - Summon specific ghost\n"
    message += f"• `@{bot.user.display_name} help` - Summon first available ghost\n"
    message += "• `!reload-ghosts` - Reload ghost configurations"
    
    await ctx.send(message)

@bot.command(name='reload-ghosts')
async def reload_ghosts(ctx):
    """Reload ghost configurations from files"""
    global GHOSTS
    
    bots_dir = os.path.join(os.path.dirname(__file__), '..', 'bots')
    old_count = len(GHOSTS)
    
    GHOSTS = load_ghosts_from_directory(bots_dir)
    new_count = len(GHOSTS)
    
    if new_count > 0:
        await ctx.send(f"🔄 **Reloaded {new_count} ghosts** (was {old_count})\n\nUse `!ghosts` to see the updated list.")
    else:
        await ctx.send("❌ **No ghosts loaded!** Check your bots directory and file formats.")

@bot.command(name='ghost-status')
async def ghost_status(ctx):
    """Show detailed status of the ghost system"""
    webhook_status = "Enabled" if channel_webhooks else "Limited"
    
    message = "🎭 **Ghost System Status**\n\n"
    message += f"**Loaded Ghosts:** {len(GHOSTS)}\n"
    message += f"**Active Channels:** {len(channel_webhooks)}\n"
    message += f"**Webhooks:** {webhook_status}\n\n"
    
    if GHOSTS:
        message += "**Ghost Models:**\n"
        model_counts = {}
        for ghost in GHOSTS.values():
            model_counts[ghost.model] = model_counts.get(ghost.model, 0) + 1
        
        for model, count in model_counts.items():
            message += f"  • {model}: {count} ghost(s)\n"
        
        message += f"\n**Try:** `@{list(GHOSTS.keys())[0]} hello` or `!test-ghost`"
    else:
        message += "⚠️ **No ghosts loaded!** Use `!reload-ghosts` to load them."
    
    await ctx.send(message)

@bot.command(name='test-ghost')
async def test_ghost(ctx, ghost_handle: str = None):
    """Test a specific ghost or the first available one"""
    if not GHOSTS:
        await ctx.send("❌ No ghosts loaded! Use `!reload-ghosts` first.")
        return
    
    # Select ghost
    if ghost_handle:
        ghost = GHOSTS.get(ghost_handle.lower())
        if not ghost:
            available = ', '.join(GHOSTS.keys())
            await ctx.send(f"❌ Ghost '{ghost_handle}' not found! Available: {available}")
            return
    else:
        ghost = list(GHOSTS.values())[0]
    
    # Test the ghost
    test_message = f"Hello {ghost.name}! This is a test to see if you're working properly."
    
    try:
        async with ctx.typing():
            # Create a simple test conversation
            test_messages = [
                {"role": "user", "content": f"{ctx.author.display_name}: {test_message}"}
            ]
            
            response = await ghost.call_llm(test_messages, max_tokens=200)
            
            await ctx.send(f"✅ **Test successful for {ghost.discord_username}:**\n\n{response}")
            
    except Exception as e:
        await ctx.send(f"❌ **Test failed for {ghost.name}:** {str(e)}")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables.")
        exit(1)
    
    bot.run(token) 
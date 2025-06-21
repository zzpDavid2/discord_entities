import asyncio
import logging
import random
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from .ghost_group import GhostGroup

# Set up logging for this module
logger = logging.getLogger(__name__)


class GhostBot(commands.Bot):
    """Discord bot for managing and interacting with ghosts"""

    def __init__(self, message_limit: int = 50, ghost_path: str = None):
        """
        Initialize the ghost bot

        Args:
            message_limit: Number of messages to include in context
            ghost_path: Path to directory containing ghost configs. If None, uses default ./ghosts/
        """
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

        self.ghost_group = GhostGroup()
        self.channel_webhooks: Dict[int, discord.Webhook] = {}
        self.message_limit = message_limit
        self.ghost_path = ghost_path
        assert self.ghost_path is not None, "ghost_path must be provided"

        # Remove any existing listeners to prevent duplicates
        self.remove_listener(self.on_ready, "on_ready")
        self.remove_listener(self.on_message, "on_message")

        # Register event handlers
        self.add_listener(self.on_ready, "on_ready")
        self.add_listener(self.on_message, "on_message")
        logger.debug("Event handlers registered")

        # Register commands
        self.add_command(commands.Command(self.cmd_list, name="list"))
        self.add_command(commands.Command(self.cmd_reload, name="reload"))
        self.add_command(commands.Command(self.cmd_status, name="status"))
        self.add_command(commands.Command(self.cmd_test_ghost, name="test-ghost"))
        self.add_command(commands.Command(self.cmd_commands, name="commands"))
        async def speak(ctx, *args):
            return await self.cmd_speak(ctx, *args)
        self.add_command(commands.Command(speak, name="speak", rest_is_raw=True))
        async def ghost_chat(ctx, *args):
            return await self.cmd_ghost_chat(ctx, *args)
        self.add_command(commands.Command(ghost_chat, name="ghost-chat"))

        # Add error handler for unknown commands
        self.add_listener(self.on_command_error, "on_command_error")

    def set_message_limit(self, limit: int):
        """Set the message limit for all ghosts"""
        self.message_limit = limit
        logger.info(f"📝 Message limit set to {self.message_limit}")

    async def get_or_create_webhook(self, channel) -> Optional[discord.Webhook]:
        """Get existing webhook for channel or create new one"""
        if channel.id in self.channel_webhooks:
            return self.channel_webhooks[channel.id]

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

        self.channel_webhooks[channel.id] = webhook
        return webhook

    async def get_recent_messages(
        self, channel, limit: int = None
    ) -> List[discord.Message]:
        """Get recent messages from channel for context"""
        if limit is None:
            limit = self.message_limit

        messages = []
        async for message in channel.history(limit=limit):
            messages.append(message)

        # Return in chronological order (oldest first)
        return list(reversed(messages))

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"🤖 {self.user} has connected to Discord!")

        # Load ghosts from configured directory
        logger.info(f"📁 Looking for ghost configs in: {self.ghost_path}")
        try:
            self.ghost_group = GhostGroup.load_from_directory(self.ghost_path)
        except ValueError as e:
            # Check if this is the specific "no bots available" error
            if "No ghost config files found" in str(e) or "No ghosts were successfully loaded" in str(e):
                logger.warning(f"⚠️  No ghost config files found in {self.ghost_path}")
                logger.warning("⚠️  Please add ghost configuration files to the ghost_definitions directory")
                # Initialize an empty ghost group so the bot can still function
                self.ghost_group = GhostGroup()
            else:
                # Re-raise other ValueError exceptions
                raise

        if len(self.ghost_group) > 0:
            logger.info(f"🎭 Ghost system ready with {len(self.ghost_group)} ghosts:")
            for ghost_key, ghost in self.ghost_group:
                logger.info(
                    f"  👻 {ghost.name} (handle: {ghost.handle}) using {ghost.model}"
                )
        else:
            logger.warning("⚠️  No ghosts loaded! Check your bots directory.")

        logger.info("🚀 Bot is ready to receive ghost summons!")

    async def activate_ghost(
        self,
        ghost,
        message: Optional[discord.Message] = None,
        prompt: Optional[str] = None,
    ):
        """
        Activate a ghost to speak, optionally in response to a message

        Args:
            ghost: The ghost to activate
            message: Optional message to reply to
            prompt: Optional custom prompt to use instead of message content
        """
        start_time = asyncio.get_event_loop().time()
        channel = message.channel if message else None

        try:
            logger.info(f"🎬 {ghost.name} starting response generation")

            # Show typing indicator if we have a channel
            if channel:
                async with channel.typing():
                    # Get recent messages for context
                    logger.debug(
                        f"📚 {ghost.name} gathering message history from #{channel.name} (limit: {self.message_limit})"
                    )
                    recent_messages = await self.get_recent_messages(channel)

                    # Format messages for LLM
                    llm_messages = ghost.format_discord_messages_for_llm(
                        recent_messages, message_limit=self.message_limit
                    )
                    logger.debug(
                        f"💬 {ghost.name} formatted {len(llm_messages)} messages for context"
                    )

                    # Generate response using the ghost's LLM
                    response = await ghost.call_llm(llm_messages, max_tokens=400)

                    # Try to send via webhook for better appearance
                    webhook = await self.get_or_create_webhook(channel)

                    if webhook:
                        try:
                            logger.debug(
                                f"📤 {ghost.name} sending response via webhook"
                            )

                            # Prepare webhook kwargs
                            webhook_kwargs = {
                                "content": response,
                                "username": ghost.name,
                            }

                            # Add avatar if specified
                            if ghost.discord_avatar:
                                webhook_kwargs["avatar_url"] = str(ghost.discord_avatar)

                            await webhook.send(**webhook_kwargs)

                            elapsed = asyncio.get_event_loop().time() - start_time
                            logger.info(
                                f"✅ {ghost.name} response sent via webhook in {elapsed:.2f}s"
                            )
                            return
                        except Exception as e:
                            logger.error(
                                f"❌ {ghost.name} webhook error: {type(e).__name__}: {e}"
                            )
                            logger.debug(
                                f"🔍 Webhook error details for {ghost.name}",
                                exc_info=True,
                            )

                    # Fallback to regular reply
                    logger.debug(f"🔄 {ghost.name} falling back to regular reply")
                    if message:
                        await message.reply(f"**{ghost.name}**: {response}")
                    else:
                        await channel.send(f"**{ghost.name}**: {response}")

                    elapsed = asyncio.get_event_loop().time() - start_time
                    logger.info(
                        f"✅ {ghost.name} response sent via fallback in {elapsed:.2f}s"
                    )

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.error(
                f"❌ {ghost.name} response generation failed after {elapsed:.2f}s: {type(e).__name__}: {e}"
            )
            logger.debug(
                f"🔍 Ghost response error details for {ghost.name}", exc_info=True
            )

            error_msg = f"*{ghost.name} flickers and fades* Something went wrong in the spirit realm... ({str(e)[:100]})"
            try:
                if message:
                    await message.reply(error_msg)
                elif channel:
                    await channel.send(error_msg)
                logger.warning(f"🔄 {ghost.name} sent error message to user")
            except Exception as reply_error:
                logger.error(
                    f"❌ {ghost.name} failed to send error message: {reply_error}"
                )

    async def on_message(self, message):
        """Handle incoming messages"""
        # Add message ID tracking to prevent duplicate processing
        if (
            hasattr(self, "_last_processed_message")
            and message.id == self._last_processed_message
        ):
            logger.debug(f"Skipping duplicate message {message.id}")
            return
        self._last_processed_message = message.id

        # Don't respond to regular bot messages (but allow webhook messages from ghosts)
        if message.author.bot and not (hasattr(message, "webhook_id") and message.webhook_id):
            return

        # Process commands first (but only for non-ghost messages)
        if message.content.startswith(self.command_prefix):
            # Only process commands from non-ghost messages
            if not (hasattr(message, "webhook_id") and message.webhook_id):
                await self.process_commands(message)
            return

        # Handle mentions and pseudo-mentions
        mentioned_ghosts = []
        is_direct_mention = False

        # Check for direct bot mention
        if self.user.mentioned_in(message):
            is_direct_mention = True
            logger.debug(
                f"🔔 Direct bot mention from {message.author.display_name} in #{message.channel.name}"
            )
            # Look for specific ghosts in the message
            mentioned_ghosts = self.ghost_group.find_ghost_by_mention(message.content)
            if mentioned_ghosts:
                logger.debug(
                    f"🎯 Specific ghosts requested: {', '.join(ghost.name for ghost in mentioned_ghosts)}"
                )

        # Check for pseudo-mentions like "@tomas", "@anna"
        mentioned_ghosts = self.ghost_group.find_ghost_by_mention(message.content)
        if mentioned_ghosts:
            logger.debug(
                f"👻 Pseudo-mentions detected for: {', '.join(ghost.name for ghost in mentioned_ghosts)} from {message.author.display_name}"
            )

        # Check for replies to ghost messages
        if message.reference:
            try:
                # Fetch the referenced message
                referenced_message = await message.channel.fetch_message(message.reference.message_id)
                
                # Check if the referenced message was sent by a ghost
                ghost_handle = self.identify_ghost_from_message(referenced_message)
                # logger.info(f"👻 Referenced message: {referenced_message.content} from {referenced_message.author.display_name!r}, ghost handle: {ghost_handle!r}")
                if ghost_handle:
                    ghost = self.ghost_group.get(ghost_handle)
                    if ghost:
                        # Add the replied-to ghost to the list if not already present
                        if ghost not in mentioned_ghosts:
                            mentioned_ghosts.insert(0, ghost)
                            logger.debug(
                                f"💬 Reply detected to {ghost.name}'s message from {message.author.display_name}"
                            )
                        else:
                            logger.debug(
                                f"💬 Reply to {ghost.name}'s message, but {ghost.name} already mentioned in message"
                            )
            except Exception as e:
                logger.debug(f"Could not fetch referenced message: {e}")

        # NEW: Check if this message is from a ghost and contains mentions of other ghosts
        if (hasattr(message, "webhook_id") and message.webhook_id and 
            hasattr(message.author, "discriminator") and message.author.discriminator == "0000"):
            
            # This is a ghost message - check if it mentions other ghosts
            ghost_mentions = self.ghost_group.find_ghost_by_mention(message.content)
            if ghost_mentions:
                logger.debug(
                    f"👻 Ghost {message.author.name} is mentioning other ghosts: {', '.join(ghost.name for ghost in ghost_mentions)}"
                )
                # Add mentioned ghosts to the response list
                for ghost in ghost_mentions:
                    if ghost not in mentioned_ghosts:
                        mentioned_ghosts.append(ghost)

        if mentioned_ghosts or is_direct_mention:
            # If no specific ghosts selected and it's a direct mention, a random ghost is summoned
            if not mentioned_ghosts and is_direct_mention and len(self.ghost_group) > 0:
                mentioned_ghosts = [random.choice(list(self.ghost_group.values()))]
                logger.debug(
                    f"🎲 No specific ghosts requested, using random: {mentioned_ghosts[0].name}"
                )

            if mentioned_ghosts:
                # Remove duplicates while preserving order
                unique_ghosts = []
                seen_ghosts = set()
                for ghost in mentioned_ghosts:
                    if ghost.name not in seen_ghosts:
                        unique_ghosts.append(ghost)
                        seen_ghosts.add(ghost.name)
                
                logger.info(
                    f"👻 Summoning {len(unique_ghosts)} ghost(s) for {message.author.display_name} in #{message.channel.name}: {', '.join(ghost.name for ghost in unique_ghosts)}"
                )
                
                for ghost in unique_ghosts:
                    await self.activate_ghost(ghost, message)
            else:
                logger.warning(
                    f"⚠️  Ghost summon failed - no ghosts available for {message.author.display_name}"
                )

    async def cmd_list(self, ctx, *args):
        """List all loaded ghosts"""
        if len(self.ghost_group) == 0:
            await ctx.send(
                "👻 No ghosts are currently loaded! Check the bots directory."
            )
            return

        message = "👻 **Loaded Ghosts:**\n\n"

        for ghost_key, ghost in self.ghost_group:
            message += f"**{ghost.name}**\n"
            message += f"  • Handle: `@{ghost.handle}`\n"
            message += f"  • Model: `{ghost.model}` (temp: {ghost.temperature})\n"
            message += f"  • Description: {ghost.description}\n\n"

        message += "**Usage:**\n"
        message += (
            f"• `@{list(self.ghost_group.keys())[0]} hello` - Summon specific ghost\n"
        )
        message += (
            f"• `@{self.user.display_name} help` - Summon first available ghost\n"
        )
        message += "• Reply to any ghost's message - Automatically summon that ghost\n"
        message += "• Reply + mention other ghosts - Multiple ghosts respond\n"
        message += "• `@ghost1 @ghost2 message` - Tag multiple ghosts at once\n"
        message += "• `!ghost-chat` - Start a conversation between all ghosts\n"
        message += "• `!reload` - Reload ghost configurations"

        await ctx.send(message)

    async def cmd_reload(self, ctx, *args):
        """Reload ghost configurations from files"""
        old_count = len(self.ghost_group)

        self.ghost_group = GhostGroup.load_from_directory(self.ghost_path)
        new_count = len(self.ghost_group)

        if new_count > 0:
            await ctx.send(
                f"🔄 **Reloaded {new_count} ghosts** (was {old_count})\n\nUse `!list` to see the updated list."
            )
        else:
            await ctx.send(
                "❌ **No ghosts loaded!** Check your bots directory and file formats."
            )

    async def cmd_status(self, ctx, *args):
        """Show detailed status of the ghost system"""
        webhook_status = "Enabled" if self.channel_webhooks else "Limited"

        message = "🎭 **Ghost System Status**\n\n"
        message += f"**Loaded Ghosts:** {len(self.ghost_group)}\n"
        message += f"**Active Channels:** {len(self.channel_webhooks)}\n"
        message += f"**Webhooks:** {webhook_status}\n\n"

        if len(self.ghost_group) > 0:
            message += "**Ghost Models:**\n"
            model_counts = {}
            for ghost in self.ghost_group.values():
                model_counts[ghost.model] = model_counts.get(ghost.model, 0) + 1

            for model, count in model_counts.items():
                message += f"  • {model}: {count} ghost(s)\n"

            message += f"\n**Try:** `@{list(self.ghost_group.keys())[0]} hello` or `!test-ghost`"
        else:
            message += "⚠️ **No ghosts loaded!** Use `!reload-ghosts` to load them."

        await ctx.send(message)

    async def cmd_test_ghost(self, ctx, ghost_handle: str = None):
        """Test a specific ghost or the first available one"""
        if len(self.ghost_group) == 0:
            await ctx.send("❌ No ghosts loaded! Use `!reload-ghosts` first.")
            return

        # Select ghost
        if ghost_handle:
            ghost_key = ghost_handle.lower()  # Normalize to match stored handles
            ghost = self.ghost_group.get(ghost_key)
            if not ghost:
                available = ", ".join(self.ghost_group.keys())
                await ctx.send(
                    f"❌ Ghost '{ghost_handle}' not found! Available: {available}"
                )
                return
        else:
            ghost = list(self.ghost_group.values())[0]

        # Test the ghost
        test_message = (
            f"Hello {ghost.name}! This is a test to see if you're working properly."
        )

        try:
            async with ctx.typing():
                # Create a simple test conversation
                test_messages = [
                    {
                        "role": "user",
                        "content": f"{ctx.author.display_name}: {test_message}",
                    }
                ]

                response = await ghost.call_llm(test_messages, max_tokens=200)

                await ctx.send(
                    f"✅ **Test successful for {ghost.name}:**\n\n{response}"
                )

        except Exception as e:
            await ctx.send(f"❌ **Test failed for {ghost.name}:** {str(e)}")

    async def cmd_commands(self, ctx, *args):
        """List all available commands"""
        message = "👻 **Available Commands:**\n\n"

        # List all commands with their descriptions
        message += "**Ghost Interaction:**\n"
        message += "• `@ghost_name message` - Summon a specific ghost\n"
        message += "• `@bot_name message` - Summon first available ghost\n"
        message += "• Reply to any ghost's message - Automatically summon that ghost\n"
        message += "• Reply + mention other ghosts - Multiple ghosts respond\n"
        message += "• `!speak ghost1 ghost2 ...` - Make specific ghosts speak in sequence\n"
        message += "• `!ghost-chat [ghost1 ghost2 ...]` - Start a conversation between ghosts\n\n"

        message += "**Ghost-to-Ghost Features:**\n"
        message += "• Ghosts can tag each other with @ghostname\n"
        message += "• Ghosts automatically respond when tagged by other ghosts\n"
        message += "• Ghosts can reply to each other's messages\n"
        message += "• Ghosts maintain context of other ghosts' messages\n\n"

        message += "**Management Commands:**\n"
        message += "• `!list` - List all loaded ghosts\n"
        message += "• `!reload` - Reload ghost configurations\n"
        message += "• `!status` - Show system status\n"
        message += "• `!test-ghost [handle]` - Test a specific ghost\n"
        message += "• `!commands` - Show this help message\n"

        await ctx.send(message)

    async def cmd_speak(self, ctx, *ghost_handles):
        """Make specific ghosts speak in sequence"""
        logger.info(f"👻 Speaking with {ghost_handles!r}")
        if len(self.ghost_group) == 0:
            await ctx.send("❌ No ghosts loaded! Use `!reload` first.")
            return

        # filter for valid ghost handles
        handles = [handle for handle in ghost_handles if handle in self.ghost_group.keys()]
        if len(handles) != len(ghost_handles):
            await ctx.send(f"❌ Some invalid ghost handles were provided: {', '.join(ghost_handles)}")
            return

        # If no ghosts specified, use all available ghosts, randomize order
        if not handles:
            handles = list(self.ghost_group.keys())
            random.shuffle(handles)

        logger.info(f"👻 Speaking with {handles!r}")

        # Find the ghosts
        ghosts_to_speak = []
        for handle in handles:
            ghost = self.ghost_group.get(handle.lower())
            if ghost:
                ghosts_to_speak.append(ghost)
            else:
                await ctx.send(f"⚠️ Ghost '{handle}' not found, skipping...")

        if not ghosts_to_speak:
            await ctx.send("❌ No valid ghosts found to speak!")
            return

        # Make each ghost speak in turn
        for ghost in ghosts_to_speak:
            try:
                await self.activate_ghost(ghost, ctx.message)

                # Add random delay between responses (1-3 seconds)
                if ghost != ghosts_to_speak[-1]:  # Don't delay after the last ghost
                    delay = random.uniform(1.0, 3.0)
                    await asyncio.sleep(delay)

            except Exception as e:
                await ctx.send(f"❌ **Error with {ghost.name}**: {str(e)}")

    async def cmd_ghost_chat(self, ctx, *args):
        """Start a conversation between multiple ghosts"""
        logger.info(f"👻 Starting ghost chat with {args!r}")
        if len(self.ghost_group) < 2:
            await ctx.send("❌ Need at least 2 ghosts for a ghost chat! Use `!reload` to load more ghosts.")
            return

        # Parse arguments for ghost handles
        if args:
            ghost_handles = [arg.lower() for arg in args]
        else:
            # Use all available ghosts if none specified
            ghost_handles = list(self.ghost_group.keys())

        # Validate ghost handles
        valid_ghosts = []
        for handle in ghost_handles:
            ghost = self.ghost_group.get(handle)
            if ghost:
                valid_ghosts.append(ghost)
            else:
                await ctx.send(f"⚠️ Ghost '{handle}' not found, skipping...")

        if len(valid_ghosts) < 2:
            await ctx.send("❌ Need at least 2 valid ghosts for a chat!")
            return

        # Start the ghost conversation
        await ctx.send(f"🎭 Starting ghost chat with: {', '.join(ghost.name for ghost in valid_ghosts)}")
        
        # Run 10 turns of conversation
        for turn in range(10):
            # Select ghost for this turn (cycle through them)
            current_ghost = valid_ghosts[turn % len(valid_ghosts)]
            
            try:
                # Activate the ghost using the existing infrastructure
                await self.activate_ghost(current_ghost, ctx.message)
                
                # Add random delay between responses (2-10 seconds)
                if turn < 9:  # Don't delay after the last turn
                    delay = random.uniform(2.0, 10.0)
                    await asyncio.sleep(delay)

            except Exception as e:
                await ctx.send(f"❌ **Error with {current_ghost.name}**: {str(e)}")
                # Continue with next ghost even if one fails
                continue
        
        await ctx.send("🎭 Ghost chat completed!")

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            # Get list of valid commands
            valid_commands = ", ".join(f"!{cmd.name}" for cmd in self.commands)
            await ctx.send(f"❓ Unknown command. Valid commands: {valid_commands}")
            return

        # Let other errors propagate
        logger.error(f"Command error: {type(error).__name__}: {error}")
        raise error

    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name by filtering out non-letter characters, emojis, and non-printable characters.
        Keeps letters (including non-Latin), numbers, and spaces.
        
        Args:
            name: The name to normalize
            
        Returns:
            Normalized name with only letter-like characters
        """
        import re
        # Keep letters (including non-Latin), numbers, and spaces
        # Remove emojis, symbols, and other non-printable characters
        normalized = re.sub(r'[^\w\s]', '', name, flags=re.UNICODE)
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return normalized.strip()

    def identify_ghost_from_message(self, message) -> Optional[str]:
        """
        Identify which ghost sent a message by checking webhook properties
        
        Args:
            message: Discord message object
            
        Returns:
            Ghost handle if the message was sent by a ghost, None otherwise
        """
        # logger.info(f"Identifying ghost from message: {message.author!r}, {message.author.name!r}, {message.author.discriminator!r}, {message.author.avatar!r} {message.webhook_id!r}")
        # Check if this is a webhook message from a ghost
        if (hasattr(message, "webhook_id") 
            and message.webhook_id 
            and hasattr(message.author, "name") 
            and hasattr(message.author, "discriminator")
            and message.author.discriminator == "0000"):  # Webhook messages have discriminator 0000
            
            # Normalize the message author name
            author_name_normalized = self._normalize_name(message.author.name)
            
            # Find the ghost by name
            for ghost_handle, ghost in self.ghost_group:
                # Normalize the ghost name for comparison
                ghost_name_normalized = self._normalize_name(ghost.name)
                # print(f"Ghost: {ghost.name!r} -> {ghost_name_normalized!r}, {ghost.handle!r}, {ghost.discord_avatar!r} matching {message.author.name!r} -> {author_name_normalized!r}")
                if ghost_name_normalized == author_name_normalized:
                    return ghost_handle
                    
        return None

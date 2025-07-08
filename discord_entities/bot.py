import asyncio
import logging
import random
import time
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from .entity_group import EntityGroup
from .utils import shorten_str

# Set up logging for this module
logger = logging.getLogger(__name__)


class Channel:
    """Simple channel state tracking"""
    def __init__(self):
        self.last_stop_time = 0  # Unix timestamp when !stop was last called
        self.chat_participants = []  # List of entity handles currently in an active chat

    def is_stopped(self) -> bool:
        """Check if channel is currently stopped (within 30 seconds of last stop)"""
        return time.time() - self.last_stop_time < 30

    def stop(self):
        """Mark channel as stopped"""
        self.last_stop_time = time.time()
        self.chat_participants.clear()  # Clear chat participants when stopped

    def add_chat_participant(self, handle: str):
        """Add a entity handle to the chat participants list"""
        if handle not in self.chat_participants:
            self.chat_participants.append(handle)

    def remove_chat_participant(self, handle: str):
        """Remove a entity handle from the chat participants list"""
        if handle in self.chat_participants:
            self.chat_participants.remove(handle)

    def clear_chat_participants(self):
        """Clear all chat participants"""
        self.chat_participants.clear()

    def is_in_chat(self, handle: str) -> bool:
        """Check if a entity handle is currently participating in a chat"""
        return handle in self.chat_participants


class EntityBot(commands.Bot):
    """Discord bot for managing and interacting with entities"""

    def __init__(self, message_limit: int = 50, entity_path: str = None):
        """
        Initialize the entity bot

        Args:
            message_limit: Number of messages to include in context
            entity_path: Path to directory containing entity configs. If None, uses the default path.
        """
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

        self.entity_group = EntityGroup()
        self.channel_webhooks: Dict[int, discord.Webhook] = {}
        self.channels: Dict[int, Channel] = {}  # channel_id -> Channel
        self.message_limit = message_limit
        self.entity_path = entity_path
        assert self.entity_path is not None, "entity_path must be provided"

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
        self.add_command(commands.Command(self.cmd_commands, name="commands"))
        self.add_command(commands.Command(self.cmd_stop, name="stop"))
        async def speak(ctx, *args):
            return await self.cmd_speak(ctx, *args)
        self.add_command(commands.Command(speak, name="speak", rest_is_raw=True))
        async def entity_chat(ctx, *args):
            return await self.cmd_entity_chat(ctx, *args)
        self.add_command(commands.Command(entity_chat, name="chat"))

        # Add error handler for unknown commands
        self.add_listener(self.on_command_error, "on_command_error")

    def get_channel_state(self, channel_id: int) -> Channel:
        """Get or create channel state"""
        if channel_id not in self.channels:
            self.channels[channel_id] = Channel()
        return self.channels[channel_id]

    def is_direct_user_mention(self, message) -> bool:
        """Check if this is a direct mention of the bot by a user (not a entity)"""
        return (
            self.user.mentioned_in(message) and 
            not message.author.bot and
            not (hasattr(message, "webhook_id") and message.webhook_id)
        )

    def set_message_limit(self, limit: int):
        """Set the message limit for all entities"""
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
            if wh.name == "Entity Bot":
                webhook = wh
                break

        # Create webhook if it doesn't exist
        if not webhook:
            try:
                webhook = await channel.create_webhook(name="Entity Bot")
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

        # Load entities from configured directory
        logger.info(f"📁 Looking for entity configs in: {self.entity_path}")
        try:
            self.entity_group = EntityGroup.load_from_directory(self.entity_path)
        except ValueError as e:
            # Check if this is the specific "no bots available" error
            if "No entity config files found" in str(e) or "No entities were successfully loaded" in str(e):
                logger.warning(f"⚠️  No entity config files found in {self.entity_path}")
                logger.warning("⚠️  Please add entity configuration files to the entity_definitions directory")
                # Initialize an empty entity group so the bot can still function
                self.entity_group = EntityGroup()
            else:
                # Re-raise other ValueError exceptions
                raise

        if len(self.entity_group) > 0:
            logger.info(f"🎭 Entity system ready with {len(self.entity_group)} entities:")
            for entity_key, entity in self.entity_group:
                logger.info(
                    f"  {entity.name} (handle: {entity.handle}) using {entity.model}"
                )
        else:
            logger.warning("⚠️  No entities loaded! Check your bots directory.")

        logger.info("🚀 Bot is ready to receive entity summons!")

    async def activate_entity(
        self,
        entity,
        message: Optional[discord.Message] = None,
    ):
        """
        Activate an entity to speak, optionally in response to a message

        Args:
            entity: The entity to activate
            message: Optional message to reply to
        """
        start_time = asyncio.get_event_loop().time()
        channel = message.channel if message else None

        try:
            logger.info(f"🎬 {entity.name} starting response generation")

            # Show typing indicator if we have a channel
            if channel:
                async with channel.typing():
                    # Get recent messages for context
                    logger.debug(
                        f"📚 {entity.name} gathering message history from #{channel.name} (limit: {self.message_limit})"
                    )
                    recent_messages = await self.get_recent_messages(channel)

                    # Format messages for LLM
                    llm_messages = entity.format_discord_messages_for_llm(
                        recent_messages, message_limit=self.message_limit, entity_group=self.entity_group
                    )
                    logger.debug(
                        f"💬 {entity.name} formatted {len(llm_messages)} messages for context"
                    )

                    # Generate response using the entity's LLM
                    response = await entity.call_llm(llm_messages, max_tokens=400)

                    # Try to send via webhook for better appearance
                    webhook = await self.get_or_create_webhook(channel)

                    if webhook:
                        try:
                            logger.debug(
                                f"📤 {entity.name} sending response via webhook"
                            )

                            # Prepare webhook kwargs
                            webhook_kwargs = {
                                "content": shorten_str(response),
                                "username": entity.name,
                            }

                            # Add avatar if specified
                            if entity.discord_avatar:
                                webhook_kwargs["avatar_url"] = str(entity.discord_avatar)

                            await webhook.send(**webhook_kwargs)

                            elapsed = asyncio.get_event_loop().time() - start_time
                            logger.info(
                                f"✅ {entity.name} response sent via webhook in {elapsed:.2f}s"
                            )
                            return
                        except Exception as e:
                            logger.error(
                                f"❌ {entity.name} webhook error: {type(e).__name__}: {e}"
                            )
                            logger.debug(
                                f"🔍 Webhook error details for {entity.name}",
                                exc_info=True,
                            )

                    # Fallback to regular reply
                    logger.debug(f"🔄 {entity.name} falling back to regular reply")
                    if message:
                        await message.reply(f"**{entity.name}**: {shorten_str(response)}")
                    else:
                        await channel.send(f"**{entity.name}**: {shorten_str(response)}")

                    elapsed = asyncio.get_event_loop().time() - start_time
                    logger.info(
                        f"✅ {entity.name} response sent via fallback in {elapsed:.2f}s"
                    )

        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.error(
                f"❌ {entity.name} response generation failed after {elapsed:.2f}s: {type(e).__name__}: {e}"
            )
            logger.debug(
                f"🔍 Entity response error details for {entity.name}", exc_info=True
            )

            error_msg = f"*{entity.name} flickers and fades* Something went wrong in the spirit realm... ({str(e)[:100]})"
            try:
                if message:
                    await message.reply(shorten_str(error_msg))
                elif channel:
                    await channel.send(shorten_str(error_msg))
                logger.warning(f"🔄 {entity.name} sent error message to user")
            except Exception as reply_error:
                logger.error(
                    f"❌ {entity.name} failed to send error message: {reply_error}"
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

        # Don't respond to regular bot messages (but allow webhook messages from entities)
        if message.author.bot and not (hasattr(message, "webhook_id") and message.webhook_id):
            return

        # Process commands first (but only for non-entity messages)
        if message.content.startswith(self.command_prefix):
            # Only process commands from non-entity messages
            if not (hasattr(message, "webhook_id") and message.webhook_id):
                await self.process_commands(message)
            return

        # Handle mentions and pseudo-mentions
        mentioned_entities = []
        is_direct_mention = False

        # Check for direct bot mention
        if self.user.mentioned_in(message):
            is_direct_mention = True
            logger.debug(
                f"🔔 Direct bot mention from {message.author.display_name} in #{message.channel.name}"
            )
            # Look for specific entities in the message
            mentioned_entities = self.entity_group.find_entity_by_mention(message.content)
            if mentioned_entities:
                logger.debug(
                    f"🎯 Specific entities requested: {', '.join(entity.name for entity in mentioned_entities)}"
                )

        # Check for pseudo-mentions like "@tomas", "@anna"
        mentioned_entities = self.entity_group.find_entity_by_mention(message.content)
        if mentioned_entities:
            logger.debug(
                f"Pseudo-mentions detected for: {', '.join(entity.name for entity in mentioned_entities)} from {message.author.display_name}"
            )

        # Check for replies to entity messages
        if message.reference:
            try:
                # Fetch the referenced message
                referenced_message = await message.channel.fetch_message(message.reference.message_id)
                
                # Check if the referenced message was sent by an entity
                entity_handle = self.identify_entity_from_message(referenced_message)
                # logger.info(f" Referenced message: {referenced_message.content} from {referenced_message.author.display_name!r}, entity handle: {entity_handle!r}")
                if entity_handle:
                    entity = self.entity_group.get(entity_handle)
                    if entity:
                        # Add the replied-to entity to the list if not already present
                        if entity not in mentioned_entities:
                            mentioned_entities.insert(0, entity)
                            logger.debug(
                                f"💬 Reply detected to {entity.name}'s message from {message.author.display_name}"
                            )
                        else:
                            logger.debug(
                                f"💬 Reply to {entity.name}'s message, but {entity.name} already mentioned in message"
                            )
            except Exception as e:
                logger.debug(f"Could not fetch referenced message: {e}")

        # NEW: Check if this message is from an entity and contains mentions of other entities
        if (hasattr(message, "webhook_id") and message.webhook_id and 
            hasattr(message.author, "discriminator") and message.author.discriminator == "0000"):
            
            # This is an entity message - check if it mentions other entities
            entity_mentions = self.entity_group.find_entity_by_mention(message.content)
            if entity_mentions:
                logger.debug(
                    f"Entity {message.author.name} is mentioning other entities: {', '.join(entity.name for entity in entity_mentions)}"
                )
                # Add mentioned entities to the response list
                for entity in entity_mentions:
                    if entity not in mentioned_entities:
                        mentioned_entities.append(entity)

        # Check if channel is stopped before processing any entity mentions
        channel_state = self.get_channel_state(message.channel.id)
        if mentioned_entities or is_direct_mention:
            # Only block if channel is stopped AND this is not a direct user mention
            if channel_state.is_stopped():
                logger.info(f"Entity mentions blocked in #{message.channel.name} (channel stopped)")
                await message.channel.send(shorten_str(f"**Dropping entity mentions ({', '.join(entity.name for entity in mentioned_entities)}) because entity activity is currently stopped in this channel**"))
                return
            
            # Filter out entitys that are currently in a chat (unless it's a direct user mention)
            if not self.is_direct_user_mention(message):
                filtered_entitys = []
                for entity in mentioned_entities:
                    if channel_state.is_in_chat(entity.handle):
                        logger.info(f"🛑 Entity {entity.handle} blocked from mention (currently in chat)")
                    else:
                        filtered_entitys.append(entity)
                mentioned_entities = filtered_entitys
            
            # If no specific entities selected and it's a direct mention, a random entity is summoned
            if not mentioned_entities and is_direct_mention and len(self.entity_group) > 0:
                # For direct mentions, still allow entitys in chat to respond
                mentioned_entities = [random.choice(list(self.entity_group.values()))]
                logger.debug(
                    f"🎲 No specific entities requested, using random: {mentioned_entities[0].name}"
                )

            if mentioned_entities:
                # Remove duplicates while preserving order
                unique_entitys = []
                seen_entitys = set()
                for entity in mentioned_entities:
                    if entity.handle not in seen_entitys:
                        unique_entitys.append(entity)
                        seen_entitys.add(entity.handle)
                
                logger.info(
                    f"Summoning {len(unique_entitys)} entity(ies) for {message.author.display_name} in #{message.channel.name}: {', '.join(entity.name for entity in unique_entitys)}"
                )
                
                for entity in unique_entitys:
                    await self.activate_entity(entity, message)
            else:
                logger.warning(
                    f"⚠️  Entity summon failed - no entities available for {message.author.display_name}"
                )

    async def cmd_list(self, ctx, *args):
        """List all loaded entities"""
        if len(self.entity_group) == 0:
            await ctx.send(
                "No entities are currently loaded! Check the bots directory."
            )
            return

        message = "**Loaded Entities:**\n\n"

        for entity_key, entity in self.entity_group:
            message += f"**{entity.name}** (`{entity.handle}`) - {shorten_str(entity.description, 50)}\n"

        await ctx.send(shorten_str(message))

    async def cmd_reload(self, ctx, *args):
        """Reload entity configurations from files"""
        old_count = len(self.entity_group)

        self.entity_group = EntityGroup.load_from_directory(self.entity_path)
        new_count = len(self.entity_group)

        if new_count > 0:
            await ctx.send(
                shorten_str(f"🔄 **Reloaded {new_count} entities** (was {old_count})\n\nUse `!list` to see the updated list.")
            )
        else:
            await ctx.send(
                shorten_str("❌ **No entities loaded!** Check your bots directory and file formats.")
            )

    async def cmd_status(self, ctx, *args):
        """Show detailed status of the entity system"""
        webhook_status = "Enabled" if self.channel_webhooks else "Limited"

        message = "🎭 **Entity System Status**\n\n"
        message += f"**Loaded Entities:** {len(self.entity_group)}\n"
        message += f"**Active Channels:** {len(self.channel_webhooks)}\n"
        message += f"**Webhooks:** {webhook_status}\n\n"

        # Show channel stop status
        channel_state = self.get_channel_state(ctx.channel.id)
        if channel_state.is_stopped():
            remaining_time = 30 - (time.time() - channel_state.last_stop_time)
            message += f"🛑 **This Channel:** Stopped ({remaining_time:.1f}s remaining)\n\n"
        else:
            message += "▶️ **This Channel:** Active\n\n"
        
        # Show chat participants if any
        if channel_state.chat_participants:
            message += f"🎭 **Active Chat:** {', '.join(channel_state.chat_participants)}\n\n"

        if len(self.entity_group) > 0:
            message += "**Entity Models:**\n"
            model_counts = {}
            for entity in self.entity_group.values():
                model_counts[entity.model] = model_counts.get(entity.model, 0) + 1

            for model, count in model_counts.items():
                message += f"  • {model}: {count} entity(ies)\n"

            # Show entity-specific configurations
            custom_config_entitys = []
            for entity in self.entity_group.values():
                if entity.base_url or entity.api_key:
                    custom_config_entitys.append(entity)
            
            if custom_config_entitys:
                message += "\n**Entities with Custom LLM Config:**\n"
                for entity in custom_config_entitys:
                    config_info = []
                    if entity.base_url:
                        config_info.append(f"URL: {entity.base_url}")
                    if entity.api_key:
                        config_info.append("Custom API Key")
                    message += f"  • {entity.name}: {', '.join(config_info)}\n"
            else:
                message += "\n**LLM Configuration:** All entities using .env settings\n"

            message += f"\n**Try:** `@{list(self.entity_group.keys())[0]} hello there!`"
        else:
            message += "⚠️ **No entities loaded!** Use `!reload-entitys` to load them."

        await ctx.send(shorten_str(message))

    async def cmd_commands(self, ctx, *args):
        """List all available commands"""
        message = "**Available Commands:**\n\n"

        # List all commands with their descriptions
        message += "**Entity Interaction:**\n"
        message += "• `@entity_name message` - Summon a specific entity\n"
        message += "• `@bot_name message` - Summon first available entity\n"
        message += "• Reply to any entity's message - Automatically summon that entity\n"
        message += "• Reply + mention other entities - Multiple entities respond\n"
        message += "• `!speak entity1 entity2 ...` - Make specific entities speak in sequence\n"
        message += "• `!chat [entity1 entity2 ...] [number]` - Start a conversation between entities (optional: specify number of turns)\n\n"

        message += "**Entity-to-Entity Features:**\n"
        message += "• Entities can tag each other with @entityname\n"
        message += "• Entities automatically respond when tagged by other entities\n"
        message += "• Entities can reply to each other's messages\n"
        message += "• Entities maintain context of other entities' messages\n\n"

        message += "**Management Commands:**\n"
        message += "• `!list` - List all loaded entities\n"
        message += "• `!reload` - Reload entity configurations\n"
        message += "• `!status` - Show system status\n"
        message += "• `!stop` - Stop all entity activity in this channel for 30 seconds\n"
        message += "• `!commands` - Show this help message\n"

        await ctx.send(shorten_str(message))

    async def cmd_speak(self, ctx, *entity_handles):
        """Make specific entities speak in sequence"""
        logger.info(f"Speaking with {entity_handles!r}")
        if len(self.entity_group) == 0:
            await ctx.send(shorten_str("❌ No entities loaded! Use `!reload` first."))
            return

        # filter for valid entity handles
        handles = [handle for handle in entity_handles if handle in self.entity_group.keys()]
        if len(handles) != len(entity_handles):
            await ctx.send(shorten_str(f"❌ Some invalid entity handles were provided: {', '.join(entity_handles)}"))
            return

        # If no entities specified, use all available entities, randomize order
        if not handles:
            handles = list(self.entity_group.keys())
            random.shuffle(handles)

        logger.info(f"Speaking with {handles!r}")

        # Find the entities
        entitys_to_speak = []
        for handle in handles:
            entity = self.entity_group.get(handle.lower())
            if entity:
                entitys_to_speak.append(entity)
            else:
                await ctx.send(shorten_str(f"⚠️ Entity '{handle}' not found, skipping..."))

        if not entitys_to_speak:
            await ctx.send(shorten_str("❌ No valid entities found to speak!"))
            return

        # Make each entity speak in turn
        channel_state = self.get_channel_state(ctx.channel.id)
        for entity in entitys_to_speak:
            # Check if channel is still stopped before each entity speaks
            if channel_state.is_stopped():
                await ctx.send(shorten_str("🛑 **Entity activity was stopped during !speak command.**"))
                return
                
            try:
                await self.activate_entity(entity, ctx.message)

                # Add random delay between responses (1-3 seconds)
                if entity != entitys_to_speak[-1]:  # Don't delay after the last entity
                    delay = random.uniform(1.0, 3.0)
                    await asyncio.sleep(delay)

            except Exception as e:
                await ctx.send(shorten_str(f"❌ **Error with {entity.name}**: {str(e)}"))

    async def cmd_entity_chat(self, ctx, *args):
        """Start a conversation between multiple entities"""
        logger.info(f"Starting entity chat with {args!r}")
        if len(self.entity_group) < 2:
            await ctx.send(shorten_str("❌ Need at least 2 entities for an entity chat! Use `!reload` to load more entities."))
            return

        # Parse arguments - look for numerical argument for turns
        num_turns = 10  # Default number of turns
        entity_handles = []
        found_number = False  # Track if we've already found a number
        
        for arg in args:
            # Check if argument is a number (only use the first one found)
            if not found_number:
                try:
                    potential_turns = int(arg)
                    if potential_turns > 0:
                        num_turns = potential_turns
                        found_number = True
                        logger.info(f"Setting conversation turns to {num_turns}")
                        continue  # Skip adding this as an entity name
                    else:
                        # Not a valid turn count, treat as entity name
                        entity_handles.append(arg.lower())
                except ValueError:
                    # Not a number, treat as entity name
                    entity_handles.append(arg.lower())
            else:
                # Already found a number, treat everything else as entity names
                entity_handles.append(arg.lower())

        # If no entities specified, use all available entities
        if not entity_handles:
            entity_handles = list(self.entity_group.keys())

        # Validate entity handles
        valid_entitys = []
        for handle in entity_handles:
            entity = self.entity_group.get(handle)
            if entity:
                valid_entitys.append(entity)
            else:
                await ctx.send(shorten_str(f"⚠️ Entity '{handle}' not found, skipping..."))

        if len(valid_entitys) < 2:
            await ctx.send(shorten_str("❌ Need at least 2 valid entities for a chat!"))
            return

        # Start the entity conversation
        await ctx.send(shorten_str(f"🎭 Starting entity chat with: {', '.join(entity.name for entity in valid_entitys)} ({num_turns} turns)"))
        
        # Add all participants to the chat list
        channel_state = self.get_channel_state(ctx.channel.id)
        for entity in valid_entitys:
            channel_state.add_chat_participant(entity.handle)
        
        # Create a queue of speakers and randomize the initial order
        speaker_queue = valid_entitys.copy()
        random.shuffle(speaker_queue)
        
        try:
            # Run the specified number of turns
            for turn in range(num_turns):
                # Check if channel is still stopped before each turn
                if channel_state.is_stopped():
                    await ctx.send(shorten_str("🛑 **Entity activity was stopped during !chat command.**"))
                    return
                
                # Select speaker from the first half of the queue
                queue_size = len(speaker_queue)
                if queue_size > 1:
                    # Select from first half of the queue
                    half_size = max(1, (queue_size + 1) // 2)
                    selected_index = random.randint(0, half_size - 1)
                else:
                    selected_index = 0
                
                current_entity = speaker_queue[selected_index]
                logger.info(f"Chat turn {turn} of {num_turns}: queue={[s.handle for s in speaker_queue]}, selected={selected_index} ({current_entity.handle})")
                
                # Move the selected speaker to the back of the queue
                speaker_queue.pop(selected_index)
                speaker_queue.append(current_entity)
                
                try:
                    # Activate the entity using the existing infrastructure
                    await self.activate_entity(current_entity, ctx.message)
                    
                    # Add random delay between responses (2-10 seconds)
                    if turn < num_turns - 1:  # Don't delay after the last turn
                        delay = random.uniform(2.0, 10.0)
                        await asyncio.sleep(delay)

                except Exception as e:
                    await ctx.send(shorten_str(f"❌ **Error with {current_entity.name}**: {str(e)}"))
                    # Continue with next entity even if one fails
                    continue
            
            await ctx.send(shorten_str("🎭 Entity chat completed!"))
            
        finally:
            # Always clear chat participants when done (whether completed or stopped)
            channel_state.clear_chat_participants()

    async def cmd_stop(self, ctx, *args):
        """Stop all entity activity in this channel for 30 seconds"""
        channel_state = self.get_channel_state(ctx.channel.id)
        channel_state.stop()
        await ctx.send(shorten_str("**Entity activity stopped in this channel for 30 seconds!**"))

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            # Get list of valid commands
            valid_commands = ", ".join(f"!{cmd.name}" for cmd in self.commands)
            await ctx.send(shorten_str(f"❓ Unknown command. Valid commands: {valid_commands}"))
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

    def identify_entity_from_message(self, message) -> Optional[str]:
        """
        Identify which entity sent a message by checking webhook properties
        
        Args:
            message: Discord message object
            
        Returns:
            Entity handle if the message was sent by an entity, None otherwise
        """
        # logger.info(f"Identifying entity from message: {message.author!r}, {message.author.name!r}, {message.author.discriminator!r}, {message.author.avatar!r} {message.webhook_id!r}")
        # Check if this is a webhook message from an entity
        if (hasattr(message, "webhook_id") 
            and message.webhook_id 
            and hasattr(message.author, "name") 
            and hasattr(message.author, "discriminator")
            and message.author.discriminator == "0000"):  # Webhook messages have discriminator 0000
            
            # Normalize the message author name
            author_name_normalized = self._normalize_name(message.author.name)
            
            # Find the entity by name
            for entity_handle, entity in self.entity_group:
                # Normalize the entity name for comparison
                entity_name_normalized = self._normalize_name(entity.name)
                # print(f"Entity: {entity.name!r} -> {entity_name_normalized!r}, {entity.handle!r}, {entity.discord_avatar!r} matching {message.author.name!r} -> {author_name_normalized!r}")
                if entity_name_normalized == author_name_normalized:
                    return entity_handle
                    
        return None

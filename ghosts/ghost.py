import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
from litellm import acompletion
import litellm

# Set up logging for this module
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """

"""


class Ghost(BaseModel):
    """A digital entity with LLM capabilities"""

    name: str = Field(..., description="Display name of the entity")
    handle: str = Field(
        ..., description="Handle/username for mentions and identification"
    )
    discord_avatar: Optional[HttpUrl] = Field(
        default=None, description="Avatar URL for webhook display (None uses default)"
    )
    description: str = Field(..., description="Brief description of the entity")
    instructions: str = Field(
        ..., description="System prompt/personality instructions for the LLM"
    )
    model: str = Field(default="gpt-4.1-mini", description="LLM model to use")
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="LLM temperature parameter (None uses model default)",
    )
    # New fields for entity-specific LLM configuration
    base_url: Optional[str] = Field(
        default=None,
        description="Custom API URL for this entity's LLM client (overrides .env configuration)",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Custom API key for this entity's LLM client (overrides .env configuration)",
    )

    class Config:
        # Allow extra fields for future extensibility
        extra = "forbid"

    @field_validator("name")
    @classmethod
    def name_must_be_clean(cls, v):
        """Ensure name is clean for display"""
        return v.strip()

    @field_validator("handle")
    @classmethod
    def handle_must_be_clean(cls, v):
        """Ensure handle is clean for use as identifier"""
        return v.strip().lower()

    @field_validator("temperature")
    @classmethod
    def temperature_reasonable_range(cls, v):
        """Ensure temperature is in a reasonable range"""
        if v is not None and (v < 0 or v > 2):
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v):
        """Validate API URL format"""
        if v is not None:
            v = v.strip()
            if not v.startswith(("http://", "https://")):
                raise ValueError("API URL must start with http:// or https://")
        return v

    async def call_llm(
        self, messages: List[Dict[str, str]], max_tokens: int = 300
    ) -> str:
        """
        Call the LLM with the given messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text
        """
        # litellm._turn_on_debug()

        logger.info(
            f"🧠 {self.name} calling LLM {self.model} with {len(messages)} messages, max_tokens={max_tokens}"
        )

        try:
            # Prepare the full message list with system prompt
            full_messages = [
                {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{self.instructions}"}
            ] + messages

            logger.debug(
                f"💭 {self.name} LLM input: {len(full_messages)} total messages, temp={self.temperature}"
            )

            # Prepare completion kwargs
            completion_kwargs = {
                "model": self.model,
                "messages": full_messages,
                "max_tokens": max_tokens,
                "timeout": 30,  # 30 second timeout
            }

            # Only include temperature if it's explicitly set
            if self.temperature is not None:
                completion_kwargs["temperature"] = self.temperature

            # Add entity-specific API configuration if provided
            if self.base_url:
                completion_kwargs["api_base"] = self.base_url
                assert self.model, "Model must be specified when using a custom API URL"
                # litellm expects the model to be in the format "openai/<model>" for a custom API URL
                completion_kwargs["model"] = "openai/" + self.model
                logger.debug(f"🔗 {self.name} using custom API URL: {self.base_url}")

            if self.api_key:
                completion_kwargs["api_key"] = self.api_key
                logger.debug(f"🔑 {self.name} using custom API key")

            # Call litellm async
            response = await acompletion(**completion_kwargs)

            response_text = response.choices[0].message.content.strip()
            logger.info(
                f"✅ {self.name} LLM response received: {len(response_text)} characters"
            )
            logger.debug(f"📝 {self.name} response preview: {response_text[:100]}...")

            return response_text

        except Exception as e:
            # Log the error with full details
            logger.error(
                f"❌ {self.name} LLM call failed: {type(e).__name__}: {str(e)}"
            )
            logger.debug(f"🔍 {self.name} LLM error details", exc_info=True)

            # Fallback response if LLM fails
            fallback_msg = f"*{self.name} flickers mysteriously* Sorry, I'm having trouble connecting to the spirit realm right now... ({str(e)[:50]})"
            logger.warning(f"🔄 {self.name} using fallback response")
            return fallback_msg

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
        normalized = re.sub(r"[^\w\s]", "", name, flags=re.UNICODE)
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def format_discord_messages_for_llm(
        self, discord_messages: List[Any], message_limit: int = 50, ghost_group=None
    ) -> List[Dict[str, str]]:
        """
        Convert Discord message objects to LLM format

        Args:
            discord_messages: List of Discord message objects
            message_limit: Maximum number of messages to include
            ghost_group: Optional GhostGroup to look up ghost handles

        Returns:
            List of formatted messages for LLM
        """
        formatted_messages = []

        for msg in discord_messages:
            # Skip empty messages
            if not msg.content.strip():
                continue

            # Skip !commands (system commands)
            if msg.content.strip().startswith("!"):
                logger.debug(
                    f"🚫 {self.name} skipping command message: {msg.content[:50]}..."
                )
                continue

            # Check if this message is from the current entity (via webhook)
            is_current_ghost = (
                hasattr(msg, "webhook_id")
                and msg.webhook_id
                and hasattr(msg.author, "name")
                and self._normalize_name(msg.author.name)
                == self._normalize_name(self.name)
            )

            # Check if this message is from another entity (webhook with different name)
            is_other_ghost = (
                hasattr(msg, "webhook_id")
                and msg.webhook_id
                and hasattr(msg.author, "name")
                and self._normalize_name(msg.author.name)
                != self._normalize_name(self.name)
                and hasattr(msg.author, "discriminator")
                and msg.author.discriminator
                == "0000"  # Webhook messages have discriminator 0000
            )

            # Check if this is a regular bot message (not webhook) - these are typically command responses
            is_regular_bot = msg.author.bot and not getattr(msg, "webhook_id", None)

            if is_current_ghost:
                # This entity's own previous messages -> assistant role, no prefix
                formatted_msg = {"role": "assistant", "content": msg.content}
                formatted_messages.append(formatted_msg)
                logger.debug(f"💬 {self.name} found own message: {msg.content[:50]}...")

            elif is_other_ghost:
                # Another entity's message -> user role with entity name
                ghost_name = msg.author.name

                # Try to find the ghost and get its handle
                ghost_handle = None
                if ghost_group:
                    # Look up the ghost by name
                    for handle, ghost in ghost_group:
                        if self._normalize_name(ghost.name) == self._normalize_name(
                            ghost_name
                        ):
                            ghost_handle = handle
                            break

                content = (
                    f"{ghost_name}: {msg.content}"
                    if not ghost_handle
                    else f"{ghost_name} (@{ghost_handle}): {msg.content}"
                )
                formatted_msg = {
                    "role": "user",
                    "content": content,
                }
                formatted_messages.append(formatted_msg)

                if ghost_handle:
                    logger.debug(
                        f"{self.name} found other entity message from {ghost_name} (@{ghost_handle})"
                    )
                else:
                    logger.debug(
                        f"{self.name} found other entity message from {ghost_name}"
                    )

            elif is_regular_bot:
                # Skip regular bot messages (command responses, etc.)
                logger.debug(
                    f"🚫 {self.name} skipping bot command response from {msg.author.display_name}"
                )
                continue

            else:
                # Regular user message -> user role with username
                formatted_msg = {
                    "role": "user",
                    "content": f"{msg.author.display_name}: {msg.content}",
                }
                formatted_messages.append(formatted_msg)

        # Limit to configured context length
        limited_messages = formatted_messages[
            -message_limit:
        ]  # Last N messages based on app config
        logger.debug(
            f"📝 {self.name} formatted {len(limited_messages)}/{len(formatted_messages)} messages for LLM context (limit: {message_limit})"
        )
        return limited_messages

    def __str__(self) -> str:
        return f"Entity(@{self.handle}, {self.name}, model={self.model})"

    @classmethod
    def load_from_file(cls, file_path: Path) -> "Ghost":
        """
        Load a single entity from a file

        Args:
            file_path: Path to the entity configuration file

        Returns:
            Ghost instance

        Raises:
            ValueError: If the file cannot be loaded or parsed
        """
        try:
            logger.debug(f"📖 Reading entity file: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() == ".json":
                    data = json.load(f)
                    logger.debug(f"🔧 Parsed JSON data from {file_path}")
                elif file_path.suffix.lower() in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                    logger.debug(f"🔧 Parsed YAML data from {file_path}")
                else:
                    raise ValueError(f"Unsupported file type: {file_path.suffix}")

            # Validate and create Ghost instance
            ghost = cls(**data)
            logger.debug(f"✅ Created entity instance: {ghost.name}")
            return ghost

        except Exception as e:
            error_msg = (
                f"Error loading entity from {file_path}: {type(e).__name__}: {e}"
            )
            logger.error(f"❌ {error_msg}")
            logger.debug(
                f"🔍 File loading error details for {file_path}", exc_info=True
            )
            raise ValueError(error_msg) from e

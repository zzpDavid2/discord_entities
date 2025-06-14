import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
import litellm
from litellm import acompletion
import os

# Set up logging for this module
logger = logging.getLogger(__name__)

class Ghost(BaseModel):
    """A digital ghost with LLM capabilities"""
    
    name: str = Field(..., description="Display name of the ghost")
    discord_handle: str = Field(..., description="Handle used to summon this ghost (e.g., 'tomas')")
    discord_avatar: HttpUrl = Field(..., description="Avatar URL for webhook display")
    discord_username: str = Field(..., description="Username displayed in Discord")
    description: str = Field(..., description="Brief description of the ghost")
    instructions: str = Field(..., description="System prompt/personality instructions for the LLM")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature parameter")
    
    class Config:
        # Allow extra fields for future extensibility
        extra = "allow"
    
    @field_validator('discord_handle')
    @classmethod
    def handle_must_be_lowercase(cls, v):
        """Ensure handle is lowercase for consistent matching"""
        return v.lower().strip()
    
    @field_validator('temperature')
    @classmethod
    def temperature_reasonable_range(cls, v):
        """Ensure temperature is in a reasonable range"""
        if v < 0 or v > 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    def get_aliases(self) -> List[str]:
        """Get all possible aliases for this ghost"""
        aliases = [self.discord_handle]
        
        # Add variations of the name
        name_lower = self.name.lower()
        if 'ghost' in name_lower:
            base_name = name_lower.replace('ghost', '').replace("'s", "").strip()
            if base_name:
                aliases.append(base_name)
        
        return list(set(aliases))  # Remove duplicates
    
    async def call_llm(self, messages: List[Dict[str, str]], max_tokens: int = 300) -> str:
        """
        Call the LLM with the given messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        logger.info(f"🧠 {self.name} calling LLM {self.model} with {len(messages)} messages, max_tokens={max_tokens}")
        
        try:
            # Prepare the full message list with system prompt
            full_messages = [
                {"role": "system", "content": self.instructions}
            ] + messages
            
            logger.debug(f"💭 {self.name} LLM input: {len(full_messages)} total messages, temp={self.temperature}")
            
            # Call litellm async
            response = await acompletion(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                timeout=30  # 30 second timeout
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"✅ {self.name} LLM response received: {len(response_text)} characters")
            logger.debug(f"📝 {self.name} response preview: {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            # Log the error with full details
            logger.error(f"❌ {self.name} LLM call failed: {type(e).__name__}: {str(e)}")
            logger.debug(f"🔍 {self.name} LLM error details", exc_info=True)
            
            # Fallback response if LLM fails
            fallback_msg = f"*{self.name} flickers mysteriously* Sorry, I'm having trouble connecting to the spirit realm right now... ({str(e)[:50]})"
            logger.warning(f"🔄 {self.name} using fallback response")
            return fallback_msg
    
    def format_discord_messages_for_llm(self, discord_messages: List[Any], message_limit: int = 50) -> List[Dict[str, str]]:
        """
        Convert Discord message objects to LLM format
        
        Args:
            discord_messages: List of Discord message objects
            
        Returns:
            List of formatted messages for LLM
        """
        formatted_messages = []
        
        for msg in discord_messages:
            # Skip empty messages
            if not msg.content.strip():
                continue
            
            # Check if this message is from the current ghost (via webhook)
            is_current_ghost = (
                hasattr(msg, 'webhook_id') and msg.webhook_id and 
                hasattr(msg.author, 'name') and msg.author.name == self.discord_username
            )
            
            # Check if this message is from another ghost (webhook with different name)
            is_other_ghost = (
                hasattr(msg, 'webhook_id') and msg.webhook_id and 
                hasattr(msg.author, 'name') and msg.author.name != self.discord_username and
                msg.author.name.endswith('*')  # Our ghosts end with *
            )
            
            # Check if this is a regular bot message (not webhook)
            is_regular_bot = msg.author.bot and not hasattr(msg, 'webhook_id')
            
            if is_current_ghost:
                # This ghost's own previous messages -> assistant role, no prefix
                formatted_msg = {
                    "role": "assistant",
                    "content": msg.content
                }
                formatted_messages.append(formatted_msg)
                logger.debug(f"💬 {self.name} found own message: {msg.content[:50]}...")
                
            elif is_other_ghost:
                # Another ghost's message -> user role with ghost name
                ghost_name = msg.author.name
                formatted_msg = {
                    "role": "user", 
                    "content": f"{ghost_name}: {msg.content}"
                }
                formatted_messages.append(formatted_msg)
                logger.debug(f"👻 {self.name} found other ghost message from {ghost_name}")
                
            elif is_regular_bot:
                # Skip regular bot messages (not from ghosts)
                logger.debug(f"🤖 {self.name} skipping regular bot message from {msg.author.display_name}")
                continue
                
            else:
                # Regular user message -> user role with username
                formatted_msg = {
                    "role": "user",
                    "content": f"{msg.author.display_name}: {msg.content}"
                }
                formatted_messages.append(formatted_msg)
        
        # Limit to configured context length
        limited_messages = formatted_messages[-message_limit:]  # Last N messages based on app config
        logger.debug(f"📝 {self.name} formatted {len(limited_messages)}/{len(formatted_messages)} messages for LLM context (limit: {message_limit})")
        return limited_messages
    
    def __str__(self) -> str:
        return f"Ghost({self.name}, handle='{self.discord_handle}', model={self.model})"


def load_ghosts_from_directory(directory: str) -> Dict[str, Ghost]:
    """
    Load all ghost configurations from a directory
    
    Args:
        directory: Path to directory containing ghost config files
        
    Returns:
        Dictionary mapping discord_handle to Ghost instance
    """
    logger.info(f"📁 Loading ghosts from directory: {directory}")
    
    ghosts = {}
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.warning(f"⚠️  Directory {directory} does not exist")
        return ghosts
    
    # Supported file extensions
    supported_extensions = ['.json', '.yaml', '.yml']
    
    for file_path in directory_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                logger.debug(f"🔍 Processing ghost file: {file_path}")
                ghost = load_ghost_from_file(file_path)
                if ghost:
                    ghosts[ghost.discord_handle] = ghost
                    logger.info(f"✅ Loaded ghost: {ghost.name} (@{ghost.discord_handle}) using {ghost.model}")
                else:
                    logger.warning(f"⚠️  Failed to create ghost from {file_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load {file_path}: {type(e).__name__}: {e}")
                logger.debug(f"🔍 Ghost loading error details for {file_path}", exc_info=True)
    
    logger.info(f"📋 Successfully loaded {len(ghosts)} ghosts total")
    return ghosts


def load_ghost_from_file(file_path: Path) -> Optional[Ghost]:
    """
    Load a single ghost from a file
    
    Args:
        file_path: Path to the ghost configuration file
        
    Returns:
        Ghost instance or None if loading failed
    """
    try:
        logger.debug(f"📖 Reading ghost file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() == '.json':
                data = json.load(f)
                logger.debug(f"🔧 Parsed JSON data from {file_path}")
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
                logger.debug(f"🔧 Parsed YAML data from {file_path}")
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Validate and create Ghost instance
        ghost = Ghost(**data)
        logger.debug(f"✅ Created ghost instance: {ghost.name} with handle '{ghost.discord_handle}'")
        return ghost
        
    except Exception as e:
        logger.error(f"❌ Error loading ghost from {file_path}: {type(e).__name__}: {e}")
        logger.debug(f"🔍 File loading error details for {file_path}", exc_info=True)
        return None


# Example usage and testing
if __name__ == "__main__":
    # Test loading ghosts
    ghosts = load_ghosts_from_directory("../bots")
    
    for handle, ghost in ghosts.items():
        print(f"\n{ghost}")
        print(f"  Aliases: {ghost.get_aliases()}")
        print(f"  Description: {ghost.description}") 
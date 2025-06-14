import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
import litellm
from litellm import completion
import os

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
        try:
            # Prepare the full message list with system prompt
            full_messages = [
                {"role": "system", "content": self.instructions}
            ] + messages
            
            # Call litellm
            response = await completion(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                timeout=30  # 30 second timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback response if LLM fails
            fallback_msg = f"*{self.name} flickers mysteriously* Sorry, I'm having trouble connecting to the spirit realm right now... ({str(e)[:50]})"
            return fallback_msg
    
    def format_discord_messages_for_llm(self, discord_messages: List[Any]) -> List[Dict[str, str]]:
        """
        Convert Discord message objects to LLM format
        
        Args:
            discord_messages: List of Discord message objects
            
        Returns:
            List of formatted messages for LLM
        """
        formatted_messages = []
        
        for msg in discord_messages:
            # Skip bot messages or empty messages
            if msg.author.bot or not msg.content.strip():
                continue
                
            # Format the message
            formatted_msg = {
                "role": "user",
                "content": f"{msg.author.display_name}: {msg.content}"
            }
            formatted_messages.append(formatted_msg)
        
        # Limit to reasonable context length
        return formatted_messages[-15:]  # Last 15 non-bot messages
    
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
    ghosts = {}
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Warning: Directory {directory} does not exist")
        return ghosts
    
    # Supported file extensions
    supported_extensions = ['.json', '.yaml', '.yml']
    
    for file_path in directory_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                ghost = load_ghost_from_file(file_path)
                if ghost:
                    ghosts[ghost.discord_handle] = ghost
                    print(f"✅ Loaded ghost: {ghost.name} ({ghost.discord_handle})")
            except Exception as e:
                print(f"❌ Failed to load {file_path}: {e}")
    
    print(f"📋 Loaded {len(ghosts)} ghosts total")
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
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() == '.json':
                data = json.load(f)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Validate and create Ghost instance
        ghost = Ghost(**data)
        return ghost
        
    except Exception as e:
        print(f"Error loading ghost from {file_path}: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    # Test loading ghosts
    ghosts = load_ghosts_from_directory("../bots")
    
    for handle, ghost in ghosts.items():
        print(f"\n{ghost}")
        print(f"  Aliases: {ghost.get_aliases()}")
        print(f"  Description: {ghost.description}") 
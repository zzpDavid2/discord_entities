# Ghost-Specific LLM Configuration

This document explains the new ghost-specific LLM configuration features that allow each ghost to have its own LiteLLM client with configurable API URL, model name, and key.

## Overview

Previously, all ghosts used the same global LLM configuration from environment variables. Now, each ghost can override these settings with their own configuration, allowing for:

- Different LLM providers for different ghosts
- Self-hosted LLM instances for specific ghosts
- Different API keys for different ghosts
- Overriding global configuration on a per-ghost basis

## New Configuration Fields

Each ghost can now specify these additional fields in their configuration:

### `api_url` (Optional)
- **Type**: String
- **Description**: Custom API URL for this ghost's LLM client
- **Example**: `"https://api.openai.com/v1"`
- **Validation**: Must start with `http://` or `https://`

### `api_key` (Optional)
- **Type**: String
- **Description**: Custom API key for this ghost's LLM client
- **Example**: `"your-custom-api-key-here"`

## Configuration Examples

### Basic Ghost (Uses Global .env Configuration)
```yaml
name: "🦍 Tomas*"
handle: "tomas"
description: "A first version of Tomas's ghost. Spooky!"
instructions: |
  You are Tomas's ghost, called 🦍 Tomas*, a delightfully eccentric digital ghost.
model: "anthropic/claude-sonnet-4-0"
temperature: 0.7
# No api_url or api_key - uses .env configuration
```

### Ghost with Custom API URL
```yaml
name: "🔮 Custom API Ghost"
handle: "custom"
description: "A ghost with custom API configuration"
instructions: "You are a ghost with custom API configuration."
model: "gpt-4o-mini"
temperature: 0.8
api_url: "https://api.openai.com/v1"
# Uses .env OPENAI_API_KEY
```

### Ghost with Custom API Key
```yaml
name: "🔑 Custom Key Ghost"
handle: "customkey"
description: "A ghost with custom API key"
instructions: "You are a ghost with custom API key."
model: "gpt-4o-mini"
temperature: 0.8
api_key: "your-custom-api-key-here"
# Uses default OpenAI API URL
```

### Ghost with Both Custom URL and Key
```yaml
name: "🔧 Fully Custom Ghost"
handle: "fullycustom"
description: "A ghost with fully custom configuration"
instructions: "You are a ghost with fully custom configuration."
model: "gpt-4o-mini"
temperature: 0.8
api_url: "https://api.openai.com/v1"
api_key: "your-custom-api-key-here"
```

### Self-Hosted LLM Example
```yaml
name: "🏠 Self-Hosted Ghost"
handle: "selfhosted"
description: "A ghost using a self-hosted LLM"
instructions: "You are a ghost using a self-hosted LLM."
model: "llama3.1:8b"
temperature: 0.8
api_url: "http://localhost:11434"
api_key: "ollama"  # or leave empty for no auth
```

## JSON Format Examples

### Basic Configuration
```json
{
    "name": "🐦‍ Anna*",
    "handle": "anna",
    "description": "Anna's ghost",
    "instructions": "You are Anna's ghost, a brilliantly eccentric digital companion.",
    "model": "gpt-4.1-mini"
}
```

### Custom Configuration
```json
{
    "name": "🔮 Custom LLM Ghost (JSON)",
    "handle": "customjson",
    "description": "A ghost with custom LLM configuration in JSON format",
    "instructions": "You are a ghost with custom LLM configuration defined in JSON format.",
    "model": "gpt-4o-mini",
    "temperature": 0.8,
    "api_url": "https://api.openai.com/v1",
    "api_key": "your-custom-api-key-here"
}
```

## Implementation Details

### Ghost Class Changes
The `Ghost` class in `ghosts/ghost.py` has been updated with:

1. **New Fields**:
   - `api_url: Optional[str]` - Custom API URL
   - `api_key: Optional[str]` - Custom API key

2. **Validation**:
   - `api_url` must start with `http://` or `https://`

3. **LLM Call Integration**:
   - Custom `api_url` is passed as `api_base` to LiteLLM
   - Custom `api_key` is passed directly to LiteLLM
   - Falls back to global .env configuration if not specified

### Bot Command Updates
The bot commands have been updated to show custom configurations:

- `!list` - Shows custom API configurations for each ghost
- `!status` - Shows detailed system status including custom configurations

## Usage Examples

### Different Providers for Different Ghosts
```yaml
# Ghost 1: OpenAI
name: "OpenAI Ghost"
model: "gpt-4o-mini"
api_url: "https://api.openai.com/v1"
api_key: "your-openai-key"

# Ghost 2: Anthropic
name: "Claude Ghost"
model: "anthropic/claude-3-5-sonnet"
api_url: "https://api.anthropic.com"
api_key: "your-anthropic-key"

# Ghost 3: Self-hosted
name: "Local Ghost"
model: "llama3.1:8b"
api_url: "http://localhost:11434"
```

### Multiple API Keys for Same Provider
```yaml
# Ghost 1: Personal OpenAI account
name: "Personal Ghost"
model: "gpt-4o-mini"
api_key: "personal-openai-key"

# Ghost 2: Work OpenAI account
name: "Work Ghost"
model: "gpt-4o-mini"
api_key: "work-openai-key"
```

## Migration Guide

### From Global Configuration
If you currently have ghosts using global .env configuration, no changes are needed. The ghosts will continue to work as before.

### Adding Custom Configuration
To add custom configuration to an existing ghost:

1. Add `api_url` and/or `api_key` fields to the ghost's configuration file
2. Restart the bot or use `!reload` to reload configurations
3. Use `!status` to verify the custom configuration is loaded

### Testing Custom Configuration
1. Create a test ghost with custom configuration
2. Use `!test-ghost ghostname` to test the configuration
3. Check the logs for custom API URL/key usage

## Troubleshooting

### Common Issues

1. **Invalid API URL**: Ensure URLs start with `http://` or `https://`
2. **API Key Not Working**: Verify the API key is valid and has proper permissions
3. **Configuration Not Loading**: Check YAML/JSON syntax and use `!reload`
4. **Fallback to Global Config**: If custom config fails, ghosts fall back to .env settings

### Debugging

- Use `!status` to see which ghosts have custom configurations
- Check logs for API URL/key usage messages
- Use `!test-ghost ghostname` to test specific ghost configurations

## Security Considerations

- **API Keys**: Store sensitive API keys securely, consider using environment variables
- **URL Validation**: API URLs are validated to ensure they start with http/https
- **Fallback**: If custom configuration fails, ghosts fall back to global settings

## Future Enhancements

Potential future improvements:

- Support for additional LLM parameters (max_tokens, timeout, etc.)
- Configuration validation and testing tools
- Support for multiple API endpoints per ghost
- Configuration templates for common providers 
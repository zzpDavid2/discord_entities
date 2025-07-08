# Entity-Specific LLM Configuration

This document explains the entity-specific LLM configuration features that allow each entity to have its own LiteLLM client with configurable API URL, model name, and key.

## Overview

Previously, all entities used the same global LLM configuration from environment variables. Now, each entity can override these settings with their own configuration, allowing for:

- Different LLM providers for different entities
- Self-hosted LLM instances for specific entities
- Different API keys for different entities
- Overriding global configuration on a per-entity basis

## New Configuration Fields

Each entity can now specify these additional fields in their configuration:

### `api_url` (Optional)
- **Type**: String
- **Description**: Custom API URL for this entity's LLM client
- **Example**: `"https://api.openai.com/v1"`
- **Validation**: Must start with `http://` or `https://`

### `api_key` (Optional)
- **Type**: String
- **Description**: Custom API key for this entity's LLM client
- **Example**: `"your-custom-api-key-here"`

## Configuration Examples

### Basic Entity (Uses Global .env Configuration)
```yaml
name: "🦍 Tomas*"
handle: "tomas"
description: "A first version of Tomas's entity. Spooky!"
instructions: |
  You are Tomas's entity, called 🦍 Tomas*, a delightfully eccentric digital entity.
model: "anthropic/claude-sonnet-4-0"
temperature: 0.7
# No api_url or api_key - uses .env configuration
```

### Entity with Custom API URL
```yaml
name: "🔮 Custom API Entity"
handle: "custom"
description: "An entity with custom API configuration"
instructions: "You are an entity with custom API configuration."
model: "gpt-4o-mini"
temperature: 0.8
api_url: "https://api.openai.com/v1"
# Uses .env OPENAI_API_KEY
```

### Entity with Custom API Key
```yaml
name: "🔑 Custom Key Entity"
handle: "customkey"
description: "An entity with custom API key"
instructions: "You are an entity with custom API key."
model: "gpt-4o-mini"
temperature: 0.8
api_key: "your-custom-api-key-here"
# Uses default OpenAI API URL
```

### Entity with Both Custom URL and Key
```yaml
name: "🔧 Fully Custom Entity"
handle: "fullycustom"
description: "An entity with fully custom configuration"
instructions: "You are an entity with fully custom configuration."
model: "gpt-4o-mini"
temperature: 0.8
api_url: "https://api.openai.com/v1"
api_key: "your-custom-api-key-here"
```

### Self-Hosted LLM Example
```yaml
name: "🏠 Self-Hosted Entity"
handle: "selfhosted"
description: "An entity using a self-hosted LLM"
instructions: "You are an entity using a self-hosted LLM."
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
    "description": "Anna's entity",
    "instructions": "You are Anna's entity, a brilliantly eccentric digital companion.",
    "model": "gpt-4.1-mini"
}
```

### Custom Configuration
```json
{
    "name": "🔮 Custom LLM Entity (JSON)",
    "handle": "customjson",
    "description": "An entity with custom LLM configuration in JSON format",
    "instructions": "You are an entity with custom LLM configuration defined in JSON format.",
    "model": "gpt-4o-mini",
    "temperature": 0.8,
    "api_url": "https://api.openai.com/v1",
    "api_key": "your-custom-api-key-here"
}
```

## Implementation Details

### Entity Class Changes
The `Entity` class in `entities/entity.py` has been updated with:

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

- `!list` - Shows custom API configurations for each entity
- `!status` - Shows detailed system status including custom configurations

## Usage Examples

### Different Providers for Different Entities
```yaml
# Entity 1: OpenAI
name: "OpenAI Entity"
model: "gpt-4o-mini"
api_url: "https://api.openai.com/v1"
api_key: "your-openai-key"

# Entity 2: Anthropic
name: "Claude Entity"
model: "anthropic/claude-3-5-sonnet"
api_url: "https://api.anthropic.com"
api_key: "your-anthropic-key"

# Entity 3: Self-hosted
name: "Local Entity"
model: "llama3.1:8b"
api_url: "http://localhost:11434"
```

### Multiple API Keys for Same Provider
```yaml
# Entity 1: Personal OpenAI account
name: "Personal Entity"
model: "gpt-4o-mini"
api_key: "personal-openai-key"

# Entity 2: Work OpenAI account
name: "Work Entity"
model: "gpt-4o-mini"
api_key: "work-openai-key"
```

## Troubleshooting

### Common Issues

1. **Invalid API URL**: Ensure URLs start with `http://` or `https://`
2. **API Key Not Working**: Verify the API key is valid and has proper permissions
3. **Configuration Not Loading**: Check YAML/JSON syntax and use `!reload`
4. **Fallback to Global Config**: If custom config fails, entities fall back to .env settings

### Debugging

- Use `!status` to see which entities have custom configurations
- Check logs for API URL/key usage messages
- Use `!test-entity entityname` to test specific entity configurations

## Security Considerations

- **API Keys**: Store sensitive API keys securely, consider using environment variables
- **URL Validation**: API URLs are validated to ensure they start with http/https
- **Fallback**: If custom configuration fails, entities fall back to global settings

## Future Enhancements

Potential future improvements:

- Support for additional LLM parameters (max_tokens, timeout, etc.)
- Configuration validation and testing tools
- Support for multiple API endpoints per entity
- Configuration templates for common providers 
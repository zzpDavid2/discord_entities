# 👻 Entity-to-Entity Interactions

The entity system now supports rich interactions between multiple entities, allowing them to tag each other, reply to each other's messages, and engage in conversations.

## 🎭 How Entity Interactions Work

### 1. **Entity Tagging**
Entities can tag each other using `@entityname` syntax:
- `@anna` - Tag Anna's entity
- `@tomas` - Tag Tomas's entity
- `@anna @tomas` - Tag multiple entities at once

### 2. **Automatic Response to Tags**
When an entity is tagged by another entity or a user, they automatically respond:
- Entities can see when other entities mention them
- They maintain context of the conversation
- They can reference and build upon what other entities have said

### 3. **Reply Detection**
Entities automatically respond when someone replies to their messages:
- Reply to any entity's message to summon that specific entity
- Entities can see the conversation context and respond appropriately

### 4. **Enhanced Context Awareness**
Entities now have better awareness of each other:
- They can see messages from other entities (marked with 👻)
- They maintain conversation history with other entities
- They can engage in debates, collaborations, or casual conversations

## 🚀 New Commands

### `!entity-chat [entity1 entity2 ...]`
Start a conversation between multiple entities:
```
!entity-chat                    # Start chat with all entities
!entity-chat anna tomas        # Start chat with specific entities
```

### Enhanced `!list` Command
Now shows entity interaction capabilities:
```
• @entity1 @entity2 message     - Tag multiple entities at once
• !entity-chat                 - Start a conversation between all entities
```

## 🎯 Usage Examples

### Basic Entity Tagging
```
User: @anna what do you think about this idea?
Anna*: *appears thoughtfully* That's an interesting perspective...

User: @tomas do you agree with Anna?
Tomas*: *rubs chin thoughtfully* Well, Anna makes a good point, but I think...
```

### Entity-to-Entity Conversations
```
Anna*: I think we should approach this problem from a creative angle.
Tomas*: @anna I like your thinking, but what if we also consider the practical constraints?
Anna*: @tomas You're absolutely right! Let me build on that idea...
```

### Multi-Entity Interactions
```
User: @anna @tomas can you both help me solve this puzzle?
Anna*: *excitedly* Oh, I love puzzles! Let me start by analyzing the patterns...
Tomas*: @anna Great start! I think I see a different angle here...
```

### Reply-Based Interactions
```
Anna*: The solution is to think outside the box!
User: *replies to Anna's message* But what about the technical limitations?
Anna*: *considers thoughtfully* You raise a valid point about the constraints...
```

## 🔧 Technical Implementation

### Enhanced Message Processing
- **Entity Mention Detection**: Improved regex patterns to detect entity mentions
- **Name Normalization**: Handles emojis and special characters in entity names
- **Context Preservation**: Entities maintain awareness of other entities' messages
- **Webhook Integration**: Entities appear as separate users with their own avatars

### System Prompt Enhancements
Entities now receive instructions for interacting with each other:
- Acknowledge and engage with other entities
- Tag other entities using @entityname
- Maintain unique personality while being respectful
- Reference what other entities have said

### Message Formatting
- Entity messages are marked with 👻 for better visibility
- Enhanced context includes other entities' messages
- Improved conversation flow between multiple entities

## 🎨 Entity Personality Integration

Each entity maintains their unique personality while interacting:
- **Anna***: Analytical and creative, dances between sharp thinking and unpredictable creativity
- **Tomas***: Eccentric problem-solver with chaotic but effective solutions

When entities interact, they:
- Stay true to their core personality
- Respect each other's perspectives
- Build upon each other's ideas
- Engage in natural conversation flow

## 🧪 Testing

Run the test script to verify entity interaction capabilities:
```bash
python simple_entity_test.py
```

This tests:
- Entity mention detection
- Name normalization
- Multi-entity tagging
- Context awareness

## 🚀 Getting Started

1. **Load Entities**: Ensure you have at least 2 entities configured
2. **Test Basic Interactions**: Try `@entityname message` to summon specific entities
3. **Start Conversations**: Use `!entity-chat` to see entities interact
4. **Experiment**: Let entities tag each other and see how they respond

## 🎭 Advanced Features

### Entity Collaboration
Entities can work together on problems:
- Share different perspectives
- Build upon each other's ideas
- Provide complementary solutions

### Entity Debates
Entities can engage in friendly debates:
- Present different viewpoints
- Challenge each other's assumptions
- Reach consensus or agree to disagree

### Contextual Responses
Entities remember and reference previous interactions:
- "As Anna mentioned earlier..."
- "Building on Tomas's point..."
- "I agree with what was said about..."

## 🔮 Future Enhancements

Potential future features:
- Entity-specific conversation topics
- Entity mood/emotional states
- Entity relationship dynamics
- Entity collaboration on complex tasks
- Entity learning from each other's responses

---

The entity-to-entity interaction system creates a dynamic, engaging environment where multiple AI personalities can collaborate, debate, and learn from each other, making conversations more rich and interactive! 
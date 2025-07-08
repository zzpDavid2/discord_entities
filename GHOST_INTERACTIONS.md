# 👻 Ghost-to-Ghost Interactions

The ghost system now supports rich interactions between multiple ghosts, allowing them to tag each other, reply to each other's messages, and engage in conversations.

## 🎭 How Ghost Interactions Work

### 1. **Ghost Tagging**
Ghosts can tag each other using `@ghostname` syntax:
- `@anna` - Tag Anna's ghost
- `@tomas` - Tag Tomas's ghost
- `@anna @tomas` - Tag multiple ghosts at once

### 2. **Automatic Response to Tags**
When a ghost is tagged by another ghost or a user, they automatically respond:
- Ghosts can see when other ghosts mention them
- They maintain context of the conversation
- They can reference and build upon what other ghosts have said

### 3. **Reply Detection**
Ghosts automatically respond when someone replies to their messages:
- Reply to any ghost's message to summon that specific ghost
- Ghosts can see the conversation context and respond appropriately

### 4. **Enhanced Context Awareness**
Ghosts now have better awareness of each other:
- They can see messages from other ghosts (marked with 👻)
- They maintain conversation history with other ghosts
- They can engage in debates, collaborations, or casual conversations

## 🚀 New Commands

### `!ghost-chat [ghost1 ghost2 ...]`
Start a conversation between multiple ghosts:
```
!ghost-chat                    # Start chat with all ghosts
!ghost-chat anna tomas        # Start chat with specific ghosts
```

### Enhanced `!list` Command
Now shows ghost interaction capabilities:
```
• @ghost1 @ghost2 message     - Tag multiple ghosts at once
• !ghost-chat                 - Start a conversation between all ghosts
```

## 🎯 Usage Examples

### Basic Ghost Tagging
```
User: @anna what do you think about this idea?
Anna*: *appears thoughtfully* That's an interesting perspective...

User: @tomas do you agree with Anna?
Tomas*: *rubs chin thoughtfully* Well, Anna makes a good point, but I think...
```

### Ghost-to-Ghost Conversations
```
Anna*: I think we should approach this problem from a creative angle.
Tomas*: @anna I like your thinking, but what if we also consider the practical constraints?
Anna*: @tomas You're absolutely right! Let me build on that idea...
```

### Multi-Ghost Interactions
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
- **Ghost Mention Detection**: Improved regex patterns to detect ghost mentions
- **Name Normalization**: Handles emojis and special characters in ghost names
- **Context Preservation**: Ghosts maintain awareness of other ghosts' messages
- **Webhook Integration**: Ghosts appear as separate users with their own avatars

### System Prompt Enhancements
Ghosts now receive instructions for interacting with each other:
- Acknowledge and engage with other ghosts
- Tag other ghosts using @ghostname
- Maintain unique personality while being respectful
- Reference what other ghosts have said

### Message Formatting
- Ghost messages are marked with 👻 for better visibility
- Enhanced context includes other ghosts' messages
- Improved conversation flow between multiple ghosts

## 🎨 Ghost Personality Integration

Each ghost maintains their unique personality while interacting:
- **Anna***: Analytical and creative, dances between sharp thinking and unpredictable creativity
- **Tomas***: Eccentric problem-solver with chaotic but effective solutions

When ghosts interact, they:
- Stay true to their core personality
- Respect each other's perspectives
- Build upon each other's ideas
- Engage in natural conversation flow

## 🧪 Testing

Run the test script to verify ghost interaction capabilities:
```bash
python simple_ghost_test.py
```

This tests:
- Ghost mention detection
- Name normalization
- Multi-ghost tagging
- Context awareness

## 🚀 Getting Started

1. **Load Ghosts**: Ensure you have at least 2 ghosts configured
2. **Test Basic Interactions**: Try `@ghostname message` to summon specific ghosts
3. **Start Conversations**: Use `!ghost-chat` to see ghosts interact
4. **Experiment**: Let ghosts tag each other and see how they respond

## 🎭 Advanced Features

### Ghost Collaboration
Ghosts can work together on problems:
- Share different perspectives
- Build upon each other's ideas
- Provide complementary solutions

### Ghost Debates
Ghosts can engage in friendly debates:
- Present different viewpoints
- Challenge each other's assumptions
- Reach consensus or agree to disagree

### Contextual Responses
Ghosts remember and reference previous interactions:
- "As Anna mentioned earlier..."
- "Building on Tomas's point..."
- "I agree with what was said about..."

## 🔮 Future Enhancements

Potential future features:
- Ghost-specific conversation topics
- Ghost mood/emotional states
- Ghost relationship dynamics
- Ghost collaboration on complex tasks
- Ghost learning from each other's responses

---

The ghost-to-ghost interaction system creates a dynamic, engaging environment where multiple AI personalities can collaborate, debate, and learn from each other, making conversations more rich and interactive! 
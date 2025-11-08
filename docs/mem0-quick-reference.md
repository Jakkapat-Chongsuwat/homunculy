# Mem0 Quick Reference Card

## 🚀 Quick Start

### 1. Install Dependencies
```bash
poetry install
# OR
docker-compose build app
```

### 2. Configure Environment
```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Test
```bash
python quick_ws_test_long.py
```

---

## 📁 File Locations

| Component | File Path |
|-----------|-----------|
| **Abstract Interface** | `src/repositories/abstraction/memory.py` |
| **Implementation** | `src/repositories/mem0_db/repository.py` |
| **Configuration** | `src/settings/mem0.py` |
| **Use Case Integration** | `src/usecases/waifu.py` |
| **WebSocket Controller** | `src/controllers/websocket/waifu_router.py` |
| **DI Registration** | `src/di/dependency_injection.py` |
| **Documentation** | `docs/mem0-integration.md` |
| **Testing Checklist** | `docs/mem0-testing-checklist.md` |

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key for memory inference |
| `MEM0_API_KEY` | Yes* | - | Mem0 hosted platform key |
| `MEM0_LLM_PROVIDER` | No | `openai` | LLM provider for inference |
| `MEM0_LLM_MODEL` | No | `gpt-4o-mini` | LLM model for inference |
| `MEM0_VECTOR_STORE_PROVIDER` | No | `qdrant` | Vector database provider |
| `MEM0_VECTOR_STORE_HOST` | No | `localhost` | Vector store host |
| `MEM0_VECTOR_STORE_PORT` | No | `6333` | Vector store port |
| `MEM0_ENABLE_INFER` | No | `true` | Enable automatic inference |
| `MEM0_SEARCH_LIMIT` | No | `5` | Default search result limit |

\* Either `OPENAI_API_KEY` or `MEM0_API_KEY` required

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────┐
│  Domain Layer                            │
│  IMemoryRepository (abstraction)         │
└──────────────────────────────────────────┘
                    ▲
┌──────────────────────────────────────────┐
│  Infrastructure Layer                    │
│  Mem0Repository (implementation)         │
└──────────────────────────────────────────┘
                    ▲
┌──────────────────────────────────────────┐
│  Use Case Layer                          │
│  chat_with_waifu() + streaming           │
└──────────────────────────────────────────┘
                    ▲
┌──────────────────────────────────────────┐
│  Controller Layer                        │
│  WebSocket Router                        │
└──────────────────────────────────────────┘
```

---

## 💾 Memory Operations

### Add Memory
```python
await memory_repository.add_memory(
    messages=[
        {"role": "user", "content": "I love sci-fi"},
        {"role": "assistant", "content": "Noted!"}
    ],
    user_id="user123",
    agent_id="sakura_chan",
    metadata={"affection_level": 45}
)
```

### Search Memories
```python
results = await memory_repository.search_memories(
    query="What are my interests?",
    user_id="user123",
    agent_id="sakura_chan",
    limit=5
)

for item in results.results:
    print(f"{item.memory} (score: {item.score})")
```

### Get All Memories
```python
results = await memory_repository.get_all_memories(
    user_id="user123",
    agent_id="sakura_chan"
)
```

### Update Memory
```python
updated = await memory_repository.update_memory(
    memory_id="mem_123",
    data="Updated memory content"
)
```

### Delete Memory
```python
success = await memory_repository.delete_memory(
    memory_id="mem_123"
)
```

---

## 🔄 Memory Flow

### Storage Flow
```
User Message → Waifu Response → Store Conversation
    ↓
Mem0 Infers Semantic Memory
    ↓
Stored as Vector Embedding
```

### Retrieval Flow
```
User Message → Search Relevant Memories
    ↓
Add to LLM Context
    ↓
Generate Contextual Response
```

---

## 🧪 Testing Commands

### Run All Tests
```bash
pytest
```

### Test Specific Module
```bash
pytest tests/unit/test_memory_repository.py
```

### Test with Coverage
```bash
pytest --cov=src/repositories/mem0_db
```

### Manual WebSocket Test
```bash
python quick_ws_test_long.py
```

---

## 📊 Expected Behavior

### With Memory Enabled
- ✅ Past conversations remembered
- ✅ Contextual responses
- ✅ Personalized interactions
- ✅ ~100-200ms additional latency

### Without Memory (Graceful Degradation)
- ✅ Chat still works
- ⚠️ No conversation memory
- ⚠️ Less personalized
- ✅ No additional latency

---

## 🐛 Troubleshooting

### Issue: "Memory repository not available"
**Solution**: 
- Check `OPENAI_API_KEY` in `.env`
- Verify Mem0Settings loaded correctly
- Check DI registration

### Issue: "Cannot connect to vector store"
**Solution**:
- Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
- Verify `MEM0_VECTOR_STORE_HOST` and `MEM0_VECTOR_STORE_PORT`

### Issue: Memories not persisting
**Solution**:
- Check environment variables loaded
- Verify Mem0 configuration in logs
- Test memory operations directly

### Issue: High latency
**Solution**:
- Reduce `MEM0_SEARCH_LIMIT` (default: 5)
- Use caching for frequent queries
- Consider async memory storage

---

## 📈 Performance Benchmarks

| Operation | Expected Time |
|-----------|---------------|
| Memory Storage | < 100ms (async) |
| Memory Search | 100-200ms |
| Chat without Memory | 1-2s |
| Chat with Memory | 1.5-2.5s |

---

## 🔍 Useful Log Commands

### View Real-time Logs
```powershell
docker-compose logs -f app
```

### Search for Memory Logs
```powershell
docker-compose logs app | Select-String -Pattern "memory"
```

### Check Memory Operations
```powershell
docker-compose logs app | Select-String -Pattern "Retrieved|Stored"
```

---

## 📝 Code Examples

### Use Case Integration
```python
# In use case
async def chat_with_waifu(
    # ... other params
    memory_repository: Optional['IMemoryRepository'] = None
):
    # Retrieve memories
    if memory_repository:
        results = await memory_repository.search_memories(
            query=user_message,
            user_id=request.user_id,
            agent_id=waifu.waifu_id,
            limit=5
        )
        llm_context["relevant_memories"] = [
            item.memory for item in results.results
        ]
    
    # ... generate response
    
    # Store memory
    if memory_repository:
        await memory_repository.add_memory(
            messages=[
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response}
            ],
            user_id=request.user_id,
            agent_id=waifu.waifu_id,
            metadata=metadata
        )
```

### Controller Integration
```python
# In WebSocket router
try:
    memory_repository = injector.get(IMemoryRepository)
except Exception as e:
    logger.warning(f"Memory repository not available: {e}")
    memory_repository = None

# Pass to use case
async for chunk in chat_with_waifu_stream(
    # ... other params
    memory_repository=memory_repository
):
    await websocket.send_text(chunk)
```

---

## 🎯 Success Criteria

- [x] Dependencies installed
- [x] Environment configured
- [x] Services running
- [x] Memories stored after chat
- [x] Memories retrieved before responses
- [x] Contextual responses working
- [x] Graceful degradation working
- [x] No crashes or errors

---

## 📚 Additional Resources

- **Integration Guide**: `docs/mem0-integration.md`
- **Testing Checklist**: `docs/mem0-testing-checklist.md`
- **Implementation Summary**: `docs/mem0-implementation-summary.md`
- **Mem0 Documentation**: https://docs.mem0.ai/
- **Mem0 GitHub**: https://github.com/mem0ai/mem0

---

## 🚨 Emergency Rollback

```powershell
# 1. Comment out memory integration
# 2. Remove MemoryModule from DI
# 3. Rebuild

git diff  # Review changes
git checkout HEAD -- src/usecases/waifu.py
docker-compose restart app
```

---

## 💡 Quick Tips

1. **Start Simple**: Use default configuration first
2. **Check Logs**: Always check logs for warnings
3. **Test Incrementally**: Test each feature separately
4. **Mock in Tests**: Use mocks for fast unit tests
5. **Monitor Performance**: Track memory operation times
6. **Adjust Limits**: Tune `MEM0_SEARCH_LIMIT` based on needs

---

**Version**: 1.0.0  
**Last Updated**: [Current Session]  
**Status**: ✅ Production Ready

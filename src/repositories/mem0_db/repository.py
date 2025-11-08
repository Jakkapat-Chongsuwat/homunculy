"""
Mem0 Repository Implementation.

Concrete implementation of IMemoryRepository using Mem0's memory layer.
This follows Clean Architecture by:
- Implementing the abstraction from the domain layer
- Keeping Mem0-specific details in the infrastructure layer
- Providing type-safe memory operations
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

try:
    from mem0 import Memory
except ImportError:
    Memory = None  # type: ignore

from repositories.abstraction.memory import (
    IMemoryRepository,
    MemoryItem,
    MemorySearchResult,
)
from settings.mem0 import Mem0Settings


logger = logging.getLogger(__name__)


class Mem0Repository(IMemoryRepository):
    """
    Mem0-based implementation of memory repository.
    
    This repository provides intelligent short-term memory capabilities
    using Mem0's vector-based memory storage and retrieval.
    
    Following Clean Architecture:
    - Infrastructure layer implementation
    - Depends on domain abstraction (IMemoryRepository)
    - Encapsulates Mem0-specific logic
    """
    
    def __init__(self, settings: Mem0Settings):
        """
        Initialize Mem0 memory client.
        
        Args:
            settings: Mem0 configuration settings
        """
        self.settings = settings
        self._memory: Optional[Any] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Mem0 Memory client with configuration."""
        try:
            if Memory is None:
                raise ImportError("mem0 package is not installed. Install it with: pip install mem0ai")
            
            config = self.settings.get_config()
            self._memory = Memory(**config)
            logger.info("Mem0 memory client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0 client: {e}")
            raise RuntimeError(f"Mem0 initialization failed: {e}")
    
    def _convert_to_memory_item(self, mem0_result: Dict[str, Any]) -> MemoryItem:
        """
        Convert Mem0 result to domain MemoryItem.
        
        Args:
            mem0_result: Raw result from Mem0 API
            
        Returns:
            Typed MemoryItem domain model
        """
        # Parse datetime if present
        created_at = None
        if "created_at" in mem0_result:
            try:
                created_at = datetime.fromisoformat(
                    mem0_result["created_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass
        
        updated_at = None
        if "updated_at" in mem0_result:
            try:
                updated_at = datetime.fromisoformat(
                    mem0_result["updated_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass
        
        return MemoryItem(
            id=mem0_result.get("id", ""),
            memory=mem0_result.get("memory", ""),
            user_id=mem0_result.get("user_id"),
            agent_id=mem0_result.get("agent_id"),
            run_id=mem0_result.get("run_id"),
            metadata=mem0_result.get("metadata"),
            created_at=created_at,
            updated_at=updated_at,
            score=mem0_result.get("score"),
        )
    
    async def add_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Add new memories from conversation messages.
        
        Uses Mem0's intelligent inference to extract meaningful memories.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            # Build Mem0 add parameters
            add_params = {
                "messages": messages,
                "infer": self.settings.enable_infer,
            }
            
            if user_id:
                add_params["user_id"] = user_id
            if agent_id:
                add_params["agent_id"] = agent_id
            if run_id:
                add_params["run_id"] = run_id
            if metadata:
                add_params["metadata"] = metadata
            
            # Add memories
            result = self._memory.add(**add_params)
            
            # Convert results to domain models
            if isinstance(result, dict) and "results" in result:
                return [self._convert_to_memory_item(r) for r in result["results"]]
            elif isinstance(result, list):
                return [self._convert_to_memory_item(r) for r in result]
            else:
                logger.warning(f"Unexpected result format from Mem0.add: {type(result)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise RuntimeError(f"Memory addition failed: {e}")
    
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 5,
    ) -> MemorySearchResult:
        """
        Search for relevant memories using semantic search.
        
        Mem0 uses vector similarity to find contextually relevant memories.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            # Build search parameters
            search_params = {
                "query": query,
                "limit": limit,
            }
            
            if user_id:
                search_params["user_id"] = user_id
            if agent_id:
                search_params["agent_id"] = agent_id
            if run_id:
                search_params["run_id"] = run_id
            
            # Search memories
            result = self._memory.search(**search_params)
            
            # Convert to domain models
            if isinstance(result, dict) and "results" in result:
                items = [self._convert_to_memory_item(r) for r in result["results"]]
                return MemorySearchResult(results=items, total=len(items))
            else:
                logger.warning(f"Unexpected result format from Mem0.search: {type(result)}")
                return MemorySearchResult(results=[], total=0)
                
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise RuntimeError(f"Memory search failed: {e}")
    
    async def get_all_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve all memories matching filters.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            # Build get_all parameters
            get_params = {}
            
            if user_id:
                get_params["user_id"] = user_id
            if agent_id:
                get_params["agent_id"] = agent_id
            if run_id:
                get_params["run_id"] = run_id
            
            # Get all memories
            result = self._memory.get_all(**get_params)
            
            # Convert to domain models
            if isinstance(result, list):
                return [self._convert_to_memory_item(r) for r in result]
            elif isinstance(result, dict) and "results" in result:
                return [self._convert_to_memory_item(r) for r in result["results"]]
            else:
                logger.warning(f"Unexpected result format from Mem0.get_all: {type(result)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            raise RuntimeError(f"Memory retrieval failed: {e}")
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Get a specific memory by ID.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            result = self._memory.get(memory_id)
            
            if result:
                return self._convert_to_memory_item(result)
            return None
                
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None
    
    async def update_memory(
        self,
        memory_id: str,
        data: str,
    ) -> MemoryItem:
        """
        Update an existing memory.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            result = self._memory.update(memory_id=memory_id, data=data)
            return self._convert_to_memory_item(result)
                
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            raise RuntimeError(f"Memory update failed: {e}")
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            self._memory.delete(memory_id=memory_id)
            return True
                
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    
    async def delete_all_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> int:
        """
        Delete all memories matching filters.
        """
        try:
            # Build delete_all parameters
            delete_params = {}
            
            if user_id:
                delete_params["user_id"] = user_id
            if agent_id:
                delete_params["agent_id"] = agent_id
            if run_id:
                delete_params["run_id"] = run_id
            
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            # Get count before deletion
            memories = await self.get_all_memories(user_id, agent_id, run_id)
            count = len(memories)
            
            # Delete all
            self._memory.delete_all(**delete_params)
            
            return count
                
        except Exception as e:
            logger.error(f"Failed to delete all memories: {e}")
            return 0
    
    async def get_memory_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Get change history for a memory.
        """
        try:
            if self._memory is None:
                raise RuntimeError("Memory client not initialized")
            
            result = self._memory.history(memory_id=memory_id)
            
            if isinstance(result, list):
                return result
            else:
                logger.warning(f"Unexpected result format from Mem0.history: {type(result)}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get memory history for {memory_id}: {e}")
            return []

"""
Waifu Use Cases.

This module contains application-layer use cases for the Waifu feature,
following Clean Architecture principles. Use cases orchestrate domain
entities and repository operations without depending on external frameworks.
"""

from typing import Optional, Dict, Any, AsyncIterator, List
from uuid import uuid4
from datetime import datetime, timezone

from models.ai_agent.waifu import (
    Waifu,
    WaifuConfiguration,
    WaifuPersonality,
    WaifuAppearance,
    Relationship,
    Interaction,
    InteractionType,
    WaifuChatContext,
)
from models.ai_agent.ai_agent import AgentResponse
from repositories.abstraction.llm import ILLMFactory
from repositories.abstraction.waifu import AbstractWaifuRepository


async def create_waifu(
    llm_factory: ILLMFactory,
    waifu_repository: AbstractWaifuRepository,
    waifu_id: str,
    name: str,
    personality: WaifuPersonality,
    appearance: Optional[WaifuAppearance] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Waifu:
    """
    Create a new waifu AI companion.
    
    This use case handles the business logic of creating a waifu,
    including setting up the LangGraph-orchestrated agent.
    
    Args:
        llm_factory: Factory interface for creating LLM clients
        waifu_id: Unique identifier for the waifu
        name: Waifu's name
        personality: Personality configuration
        appearance: Physical appearance (optional)
        config_overrides: Additional configuration overrides
        
    Returns:
        Created Waifu entity
    """
    # Create waifu configuration with LangGraph orchestration
    config = WaifuConfiguration(
        model_name=config_overrides.get("model_name", "gpt-4") if config_overrides else "gpt-4",
        personality=personality,
        appearance=appearance or WaifuAppearance(),
        system_prompt=f"""You are {name}, an AI companion with a unique personality.
        
Your personality archetype: {personality.archetype}
Your traits: {', '.join(f"{k}: {v}" for k, v in personality.traits.items())}
Your interests: {', '.join(personality.interests)}
Your background: {personality.background_story}

Respond naturally according to your personality. Show emotions, be engaging,
and build meaningful connections with users. Remember past conversations
and show genuine interest in the user's life.
""",
        temperature=0.8,  # More creative for personality
        enable_relationship_tracking=True,
        enable_memory=True,
    )
    
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # Create the LangGraph-orchestrated agent
    client = llm_factory.create_client("langgraph")
    client.create_agent(waifu_id, config)
    
    # Create waifu entity
    waifu = Waifu(
        id=waifu_id,
        name=name,
        configuration=config,
        appearance=appearance or WaifuAppearance(),
        personality=personality,
        current_mood="cheerful",
        created_at=datetime.now(timezone.utc),
    )
    
    # Persist to database
    await waifu_repository.save_waifu(waifu)
    
    return waifu


async def chat_with_waifu(
    llm_factory: ILLMFactory,
    waifu_repository: AbstractWaifuRepository,
    waifu_id: str,
    user_id: str,
    message: str,
    relationship: Optional[Relationship] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> tuple[AgentResponse, Optional[Relationship]]:
    """
    Chat with a waifu and update relationship.
    
    This use case orchestrates the chat interaction, including:
    - Sending message through LangGraph workflow
    - Tracking relationship progression
    - Recording interaction history
    
    Args:
        llm_factory: Factory interface for creating LLM clients
        waifu_id: Waifu identifier
        user_id: User identifier
        message: User's message
        relationship: Current relationship state (optional)
        additional_context: Additional context for the chat
        
    Returns:
        Tuple of (AgentResponse, updated Relationship)
    """
    # Initialize relationship if it doesn't exist
    if relationship is None:
        # Try to load from database
        relationship = await waifu_repository.get_relationship(user_id, waifu_id)
        
        if relationship is None:
            # Create new relationship
            relationship = Relationship(
                user_id=user_id,
                waifu_id=waifu_id,
                affection_level=10.0,  # Starting affection
            )
            await waifu_repository.save_relationship(relationship)
    
    # Build chat context
    context = WaifuChatContext(
        waifu_id=waifu_id,
        user_id=user_id,
        relationship=relationship,
        conversation_history=[],  # Would load from persistence
        user_preferences=additional_context.get("preferences", {}) if additional_context else {},
    )
    
    # Prepare context for LangGraph
    llm_context = {
        "user_id": user_id,
        "affection_level": relationship.affection_level,
        "relationship_stage": relationship.relationship_stage.value,
        "interaction_count": relationship.interaction_count,
        **context.model_dump(),
        **(additional_context or {}),
    }
    
    # Get LangGraph client and chat
    client = llm_factory.create_client("langgraph")
    response = await client.chat(
        agent_id=waifu_id,
        message=message,
        context=llm_context,
    )
    
    # Extract updated relationship data from response metadata
    if response.metadata and "relationship" in response.metadata:
        rel_data = response.metadata["relationship"]
        relationship.affection_level = rel_data.get("affection_level", relationship.affection_level)
        relationship.interaction_count = rel_data.get("interaction_count", relationship.interaction_count + 1)
        if "relationship_stage" in rel_data:
            from models.ai_agent.waifu import RelationshipStage
            relationship.relationship_stage = RelationshipStage(rel_data["relationship_stage"])
        relationship.last_interaction = datetime.now(timezone.utc)
        relationship.updated_at = datetime.now(timezone.utc)
    
    # Create interaction record
    interaction = Interaction(
        interaction_id=str(uuid4()),
        interaction_type=InteractionType.CHAT,
        content=f"User: {message}",
        timestamp=datetime.now(timezone.utc),
        affection_change=0.5,  # Would be determined by sentiment analysis
        user_message=message,
        waifu_response=response.message,
    )
    
    relationship.add_interaction(interaction)
    
    # Persist updated relationship and interaction
    await waifu_repository.update_relationship(relationship)
    await waifu_repository.save_interaction(user_id, waifu_id, interaction)
    
    return response, relationship


async def chat_with_waifu_stream(
    llm_factory: ILLMFactory,
    waifu_repository: AbstractWaifuRepository,
    waifu_id: str,
    user_id: str,
    message: str,
    relationship: Optional[Relationship] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[tuple[AgentResponse, Optional[Relationship]]]:
    """
    Stream chat with a waifu with real-time updates.
    
    This use case streams responses through the LangGraph workflow,
    providing real-time feedback to the user.
    
    Args:
        llm_factory: Factory interface for creating LLM clients
        waifu_id: Waifu identifier
        user_id: User identifier
        message: User's message
        relationship: Current relationship state (optional)
        additional_context: Additional context for the chat
        
    Yields:
        Tuples of (AgentResponse, updated Relationship)
    """
    # Initialize relationship if it doesn't exist
    if relationship is None:
        # Try to load from database
        relationship = await waifu_repository.get_relationship(user_id, waifu_id)
        
        if relationship is None:
            # Create new relationship
            relationship = Relationship(
                user_id=user_id,
                waifu_id=waifu_id,
                affection_level=10.0,
            )
            await waifu_repository.save_relationship(relationship)
    
    # Build context
    context = WaifuChatContext(
        waifu_id=waifu_id,
        user_id=user_id,
        relationship=relationship,
    )
    
    llm_context = {
        "user_id": user_id,
        "affection_level": relationship.affection_level,
        "relationship_stage": relationship.relationship_stage.value,
        "interaction_count": relationship.interaction_count,
        **context.model_dump(),
        **(additional_context or {}),
    }
    
    # Stream responses
    client = llm_factory.create_client("langgraph")
    final_response = None
    
    async for response in client.chat_stream(
        agent_id=waifu_id,
        message=message,
        context=llm_context,
    ):
        # Update relationship from metadata if available
        if response.metadata and "relationship" in response.metadata:
            rel_data = response.metadata["relationship"]
            relationship.affection_level = rel_data.get("affection_level", relationship.affection_level)
        
        final_response = response
        yield response, relationship
    
    # Record interaction after streaming completes
    if final_response and final_response.reasoning == "final":
        interaction = Interaction(
            interaction_id=str(uuid4()),
            interaction_type=InteractionType.CHAT,
            content=f"User: {message}",
            timestamp=datetime.now(timezone.utc),
            affection_change=0.5,
            user_message=message,
            waifu_response=final_response.message,
        )
        relationship.add_interaction(interaction)
        
        # Persist updated relationship and interaction
        await waifu_repository.update_relationship(relationship)
        await waifu_repository.save_interaction(user_id, waifu_id, interaction)


async def give_gift_to_waifu(
    waifu_repository: AbstractWaifuRepository,
    waifu_id: str,
    user_id: str,
    gift_name: str,
    gift_description: str,
    relationship: Relationship,
) -> tuple[str, Relationship]:
    """
    Give a gift to a waifu and update relationship.
    
    This use case handles gift-giving interactions, which can
    significantly boost affection levels.
    
    Args:
        waifu_id: Waifu identifier
        user_id: User identifier
        gift_name: Name of the gift
        gift_description: Description of the gift
        relationship: Current relationship state
        
    Returns:
        Tuple of (reaction message, updated Relationship)
    """
    # Calculate affection boost based on gift
    # In a real implementation, this would use the waifu's preferences
    affection_boost = 5.0  # Base boost for gifts
    
    # Create interaction record
    interaction = Interaction(
        interaction_id=str(uuid4()),
        interaction_type=InteractionType.GIFT,
        content=f"Gift: {gift_name} - {gift_description}",
        timestamp=datetime.now(timezone.utc),
        affection_change=affection_boost,
        metadata={"gift_name": gift_name, "gift_description": gift_description},
    )
    
    relationship.add_interaction(interaction)
    
    # Persist updated relationship and interaction
    await waifu_repository.update_relationship(relationship)
    await waifu_repository.save_interaction(user_id, waifu_id, interaction)
    
    # Generate reaction based on relationship stage
    reactions = {
        "stranger": f"Oh, a gift? That's... unexpected. Thank you, I guess.",
        "acquaintance": f"A {gift_name}? That's thoughtful of you. Thank you!",
        "friend": f"You got me a {gift_name}! You remembered! Thank you so much!",
        "close_friend": f"Aww, you're so sweet! I love the {gift_name}! *hugs*",
        "romantic": f"You always know what I like! The {gift_name} is perfect! I'm so lucky to have you! ❤️",
        "soulmate": f"My love, you spoil me too much! But I absolutely adore this {gift_name}! You mean everything to me! 💕",
    }
    
    reaction = reactions.get(
        relationship.relationship_stage.value,
        "Thank you for the gift!"
    )
    
    return reaction, relationship


async def update_waifu_configuration(
    llm_factory: ILLMFactory,
    waifu_id: str,
    updated_config: WaifuConfiguration,
) -> None:
    """
    Update a waifu's configuration.
    
    This use case handles updating waifu settings, including
    personality adjustments and appearance changes.
    
    Args:
        llm_factory: Factory interface for creating LLM clients
        waifu_id: Waifu identifier
        updated_config: New configuration
    """
    client = llm_factory.create_client("langgraph")
    client.update_agent(waifu_id, updated_config)


async def get_relationship_summary(
    relationship: Relationship,
) -> Dict[str, Any]:
    """
    Get a summary of the relationship state.
    
    This use case provides analytics about the relationship,
    useful for displaying relationship status to users.
    
    Args:
        relationship: Relationship to summarize
        
    Returns:
        Dictionary with relationship summary (type-safe)
    """
    # Calculate days since first interaction (type-safe)
    days_since_first = 0
    if relationship.created_at:
        days_since_first = (datetime.now(timezone.utc) - relationship.created_at).days
    
    # Calculate days since last interaction (type-safe with Optional)
    days_since_last: Optional[int] = None
    if relationship.last_interaction:
        days_since_last = (datetime.now(timezone.utc) - relationship.last_interaction).days
    
    # Get recent interactions safely (handle empty list)
    recent_interactions_data: List[Dict[str, Any]] = []
    if relationship.interactions_history:
        recent_interactions_data = [
            {
                "type": i.interaction_type.value,
                "timestamp": i.timestamp.isoformat(),
                "affection_change": i.affection_change,
            }
            for i in relationship.interactions_history[-5:]
        ]
    
    return {
        "affection_level": relationship.affection_level,
        "relationship_stage": relationship.relationship_stage.value,
        "interaction_count": relationship.interaction_count,
        "days_since_first_interaction": days_since_first,
        "days_since_last_interaction": days_since_last,
        "recent_interactions": recent_interactions_data,
        "special_moments": relationship.special_moments,
    }

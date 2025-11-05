"""
Mappers between Waifu domain models and ORM models.

These mappers handle the translation between domain entities
and database representations, following the Data Mapper pattern.

Note: We use TYPE_CHECKING and cast() to handle SQLAlchemy's descriptor magic.
At runtime, ORM attributes return actual values (str, int, etc.), but the type
checker sees Column[T]. This is a known SQLAlchemy limitation with declarative_base.
"""

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional, cast

from models.ai_agent.waifu import (
    Waifu,
    WaifuConfiguration,
    WaifuPersonality,
    WaifuAppearance,
    Relationship,
    RelationshipStage,
    Interaction,
    InteractionType,
)
from models.ai_agent.ai_agent import AgentProvider

from .orm import WaifuORM, RelationshipORM, InteractionORM


class WaifuOrmMapper:
    """Mapper for Waifu domain entity <-> ORM model."""
    
    @staticmethod
    def orm_to_entity(orm_waifu: WaifuORM) -> Waifu:
        """
        Convert ORM model to domain entity.
        
        Note: SQLAlchemy descriptors return actual values at runtime, not Column objects.
        We use cast() to inform the type checker of the correct runtime types.
        """
        # Deserialize JSON fields
        configuration_data = json.loads(cast(str, orm_waifu.configuration_json))
        appearance_data = json.loads(cast(str, orm_waifu.appearance_json))
        personality_data = json.loads(cast(str, orm_waifu.personality_json))
        
        # Reconstruct domain objects
        personality = WaifuPersonality(**personality_data)
        appearance = WaifuAppearance(**appearance_data)
        
        # Create configuration (handling nested personality)
        configuration = WaifuConfiguration(
            provider=AgentProvider(configuration_data.get("provider", "langgraph")),
            model_name=configuration_data["model_name"],
            personality=personality,
            appearance=appearance,
            system_prompt=configuration_data.get("system_prompt", ""),
            temperature=configuration_data.get("temperature", 0.8),
            max_tokens=configuration_data.get("max_tokens", 2000),
            tools=configuration_data.get("tools", []),
            enable_relationship_tracking=configuration_data.get("enable_relationship_tracking", True),
            enable_memory=configuration_data.get("enable_memory", True),
            max_memory_items=configuration_data.get("max_memory_items", 50),
            affection_sensitivity=configuration_data.get("affection_sensitivity", 1.0),
        )
        
        # Cast ORM attributes to their runtime types for type safety
        created_at = cast(datetime, orm_waifu.created_at)
        updated_at = cast(datetime, orm_waifu.updated_at)
        
        return Waifu(
            id=cast(str, orm_waifu.id),
            name=cast(str, orm_waifu.name),
            configuration=configuration,
            appearance=appearance,
            personality=personality,
            current_mood=cast(str, orm_waifu.current_mood),
            energy_level=float(cast(Decimal, orm_waifu.energy_level)),
            created_at=created_at.replace(tzinfo=timezone.utc) if created_at is not None else datetime.now(timezone.utc),
            updated_at=updated_at.replace(tzinfo=timezone.utc) if updated_at is not None else datetime.now(timezone.utc),
            is_active=cast(bool, orm_waifu.is_active),
            total_interactions=cast(int, orm_waifu.total_interactions),
            total_users=cast(int, orm_waifu.total_users),
        )
    
    @staticmethod
    def entity_to_orm(waifu: Waifu) -> WaifuORM:
        """Convert domain entity to ORM model."""
        # Serialize complex objects to JSON
        configuration_json = json.dumps({
            "provider": waifu.configuration.provider.value,
            "model_name": waifu.configuration.model_name,
            "system_prompt": waifu.configuration.system_prompt,
            "temperature": waifu.configuration.temperature,
            "max_tokens": waifu.configuration.max_tokens,
            "tools": waifu.configuration.tools,
            "enable_relationship_tracking": waifu.configuration.enable_relationship_tracking,
            "enable_memory": waifu.configuration.enable_memory,
            "max_memory_items": waifu.configuration.max_memory_items,
            "affection_sensitivity": waifu.configuration.affection_sensitivity,
        })
        
        appearance_json = waifu.appearance.model_dump_json()
        personality_json = waifu.personality.model_dump_json()
        
        return WaifuORM(
            id=waifu.id,
            name=waifu.name,
            configuration_json=configuration_json,
            appearance_json=appearance_json,
            personality_json=personality_json,
            current_mood=waifu.current_mood,
            energy_level=Decimal(str(waifu.energy_level)),
            created_at=waifu.created_at,
            updated_at=waifu.updated_at,
            is_active=waifu.is_active,
            total_interactions=waifu.total_interactions,
            total_users=waifu.total_users,
        )


class RelationshipOrmMapper:
    """Mapper for Relationship domain entity <-> ORM model."""
    
    @staticmethod
    def orm_to_entity(orm_relationship: RelationshipORM, interactions: Optional[List[Interaction]] = None) -> Relationship:
        """
        Convert ORM model to domain entity.
        
        Note: Using cast() for type-safe access to SQLAlchemy ORM attributes.
        """
        special_moments = json.loads(cast(str, orm_relationship.special_moments_json))
        
        # Cast datetime fields for proper type handling
        last_interaction = cast(Optional[datetime], orm_relationship.last_interaction)
        created_at = cast(datetime, orm_relationship.created_at)
        updated_at = cast(datetime, orm_relationship.updated_at)
        
        return Relationship(
            user_id=cast(str, orm_relationship.user_id),
            waifu_id=cast(str, orm_relationship.waifu_id),
            affection_level=float(cast(Decimal, orm_relationship.affection_level)),
            relationship_stage=RelationshipStage(cast(str, orm_relationship.relationship_stage)),
            interaction_count=cast(int, orm_relationship.interaction_count),
            last_interaction=(
                last_interaction.replace(tzinfo=timezone.utc)
                if last_interaction is not None else None
            ),
            created_at=created_at.replace(tzinfo=timezone.utc) if created_at is not None else datetime.now(timezone.utc),
            updated_at=updated_at.replace(tzinfo=timezone.utc) if updated_at is not None else datetime.now(timezone.utc),
            interactions_history=interactions or [],
            special_moments=special_moments,
            relationship_notes=cast(str, orm_relationship.relationship_notes),
        )
    
    @staticmethod
    def entity_to_orm(relationship: Relationship) -> RelationshipORM:
        """Convert domain entity to ORM model."""
        return RelationshipORM(
            user_id=relationship.user_id,
            waifu_id=relationship.waifu_id,
            affection_level=Decimal(str(relationship.affection_level)),
            relationship_stage=relationship.relationship_stage.value,
            interaction_count=relationship.interaction_count,
            last_interaction=relationship.last_interaction,
            created_at=relationship.created_at,
            updated_at=relationship.updated_at,
            special_moments_json=json.dumps(relationship.special_moments),
            relationship_notes=relationship.relationship_notes,
        )


class InteractionOrmMapper:
    """Mapper for Interaction domain entity <-> ORM model."""
    
    @staticmethod
    def orm_to_entity(orm_interaction: InteractionORM) -> Interaction:
        """
        Convert ORM model to domain entity.
        
        Note: Using cast() for type-safe access to SQLAlchemy ORM attributes.
        """
        metadata = json.loads(cast(str, orm_interaction.metadata_json))
        timestamp = cast(datetime, orm_interaction.timestamp)
        
        return Interaction(
            interaction_id=cast(str, orm_interaction.interaction_id),
            interaction_type=InteractionType(cast(str, orm_interaction.interaction_type)),
            content=cast(str, orm_interaction.content),
            timestamp=timestamp.replace(tzinfo=timezone.utc) if timestamp is not None else datetime.now(timezone.utc),
            affection_change=float(cast(Decimal, orm_interaction.affection_change)),
            user_message=cast(Optional[str], orm_interaction.user_message),
            waifu_response=cast(Optional[str], orm_interaction.waifu_response),
            metadata=metadata,
        )
    
    @staticmethod
    def entity_to_orm(interaction: Interaction, user_id: str, waifu_id: str) -> InteractionORM:
        """Convert domain entity to ORM model."""
        return InteractionORM(
            interaction_id=interaction.interaction_id,
            user_id=user_id,
            waifu_id=waifu_id,
            interaction_type=interaction.interaction_type.value,
            content=interaction.content,
            timestamp=interaction.timestamp,
            affection_change=Decimal(str(interaction.affection_change)),
            user_message=interaction.user_message,
            waifu_response=interaction.waifu_response,
            metadata_json=json.dumps(interaction.metadata),
        )

"""
Relational Database Waifu Repository Implementation.

This module provides the concrete repository implementation for Waifu entities
using SQLAlchemy, following Clean Architecture and Repository Pattern.

Note: We use cast() to handle SQLAlchemy's descriptor typing for type safety.
"""

from typing import List, Optional, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, delete
from sqlalchemy.orm import selectinload

from models.ai_agent.waifu import Waifu, Relationship, Interaction
from repositories.abstraction.waifu import AbstractWaifuRepository

from .mapper import WaifuOrmMapper, RelationshipOrmMapper, InteractionOrmMapper
from .orm import WaifuORM, RelationshipORM, InteractionORM


class RelationalDBWaifuRepository(AbstractWaifuRepository):
    """Relational database repository for Waifu entities using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session

    # Waifu CRUD operations
    async def save_waifu(self, waifu: Waifu) -> str:
        """Save a waifu entity."""
        orm_waifu = WaifuOrmMapper.entity_to_orm(waifu)
        self.session.add(orm_waifu)
        await self.session.commit()
        await self.session.refresh(orm_waifu)
        return cast(str, orm_waifu.id)

    async def get_waifu(self, waifu_id: str) -> Optional[Waifu]:
        """Get a waifu by ID."""
        stmt = select(WaifuORM).where(WaifuORM.id == waifu_id)
        result = await self.session.execute(stmt)
        orm_waifu = result.scalar_one_or_none()

        if not orm_waifu:
            return None

        return WaifuOrmMapper.orm_to_entity(orm_waifu)

    async def update_waifu(self, waifu: Waifu) -> bool:
        """Update a waifu entity."""
        stmt = select(WaifuORM).where(WaifuORM.id == waifu.id)
        result = await self.session.execute(stmt)
        orm_waifu = result.scalar_one_or_none()

        if not orm_waifu:
            return False

        # Update ORM object with new values
        updated_orm = WaifuOrmMapper.entity_to_orm(waifu)
        orm_waifu.name = updated_orm.name
        orm_waifu.configuration_json = updated_orm.configuration_json
        orm_waifu.appearance_json = updated_orm.appearance_json
        orm_waifu.personality_json = updated_orm.personality_json
        orm_waifu.current_mood = updated_orm.current_mood
        orm_waifu.energy_level = updated_orm.energy_level
        orm_waifu.is_active = updated_orm.is_active
        orm_waifu.total_interactions = updated_orm.total_interactions
        orm_waifu.total_users = updated_orm.total_users
        orm_waifu.updated_at = updated_orm.updated_at

        await self.session.commit()
        return True

    async def delete_waifu(self, waifu_id: str) -> bool:
        """Delete a waifu by ID."""
        stmt = select(WaifuORM).where(WaifuORM.id == waifu_id)
        result = await self.session.execute(stmt)
        orm_waifu = result.scalar_one_or_none()

        if not orm_waifu:
            return False

        await self.session.delete(orm_waifu)
        await self.session.commit()
        return True

    async def list_waifus(self, limit: int = 50, offset: int = 0) -> List[Waifu]:
        """List all waifus with pagination."""
        stmt = select(WaifuORM).limit(limit).offset(offset).order_by(WaifuORM.created_at.desc())
        result = await self.session.execute(stmt)
        orm_waifus = result.scalars().all()

        return [WaifuOrmMapper.orm_to_entity(orm_waifu) for orm_waifu in orm_waifus]

    # Relationship CRUD operations
    async def save_relationship(self, relationship: Relationship) -> str:
        """Save a relationship entity."""
        orm_relationship = RelationshipOrmMapper.entity_to_orm(relationship)
        
        # Check if relationship already exists (upsert behavior)
        stmt = select(RelationshipORM).where(
            RelationshipORM.user_id == relationship.user_id,
            RelationshipORM.waifu_id == relationship.waifu_id
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing relationship
            existing.affection_level = orm_relationship.affection_level
            existing.relationship_stage = orm_relationship.relationship_stage
            existing.interaction_count = orm_relationship.interaction_count
            existing.last_interaction = orm_relationship.last_interaction
            existing.updated_at = orm_relationship.updated_at
            existing.special_moments_json = orm_relationship.special_moments_json
            existing.relationship_notes = orm_relationship.relationship_notes
        else:
            # Create new relationship
            self.session.add(orm_relationship)
        
        await self.session.commit()
        return f"{relationship.user_id}:{relationship.waifu_id}"

    async def get_relationship(
        self, user_id: str, waifu_id: str
    ) -> Optional[Relationship]:
        """Get a relationship by user and waifu IDs."""
        stmt = (
            select(RelationshipORM)
            .options(selectinload(RelationshipORM.interactions))
            .where(
                RelationshipORM.user_id == user_id,
                RelationshipORM.waifu_id == waifu_id
            )
        )
        result = await self.session.execute(stmt)
        orm_relationship = result.scalar_one_or_none()

        if not orm_relationship:
            return None

        # Load interactions (recent 100)
        interactions = [
            InteractionOrmMapper.orm_to_entity(orm_interaction)
            for orm_interaction in orm_relationship.interactions[-100:]
        ]

        return RelationshipOrmMapper.orm_to_entity(orm_relationship, interactions)

    async def update_relationship(self, relationship: Relationship) -> bool:
        """Update a relationship entity."""
        stmt = select(RelationshipORM).where(
            RelationshipORM.user_id == relationship.user_id,
            RelationshipORM.waifu_id == relationship.waifu_id
        )
        result = await self.session.execute(stmt)
        orm_relationship = result.scalar_one_or_none()

        if not orm_relationship:
            return False

        # Update ORM object
        updated_orm = RelationshipOrmMapper.entity_to_orm(relationship)
        orm_relationship.affection_level = updated_orm.affection_level
        orm_relationship.relationship_stage = updated_orm.relationship_stage
        orm_relationship.interaction_count = updated_orm.interaction_count
        orm_relationship.last_interaction = updated_orm.last_interaction
        orm_relationship.updated_at = updated_orm.updated_at
        orm_relationship.special_moments_json = updated_orm.special_moments_json
        orm_relationship.relationship_notes = updated_orm.relationship_notes

        await self.session.commit()
        return True

    async def delete_relationship(self, user_id: str, waifu_id: str) -> bool:
        """Delete a relationship."""
        stmt = select(RelationshipORM).where(
            RelationshipORM.user_id == user_id,
            RelationshipORM.waifu_id == waifu_id
        )
        result = await self.session.execute(stmt)
        orm_relationship = result.scalar_one_or_none()

        if not orm_relationship:
            return False

        await self.session.delete(orm_relationship)
        await self.session.commit()
        return True

    async def list_user_relationships(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Relationship]:
        """List all relationships for a user."""
        stmt = (
            select(RelationshipORM)
            .where(RelationshipORM.user_id == user_id)
            .limit(limit)
            .offset(offset)
            .order_by(RelationshipORM.last_interaction.desc())
        )
        result = await self.session.execute(stmt)
        orm_relationships = result.scalars().all()

        return [
            RelationshipOrmMapper.orm_to_entity(orm_rel)
            for orm_rel in orm_relationships
        ]

    async def list_waifu_relationships(
        self, waifu_id: str, limit: int = 50, offset: int = 0
    ) -> List[Relationship]:
        """List all relationships for a waifu."""
        stmt = (
            select(RelationshipORM)
            .where(RelationshipORM.waifu_id == waifu_id)
            .limit(limit)
            .offset(offset)
            .order_by(RelationshipORM.last_interaction.desc())
        )
        result = await self.session.execute(stmt)
        orm_relationships = result.scalars().all()

        return [
            RelationshipOrmMapper.orm_to_entity(orm_rel)
            for orm_rel in orm_relationships
        ]

    # Interaction operations
    async def save_interaction(
        self, user_id: str, waifu_id: str, interaction: Interaction
    ) -> str:
        """Save an interaction to a relationship."""
        orm_interaction = InteractionOrmMapper.entity_to_orm(interaction, user_id, waifu_id)
        self.session.add(orm_interaction)
        await self.session.commit()
        await self.session.refresh(orm_interaction)
        return cast(str, orm_interaction.interaction_id)

    async def get_interaction_history(
        self, user_id: str, waifu_id: str, limit: int = 100, offset: int = 0
    ) -> List[Interaction]:
        """Get interaction history for a relationship."""
        stmt = (
            select(InteractionORM)
            .where(
                InteractionORM.user_id == user_id,
                InteractionORM.waifu_id == waifu_id
            )
            .limit(limit)
            .offset(offset)
            .order_by(InteractionORM.timestamp.desc())
        )
        result = await self.session.execute(stmt)
        orm_interactions = result.scalars().all()

        return [
            InteractionOrmMapper.orm_to_entity(orm_interaction)
            for orm_interaction in orm_interactions
        ]

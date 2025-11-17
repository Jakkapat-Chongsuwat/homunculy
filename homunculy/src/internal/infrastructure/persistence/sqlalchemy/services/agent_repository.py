"""SQLAlchemy Agent Repository Implementation."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.entities import (
    Agent,
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
    AgentStatus,
)
from internal.domain.repositories import AgentRepository

from ..models import AgentModel


class SQLAlchemyAgentRepository(AgentRepository):
    """SQLAlchemy implementation of the agent repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_domain(self, model: AgentModel) -> Agent:
        config_dict: dict = model.configuration  # type: ignore[assignment]

        personality = AgentPersonality(
            name=str(config_dict["personality"]["name"]),
            description=str(config_dict["personality"]["description"]),
            traits=dict(config_dict["personality"].get("traits", {})),
            mood=str(config_dict["personality"].get("mood", "neutral")),
        )

        configuration = AgentConfiguration(
            provider=AgentProvider(config_dict["provider"]),
            model_name=str(config_dict["model_name"]),
            personality=personality,
            system_prompt=str(config_dict.get("system_prompt", "")),
            temperature=float(config_dict.get("temperature", 0.7)),
            max_tokens=int(config_dict.get("max_tokens", 2000)),
        )

        return Agent(
            id=str(model.id),  # type: ignore[arg-type]
            name=str(model.name),  # type: ignore[arg-type]
            configuration=configuration,
            status=AgentStatus(model.status),  # type: ignore[arg-type]
            is_active=bool(model.is_active),  # type: ignore[arg-type]
            created_at=model.created_at,  # type: ignore[arg-type]
            updated_at=model.updated_at,  # type: ignore[arg-type]
        )

    def _to_model(self, agent: Agent) -> dict:
        return {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status.value,
            "is_active": agent.is_active,
            "configuration": {
                "provider": agent.configuration.provider.value,
                "model_name": agent.configuration.model_name,
                "personality": {
                    "name": agent.configuration.personality.name,
                    "description": agent.configuration.personality.description,
                    "traits": agent.configuration.personality.traits,
                    "mood": agent.configuration.personality.mood,
                },
                "system_prompt": agent.configuration.system_prompt,
                "temperature": agent.configuration.temperature,
                "max_tokens": agent.configuration.max_tokens,
            },
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
        }

    async def create(self, agent: Agent) -> Agent:
        model_dict = self._to_model(agent)
        model = AgentModel(**model_dict)
        self.session.add(model)
        await self.session.flush()
        return agent

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        result = await self.session.execute(
            select(AgentModel).where(AgentModel.id == agent_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, agent: Agent) -> Agent:
        result = await self.session.execute(
            select(AgentModel).where(AgentModel.id == agent.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Agent {agent.id} not found")

        model_dict = self._to_model(agent)
        for key, value in model_dict.items():
            if key != "id":
                setattr(model, key, value)

        await self.session.flush()
        return agent

    async def delete(self, agent_id: str) -> bool:
        result = await self.session.execute(
            select(AgentModel).where(AgentModel.id == agent_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True

    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        result = await self.session.execute(
            select(AgentModel).limit(limit).offset(offset)
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update_configuration(
        self, agent_id: str, configuration: AgentConfiguration
    ) -> bool:
        agent = await self.get_by_id(agent_id)
        if not agent:
            return False

        agent.configuration = configuration
        await self.update(agent)
        return True

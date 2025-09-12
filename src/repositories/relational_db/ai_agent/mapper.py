import json
from datetime import datetime

from common.docstring import MAPPER_DOCSTRING
from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentThread,
)

from .orm import AgentConfiguration as AgentConfigurationOrm, AgentPersonality as AgentPersonalityOrm, AgentThread as AgentThreadOrm

__doc__ = MAPPER_DOCSTRING


class AgentConfigurationOrmMapper:
    @staticmethod
    def orm_to_entity(orm_config: AgentConfigurationOrm) -> AgentConfiguration:
        personality_data = json.loads(orm_config.personality_json)
        personality = AgentPersonality(**personality_data)

        return AgentConfiguration(
            provider=AgentProvider(orm_config.provider),
            model_name=orm_config.model_name,
            personality=personality,
            system_prompt=orm_config.system_prompt,
            temperature=float(orm_config.temperature),
            max_tokens=orm_config.max_tokens,
            tools=json.loads(orm_config.tools_json),
        )

    @staticmethod
    def entity_to_orm(entity_config: AgentConfiguration, agent_id: str) -> AgentConfigurationOrm:
        return AgentConfigurationOrm(
            id=agent_id,
            provider=entity_config.provider.value,
            model_name=entity_config.model_name,
            personality_json=entity_config.personality.model_dump_json(),
            system_prompt=entity_config.system_prompt,
            temperature=str(entity_config.temperature),
            max_tokens=entity_config.max_tokens,
            tools_json=json.dumps(entity_config.tools),
        )


class AgentThreadOrmMapper:
    @staticmethod
    def orm_to_entity(orm_thread: AgentThreadOrm) -> AgentThread:
        messages_data = json.loads(orm_thread.messages_json)
        messages = [
            AgentMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata"),
            )
            for msg_data in messages_data
        ]

        return AgentThread(
            id=orm_thread.id,
            agent_id=orm_thread.agent_id,
            messages=messages,
            created_at=orm_thread.created_at,
            updated_at=orm_thread.updated_at,
            metadata=json.loads(orm_thread.metadata_json),
        )

    @staticmethod
    def entity_to_orm(entity_thread: AgentThread) -> AgentThreadOrm:
        messages_data = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata or {},
            }
            for msg in entity_thread.messages
        ]

        return AgentThreadOrm(
            id=entity_thread.id,
            agent_id=entity_thread.agent_id,
            messages_json=json.dumps(messages_data),
            metadata_json=json.dumps(entity_thread.metadata),
        )


class AgentPersonalityOrmMapper:
    @staticmethod
    def orm_to_entity(orm_personality: AgentPersonalityOrm) -> AgentPersonality:
        return AgentPersonality(
            name=orm_personality.name,
            description=orm_personality.description,
            traits=json.loads(orm_personality.traits_json),
            mood=orm_personality.mood,
            memory_context=orm_personality.memory_context,
        )

    @staticmethod
    def entity_to_orm(entity_personality: AgentPersonality, personality_id: str) -> AgentPersonalityOrm:
        return AgentPersonalityOrm(
            id=personality_id,
            name=entity_personality.name,
            description=entity_personality.description,
            traits_json=json.dumps(entity_personality.traits),
            mood=entity_personality.mood,
            memory_context=entity_personality.memory_context,
        )
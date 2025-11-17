--liquibase formatted sql

--changeset jakkapat:001-create-conversation-agents-table
--comment: Create table for storing conversation agent configurations (simple version)
CREATE TABLE conversation_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('openai', 'pydantic_ai', 'langraph')),
    model VARCHAR(100) NOT NULL,
    temperature DECIMAL(3, 2) NOT NULL DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),
    system_message TEXT,
    max_tokens INTEGER NOT NULL DEFAULT 1000,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_agents_provider ON conversation_agents(provider);
CREATE INDEX idx_conversation_agents_is_active ON conversation_agents(is_active);
--rollback DROP TABLE conversation_agents;

--changeset jakkapat:002-create-conversation-sessions-table
--comment: Create table for multi-turn conversation sessions
CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_id UUID NOT NULL REFERENCES conversation_agents(id) ON DELETE CASCADE,
    title VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX idx_sessions_agent_id ON conversation_sessions(agent_id);
CREATE INDEX idx_sessions_is_active ON conversation_sessions(is_active);
CREATE INDEX idx_sessions_started_at ON conversation_sessions(started_at);
--rollback DROP TABLE conversation_sessions;

--changeset jakkapat:003-create-messages-table
--comment: Create table for storing individual messages in conversations
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER,
    model VARCHAR(100),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_role ON messages(role);
--rollback DROP TABLE messages;

--changeset jakkapat:004-create-emotional-states-table
--comment: Create table for tracking user emotional states during conversations
CREATE TABLE emotional_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    emotion VARCHAR(50) NOT NULL,
    confidence DECIMAL(3, 2) CHECK (confidence >= 0 AND confidence <= 1),
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_emotional_states_session_id ON emotional_states(session_id);
CREATE INDEX idx_emotional_states_message_id ON emotional_states(message_id);
CREATE INDEX idx_emotional_states_emotion ON emotional_states(emotion);
--rollback DROP TABLE emotional_states;

--changeset jakkapat:005-create-context-data-table
--comment: Create table for storing session-specific context and memory
CREATE TABLE context_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, key)
);

CREATE INDEX idx_context_data_session_id ON context_data(session_id);
CREATE INDEX idx_context_data_key ON context_data(key);
CREATE INDEX idx_context_data_value ON context_data USING gin(value);
--rollback DROP TABLE context_data;

--changeset jakkapat:006-create-updated-at-trigger-function splitStatements:false
--comment: Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--rollback DROP FUNCTION update_updated_at_column();

--changeset jakkapat:007-create-updated-at-triggers
--comment: Create triggers for automatic updated_at updates
CREATE TRIGGER update_conversation_agents_updated_at BEFORE UPDATE ON conversation_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON conversation_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_context_data_updated_at BEFORE UPDATE ON context_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
--rollback DROP TRIGGER update_conversation_agents_updated_at ON conversation_agents;
--rollback DROP TRIGGER update_sessions_updated_at ON conversation_sessions;
--rollback DROP TRIGGER update_context_data_updated_at ON context_data;

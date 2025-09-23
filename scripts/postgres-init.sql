-- Homunculy AI Agent Database Initialization
-- This script creates all necessary tables for the AI agent system

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create AI Agent Configurations table
CREATE TABLE IF NOT EXISTS ai_agent_configurations (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    personality_json TEXT NOT NULL,
    system_prompt TEXT DEFAULT '',
    temperature VARCHAR(10) DEFAULT '0.7',
    max_tokens INTEGER NOT NULL DEFAULT 2000,
    tools_json TEXT DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create AI Agent Threads table
CREATE TABLE IF NOT EXISTS ai_agent_threads (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    agent_id VARCHAR(36) NOT NULL,
    messages_json TEXT DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT DEFAULT '{}'
);

-- Create AI Agent Personalities table
CREATE TABLE IF NOT EXISTS ai_agent_personalities (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    traits_json TEXT DEFAULT '{}',
    mood VARCHAR(50) DEFAULT 'neutral',
    memory_context TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ai_agent_configurations_provider ON ai_agent_configurations(provider);
CREATE INDEX IF NOT EXISTS idx_ai_agent_configurations_model_name ON ai_agent_configurations(model_name);
CREATE INDEX IF NOT EXISTS idx_ai_agent_threads_agent_id ON ai_agent_threads(agent_id);
CREATE INDEX IF NOT EXISTS idx_ai_agent_threads_created_at ON ai_agent_threads(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_agent_personalities_name ON ai_agent_personalities(name);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_ai_agent_configurations_updated_at
    BEFORE UPDATE ON ai_agent_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_agent_threads_updated_at
    BEFORE UPDATE ON ai_agent_threads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_agent_personalities_updated_at
    BEFORE UPDATE ON ai_agent_personalities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing
INSERT INTO ai_agent_personalities (name, description, traits_json, mood) VALUES
('Default Assistant', 'A helpful and friendly AI assistant', '{"helpful": 0.9, "creative": 0.7, "analytical": 0.8}', 'friendly'),
('Creative Writer', 'An imaginative and creative writing assistant', '{"creative": 0.95, "imaginative": 0.9, "artistic": 0.85}', 'inspired'),
('Technical Expert', 'A knowledgeable technical and programming assistant', '{"analytical": 0.95, "technical": 0.9, "precise": 0.85}', 'focused')
ON CONFLICT (id) DO NOTHING;

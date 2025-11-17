--liquibase formatted sql

--changeset homunculy:002-waifu-schema
--comment: Database schema for Waifu AI companion feature

-- Create Waifus table
CREATE TABLE waifus (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    -- Configuration (embedded JSON)
    configuration_json TEXT NOT NULL,
    -- Appearance (embedded JSON)
    appearance_json TEXT NOT NULL DEFAULT '{}',
    -- Personality (embedded JSON)
    personality_json TEXT NOT NULL,
    -- State
    current_mood VARCHAR(50) DEFAULT 'neutral',
    energy_level DECIMAL(5,2) DEFAULT 100.00 CHECK (energy_level >= 0 AND energy_level <= 100),
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    -- Statistics
    total_interactions INTEGER DEFAULT 0 CHECK (total_interactions >= 0),
    total_users INTEGER DEFAULT 0 CHECK (total_users >= 0)
);

-- Create Relationships table
CREATE TABLE relationships (
    user_id VARCHAR(36) NOT NULL,
    waifu_id VARCHAR(36) NOT NULL,
    affection_level DECIMAL(5,2) DEFAULT 0.00 CHECK (affection_level >= 0 AND affection_level <= 100),
    relationship_stage VARCHAR(20) DEFAULT 'stranger' CHECK (
        relationship_stage IN ('stranger', 'acquaintance', 'friend', 'close_friend', 'romantic', 'soulmate')
    ),
    interaction_count INTEGER DEFAULT 0 CHECK (interaction_count >= 0),
    last_interaction TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    special_moments_json TEXT DEFAULT '[]',
    relationship_notes TEXT DEFAULT '',
    PRIMARY KEY (user_id, waifu_id),
    CONSTRAINT fk_relationships_waifu FOREIGN KEY (waifu_id) 
        REFERENCES waifus(id) ON DELETE CASCADE
);

-- Create Interactions table
CREATE TABLE interactions (
    interaction_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    waifu_id VARCHAR(36) NOT NULL,
    interaction_type VARCHAR(20) NOT NULL CHECK (
        interaction_type IN ('chat', 'gift', 'date', 'compliment', 'activity', 'special_event')
    ),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    affection_change DECIMAL(5,2) DEFAULT 0.00,
    user_message TEXT,
    waifu_response TEXT,
    metadata_json TEXT DEFAULT '{}',
    CONSTRAINT fk_interactions_relationship FOREIGN KEY (user_id, waifu_id) 
        REFERENCES relationships(user_id, waifu_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_waifus_name ON waifus(name);
CREATE INDEX idx_waifus_is_active ON waifus(is_active);
CREATE INDEX idx_waifus_created_at ON waifus(created_at);

CREATE INDEX idx_relationships_user_id ON relationships(user_id);
CREATE INDEX idx_relationships_waifu_id ON relationships(waifu_id);
CREATE INDEX idx_relationships_relationship_stage ON relationships(relationship_stage);
CREATE INDEX idx_relationships_affection_level ON relationships(affection_level);
CREATE INDEX idx_relationships_last_interaction ON relationships(last_interaction);

CREATE INDEX idx_interactions_user_waifu ON interactions(user_id, waifu_id);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);
CREATE INDEX idx_interactions_type ON interactions(interaction_type);

-- Create trigger for waifus updated_at
CREATE TRIGGER update_waifus_updated_at
    BEFORE UPDATE ON waifus
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for relationships updated_at
CREATE TRIGGER update_relationships_updated_at
    BEFORE UPDATE ON relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE waifus IS 'AI companion waifus with personality and appearance';
COMMENT ON TABLE relationships IS 'User-Waifu relationships with affection tracking';
COMMENT ON TABLE interactions IS 'Interaction history between users and waifus';

COMMENT ON COLUMN waifus.configuration_json IS 'WaifuConfiguration serialized as JSON';
COMMENT ON COLUMN waifus.appearance_json IS 'WaifuAppearance serialized as JSON';
COMMENT ON COLUMN waifus.personality_json IS 'WaifuPersonality serialized as JSON';
COMMENT ON COLUMN waifus.energy_level IS 'Energy level (0-100) affects responsiveness';

COMMENT ON COLUMN relationships.affection_level IS 'Affection level (0-100) determines relationship stage';
COMMENT ON COLUMN relationships.special_moments_json IS 'Array of memorable moments';

COMMENT ON COLUMN interactions.affection_change IS 'Change in affection from this interaction';

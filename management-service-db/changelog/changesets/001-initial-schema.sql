--liquibase formatted sql

--changeset jakkapat:001-create-users-table
--comment: Create users table with subscription tiers
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(20) NOT NULL CHECK (subscription_tier IN ('free', 'premium', 'enterprise')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX idx_users_is_active ON users(is_active);
--rollback DROP TABLE users;

--changeset jakkapat:002-create-quotas-table
--comment: Create quotas table for user resource limits
CREATE TABLE quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL,
    max_agents INTEGER NOT NULL DEFAULT 1,
    max_tokens_per_day BIGINT NOT NULL,
    max_requests_per_day INTEGER NOT NULL,
    max_requests_per_minute INTEGER NOT NULL DEFAULT 10,
    used_tokens_today INTEGER NOT NULL DEFAULT 0,
    used_requests_today INTEGER NOT NULL DEFAULT 0,
    reset_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_quotas_user_id ON quotas(user_id);
CREATE INDEX idx_quotas_reset_date ON quotas(reset_date);
--rollback DROP TABLE quotas;

--changeset jakkapat:003-create-agent-assignments-table
--comment: Create agent assignments table for user-agent mapping
CREATE TABLE agent_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id_reference VARCHAR(255) NOT NULL,
    allocation_strategy VARCHAR(20) NOT NULL CHECK (allocation_strategy IN ('shared', 'dedicated', 'pool')),
    priority INTEGER NOT NULL DEFAULT 0,
    max_concurrent_requests INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, agent_id_reference)
);

CREATE INDEX idx_agent_assignments_user_id ON agent_assignments(user_id);
CREATE INDEX idx_agent_assignments_agent_id_reference ON agent_assignments(agent_id_reference);
CREATE INDEX idx_agent_assignments_allocation_strategy ON agent_assignments(allocation_strategy);
--rollback DROP TABLE agent_assignments;

--changeset jakkapat:004-create-usage-metrics-table
--comment: Create usage metrics table for billing and analytics
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id_reference VARCHAR(255) NOT NULL,
    tokens_used BIGINT NOT NULL,
    requests_count BIGINT NOT NULL DEFAULT 1,
    cost DECIMAL(10, 6) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_metrics_user_id ON usage_metrics(user_id);
CREATE INDEX idx_usage_metrics_agent_id_reference ON usage_metrics(agent_id_reference);
CREATE INDEX idx_usage_metrics_timestamp ON usage_metrics(timestamp);
CREATE INDEX idx_usage_metrics_user_timestamp ON usage_metrics(user_id, timestamp);
--rollback DROP TABLE usage_metrics;

--changeset jakkapat:005-create-updated-at-trigger-function splitStatements:false
--comment: Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--rollback DROP FUNCTION update_updated_at_column();

--changeset jakkapat:006-create-updated-at-triggers
--comment: Create triggers for automatic updated_at updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quotas_updated_at BEFORE UPDATE ON quotas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_assignments_updated_at BEFORE UPDATE ON agent_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
--rollback DROP TRIGGER update_users_updated_at ON users;
--rollback DROP TRIGGER update_quotas_updated_at ON quotas;
--rollback DROP TRIGGER update_agent_assignments_updated_at ON agent_assignments;

class PokemonError(Exception):
    pass


class PokemonNotFound(PokemonError):
    pass


class PokemonAlreadyExists(PokemonError):
    pass


class PokemonUnknownError(PokemonError):
    pass


class AIAgentError(Exception):
    """Base exception for AI agent related errors."""
    pass


class AgentNotFound(AIAgentError):
    """Raised when an agent is not found."""
    pass


class ThreadNotFound(AIAgentError):
    """Raised when a thread is not found."""
    pass


class PersonalityNotFound(AIAgentError):
    """Raised when a personality is not found."""
    pass


class AgentException(AIAgentError):
    """General agent exception."""
    pass

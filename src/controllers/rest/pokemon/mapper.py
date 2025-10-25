"""Pokemon feature removed: mapper placeholder.

The Pokemon feature has been removed from the codebase. This module is
kept as a placeholder to avoid import errors while other parts of the
project are adjusted. Any attempt to use the Pokemon mappers will raise
an explicit error.
"""


def _feature_removed(*args, **kwargs):
    raise RuntimeError("Pokemon feature removed: mapper not available")


class PokemonRequestMapper:
    create_request_to_entity = _feature_removed
    update_request_to_entity = _feature_removed


class PokemonResponseMapper:
    entity_to_response = _feature_removed


class TypeResponseMapper:
    entity_to_response = _feature_removed


class EvolutionResponseMapper:
    entity_to_response = _feature_removed

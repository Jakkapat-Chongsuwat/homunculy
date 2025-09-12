"""
Pokemon REST API Extensions.

This module provides utility functions to integrate FastAPI exception handlers with the application's
domain-specific exceptions for Pokemon operations.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from models.pokemon.exception import (
    PokemonAlreadyExists,
    PokemonError,
    PokemonNotFound,
    PokemonUnknownError,
)


def add_pokemon_exception_handlers(app: FastAPI):
    """Add exception handlers for Pokemon-related errors."""
    @app.exception_handler(PokemonError)
    @app.exception_handler(PokemonUnknownError)
    async def handle_general_pokemon_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(content={'error': f'{type(exc).__name__}: {exc}'}, status_code=400)

    @app.exception_handler(PokemonNotFound)
    async def handle_pokemon_not_found_error(_: Request, exc: PokemonNotFound) -> JSONResponse:
        return JSONResponse(content={'error': f'{type(exc).__name__}: {exc}'}, status_code=404)

    @app.exception_handler(PokemonAlreadyExists)
    async def handle_pokemon_already_exists_error(_: Request, exc: PokemonAlreadyExists) -> JSONResponse:
        return JSONResponse(content={'error': f'{type(exc).__name__}: {exc}'}, status_code=409)
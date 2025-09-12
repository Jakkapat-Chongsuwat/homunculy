from fastapi import APIRouter, Body, Path, status

from common.type import PokemonNumberStr
from di.dependency_injection import injector
from di.unit_of_work import AbstractPokemonUnitOfWork
from usecases import pokemon as pokemon_ucase

from .mapper import PokemonRequestMapper, PokemonResponseMapper
from .schema import CreatePokemonRequest, PokemonResponse, UpdatePokemonRequest

router = APIRouter()


@router.post('/pokemons', status_code=status.HTTP_201_CREATED)
async def create_pokemon(body: CreatePokemonRequest) -> PokemonResponse:
    pokemon_unit_of_work = injector.get(AbstractPokemonUnitOfWork)
    create_pokemon_data = PokemonRequestMapper.create_request_to_entity(body)
    created_pokemon = await pokemon_ucase.create_pokemon(pokemon_unit_of_work, create_pokemon_data)

    return PokemonResponseMapper.entity_to_response(created_pokemon)


@router.get('/pokemons/{no}')
async def get_pokemon(no: str = Path(..., description=PokemonNumberStr.__doc__)) -> PokemonResponse:
    pokemon_unit_of_work = injector.get(AbstractPokemonUnitOfWork)
    no = PokemonNumberStr(no)
    pokemon = await pokemon_ucase.get_pokemon(pokemon_unit_of_work, no)

    return PokemonResponseMapper.entity_to_response(pokemon)


@router.get('/pokemons')
async def get_pokemons() -> list[PokemonResponse]:
    pokemon_unit_of_work = injector.get(AbstractPokemonUnitOfWork)
    pokemons = await pokemon_ucase.get_pokemons(pokemon_unit_of_work)

    return list(map(PokemonResponseMapper.entity_to_response, pokemons))


@router.patch('/pokemons/{no}')
async def update_pokemon(
    no: str = Path(..., description=PokemonNumberStr.__doc__),
    body: UpdatePokemonRequest = Body(...),
) -> PokemonResponse:
    pokemon_unit_of_work = injector.get(AbstractPokemonUnitOfWork)
    no = PokemonNumberStr(no)
    update_pokemon_data = PokemonRequestMapper.update_request_to_entity(body)
    update_pokemon_data.validate_no_not_in_evolutions(no)
    updated_pokemon = await pokemon_ucase.update_pokemon(pokemon_unit_of_work, no, update_pokemon_data)  # fmt: skip

    return PokemonResponseMapper.entity_to_response(updated_pokemon)


@router.delete('/pokemons/{no}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_pokemon(no: str = Path(..., description=PokemonNumberStr.__doc__)):
    pokemon_unit_of_work = injector.get(AbstractPokemonUnitOfWork)
    no = PokemonNumberStr(no)
    await pokemon_ucase.delete_pokemon(pokemon_unit_of_work, no)

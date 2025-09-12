from common.type import PokemonNumberStr
from di.unit_of_work import AbstractPokemonUnitOfWork
from models.pokemon.exception import PokemonNotFound
from models.pokemon.pokemon import CreatePokemonModel, PokemonModel, UpdatePokemonModel


async def create_pokemon(
    pokemon_unit_of_work: AbstractPokemonUnitOfWork, data: CreatePokemonModel
) -> PokemonModel:
    async with pokemon_unit_of_work as puow:
        no = await puow.pokemon_repo.create(data)
        await puow.pokemon_repo.replace_types(no, data.type_names)

        if data.previous_evolution_numbers:
            if not await puow.pokemon_repo.are_existed(data.previous_evolution_numbers):
                raise PokemonNotFound(data.previous_evolution_numbers)
            await puow.pokemon_repo.replace_previous_evolutions(no, data.previous_evolution_numbers)
        if data.next_evolution_numbers:
            if not await puow.pokemon_repo.are_existed(data.next_evolution_numbers):
                raise PokemonNotFound(data.next_evolution_numbers)
            await puow.pokemon_repo.replace_next_evolutions(no, data.next_evolution_numbers)

        puow.commit()  # Explicit commit like in the book
        return await puow.pokemon_repo.get(no)


async def get_pokemon(pokemon_unit_of_work: AbstractPokemonUnitOfWork, no: PokemonNumberStr) -> PokemonModel:
    async with pokemon_unit_of_work as puow:
        return await puow.pokemon_repo.get(no)


async def get_pokemons(pokemon_unit_of_work: AbstractPokemonUnitOfWork) -> list[PokemonModel]:
    async with pokemon_unit_of_work as puow:
        return await puow.pokemon_repo.list()


async def update_pokemon(
    pokemon_unit_of_work: AbstractPokemonUnitOfWork, no: PokemonNumberStr, data: UpdatePokemonModel
):
    async with pokemon_unit_of_work as puow:
        await puow.pokemon_repo.update(no, data)

        if data.type_names is not None:
            await puow.pokemon_repo.replace_types(no, data.type_names)

        if data.previous_evolution_numbers is not None:
            if not await puow.pokemon_repo.are_existed(data.previous_evolution_numbers):
                raise PokemonNotFound(data.previous_evolution_numbers)
            await puow.pokemon_repo.replace_previous_evolutions(no, data.previous_evolution_numbers)
        if data.next_evolution_numbers is not None:
            if not await puow.pokemon_repo.are_existed(data.next_evolution_numbers):
                raise PokemonNotFound(data.next_evolution_numbers)
            await puow.pokemon_repo.replace_next_evolutions(no, data.next_evolution_numbers)

        puow.commit()  # Explicit commit like in the book
        return await puow.pokemon_repo.get(no)


async def delete_pokemon(pokemon_unit_of_work: AbstractPokemonUnitOfWork, no: PokemonNumberStr):
    async with pokemon_unit_of_work as puow:
        await puow.pokemon_repo.delete(no)

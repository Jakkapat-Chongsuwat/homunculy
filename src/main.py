from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from controllers.graphql.extension import customize_graphql_openapi
from controllers.graphql.pokemon.router import router as pokemon_graphql_router
from controllers.rest.extension import add_exception_handlers as add_rest_exception_handlers
from controllers.rest.pokemon.router import router as pokemon_rest_router
from controllers.rest.ai_agent.router import router as ai_agent_rest_router
from settings import APP_NAME, APP_VERSION
from settings.db import IS_RELATIONAL_DB

# Import the appropriate database initialization function
if IS_RELATIONAL_DB:
    from settings.db import initialize_db
else:
    # For non-relational databases, initialize_db takes no arguments
    from settings.db import initialize_db  # type: ignore


# https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=redefined-outer-name
    # pylint: disable=import-outside-toplevel

    if IS_RELATIONAL_DB:
        from repositories.relational_db.pokemon.orm import Base as PokemonBase  # fmt: skip
        from repositories.relational_db.ai_agent.orm import Base as AIAgentBase  # fmt: skip
        
        # Initialize both Pokemon and AI Agent tables separately
        await initialize_db(PokemonBase)  # type: ignore
        await initialize_db(AIAgentBase)  # type: ignore
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# controllers/rest
app.include_router(pokemon_rest_router, tags=['REST'])
app.include_router(ai_agent_rest_router, tags=['AI Agent'])
add_rest_exception_handlers(app)

# controllers/graphql
app.include_router(pokemon_graphql_router, prefix='/graphql', tags=['GraphQL'])
customize_graphql_openapi(app)


@app.exception_handler(Exception)
async def universal_exception_handler(_, exc):
    return JSONResponse(content={'error': f'{type(exc).__name__}: {exc}'}, status_code=500)


@app.get('/', include_in_schema=False)
async def root():
    return JSONResponse({'service': APP_NAME, 'version': APP_VERSION})

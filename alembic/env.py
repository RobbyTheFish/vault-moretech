from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import pool
from alembic import context

from auth.db import Base
from auth.models import Role, Token

import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

POSTGRES_URI = os.getenv('POSTGRES_URI')
if POSTGRES_URI is None:
    raise ValueError("Missing env variable POSTGRES_URI")

config.set_main_option('sqlalchemy.url', POSTGRES_URI)

async_engine = create_async_engine(
    POSTGRES_URI,
    poolclass=pool.NullPool,
    future=True
)

def run_migrations_offline():
    """Запуск миграций в offline-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Запуск миграций в online-режиме."""
    async with async_engine.connect() as connection:
        # Вызов миграций в синхронном контексте
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection):
    """Функция для конфигурирования миграций в синхронном режиме."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
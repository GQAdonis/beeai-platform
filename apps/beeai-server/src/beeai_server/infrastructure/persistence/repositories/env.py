# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from cryptography.fernet import Fernet
from kink import inject
from sqlalchemy import Column, String, Table, Text
from sqlalchemy.ext.asyncio import AsyncConnection

from beeai_server.configuration import Configuration
from beeai_server.domain.repositories.env import NOT_SET, IEnvVariableRepository
from beeai_server.exceptions import EntityNotFoundError
from beeai_server.infrastructure.persistence.repositories.db_metadata import metadata

variables_table = Table(
    "variables",
    metadata,
    Column("key", String(256), primary_key=True),
    Column("value", Text, nullable=False),
)


@inject
class SqlAlchemyEnvVariableRepository(IEnvVariableRepository):
    def __init__(self, connection: AsyncConnection, configuration: Configuration):
        self.connection = connection
        if not configuration.persistence.encryption_key:
            raise RuntimeError("Missing encryption key in configuration.")

        self.fernet = Fernet(configuration.persistence.encryption_key.get_secret_value())

    async def update(self, variables: dict[str, str]) -> None:
        if not variables:
            return

        existing_keys = {row.key for row in (await self.connection.execute(variables_table.select())).all()}
        to_remove = [key for key, value in variables.items() if value is None or key in existing_keys]
        crypted = {key: self.fernet.encrypt(var.encode()).decode() for key, var in variables.items() if var is not None}
        await self.connection.execute(variables_table.delete().where(variables_table.c.key.in_(to_remove)))
        if crypted:
            await self.connection.execute(variables_table.insert().values(list(crypted.items())))

    async def get(self, *, key: str, default: str | None = NOT_SET) -> str:
        query = variables_table.select().where(variables_table.c.key == key)
        result = await self.connection.execute(query)
        if not (row := result.fetchone()):
            if default is NOT_SET:
                raise EntityNotFoundError(entity="variable", id=key)
            return default
        return self.fernet.decrypt(row.value).decode()

    async def get_all(self) -> dict[str, str]:
        rows = await self.connection.execute(variables_table.select())
        return {row.key: self.fernet.decrypt(row.value).decode() for row in rows.all()}

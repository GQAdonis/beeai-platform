# Copyright 2025 © BeeAI a Series of LF Projects, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import BinaryIO, AsyncIterator
from uuid import UUID, uuid4

from kink import inject

from beeai_server.domain.repositories.files import IObjectStorageRepository

logger = logging.getLogger(__name__)


@inject
class FileService:
    def __init__(self, object_storage_repository: IObjectStorageRepository):
        self.object_storage = object_storage_repository

    async def upload_file(self, file_content: BinaryIO, content_type: str) -> UUID:
        file_id = uuid4()

        try:
            await self.object_storage.upload_file(file_id, file_content, content_type)
            logger.info(f"File uploaded with ID: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    async def get_file(self, file_id: UUID) -> AsyncIterator[bytes]:
        try:
            async for chunk in self.object_storage.get_file(file_id):
                yield chunk
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {e}")
            raise

    async def delete_file(self, file_id: UUID) -> None:
        try:
            await self.object_storage.delete_file(file_id)
            logger.info(f"File deleted with ID: {file_id}")
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            raise

    async def get_file_url(self, file_id: UUID) -> str:
        try:
            url = await self.object_storage.get_file_url(file_id)
            return url
        except Exception as e:
            logger.error(f"Error getting URL for file {file_id}: {e}")
            raise

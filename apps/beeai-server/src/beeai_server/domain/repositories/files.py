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

from typing import runtime_checkable, Protocol, BinaryIO, AsyncIterator
from uuid import UUID


@runtime_checkable
class IObjectStorageRepository(Protocol):
    async def upload_file(self, file_id: UUID, file_content: BinaryIO, content_type: str) -> str: ...
    async def get_file(self, file_id: UUID) -> AsyncIterator[bytes]: ...
    async def delete_file(self, file_id: UUID) -> None: ...
    async def get_file_url(self, file_id: UUID) -> str: ...

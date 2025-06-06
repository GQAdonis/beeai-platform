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
from uuid import UUID

from fastapi import APIRouter, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse

from beeai_server.api.routes.dependencies import FileServiceDependency
from beeai_server.api.schema.files import FileUploadResponse, FileUrlResponse
from beeai_server.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, file_service: FileServiceDependency) -> FileUploadResponse:
    try:
        file_id = await file_service.upload_file(file.file, file.content_type)
        url = await file_service.get_file_url(file_id)
        return FileUploadResponse(file_id=file_id, url=url)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{file_id}")
async def get_file(file_id: UUID, file_service: FileServiceDependency) -> StreamingResponse:
    try:

        async def file_generator():
            async for chunk in file_service.get_file(file_id):
                yield chunk

        return StreamingResponse(
            file_generator(),
            media_type="application/octet-stream",  # Generic binary data
        )
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {file_id} not found")
    except Exception as e:
        logger.error(f"Error retrieving file {file_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{file_id}/url")
async def get_file_url(
    file_id: UUID,
    file_service: FileServiceDependency = None,
) -> FileUrlResponse:
    try:
        url = await file_service.get_file_url(file_id)
        return FileUrlResponse(url=url)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {file_id} not found")
    except Exception as e:
        logger.error(f"Error getting URL for file {file_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    file_service: FileServiceDependency = None,
) -> None:
    try:
        await file_service.delete_file(file_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {file_id} not found")
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useMemo, useState } from 'react';
import { type FileRejection, useDropzone } from 'react-dropzone';
import { v4 as uuid } from 'uuid';

import { useToast } from '#contexts/Toast/index.ts';

import { useDeleteFile } from '../api/mutations/useDeleteFile';
import { useUploadFile } from '../api/mutations/useUploadFile';
import { ALL_FILES_CONTENT_TYPE, MAX_FILE_SIZE, MAX_FILES, NO_FILES_CONTENT_TYPE } from '../constants';
import { type FileEntity, FileStatus } from '../types';
import { FileUploadContext } from './file-upload-context';

interface Props {
  allowedContentTypes: string[];
}

export function FileUploadProvider({ allowedContentTypes, children }: PropsWithChildren<Props>) {
  const [files, setFiles] = useState<FileEntity[]>([]);

  const { addToast } = useToast();
  const { mutateAsync: uploadFile } = useUploadFile({
    onMutate: ({ file: { id } }) => {
      setFiles((files) => files.map((file) => (file.id === id ? { ...file, status: FileStatus.Uploading } : file)));
    },
    onSuccess: (data, { file: { id } }) => {
      setFiles((files) =>
        files.map((file) => (file.id === id ? { ...file, status: FileStatus.Completed, uploadFile: data } : file)),
      );
    },
    onError: (error, { file: { id } }) => {
      setFiles((files) =>
        files.map((file) => (file.id === id ? { ...file, status: FileStatus.Failed, error: error.message } : file)),
      );
    },
  });
  const { mutateAsync: deleteFile } = useDeleteFile();

  const onDropAccepted = useCallback(
    async (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.map((file) => ({ id: uuid(), originalFile: file, status: FileStatus.Idle }));

      setFiles((files) => [...files, ...newFiles]);

      newFiles.forEach((file) => {
        uploadFile({ file });
      });
    },
    [uploadFile],
  );

  const onDropRejected = useCallback(
    (fileRejections: FileRejection[]) => {
      fileRejections.forEach(({ errors, file }) => {
        addToast({
          title: `File ${file.name} was rejected`,
          subtitle: errors.map(({ message }) => message).join('\n'),
          timeout: 5_000,
        });
      });
    },
    [addToast],
  );

  const clearFiles = useCallback(() => {
    setFiles([]);
  }, []);

  const removeFile = useCallback(
    (id: string) => {
      const uploadFileId = files.find((file) => file.id === id)?.uploadFile?.id;

      if (uploadFileId) {
        deleteFile({ file_id: uploadFileId });
      }

      setFiles((files) => files.filter((file) => file.id !== id));
    },
    [files, deleteFile],
  );

  const isPending = useMemo(
    () => files.some(({ status }) => status !== FileStatus.Completed && status !== FileStatus.Failed),
    [files],
  );

  const isDisabled = allowedContentTypes.includes(NO_FILES_CONTENT_TYPE) || !allowedContentTypes.length;
  const accept = isDisabled
    ? {}
    : allowedContentTypes.reduce(
        (value, mimeType) =>
          mimeType === ALL_FILES_CONTENT_TYPE
            ? value
            : {
                ...value,
                [mimeType]: [],
              },
        {} as Record<string, string[]>,
      );

  const dropzone = useDropzone({
    accept,
    disabled: isDisabled,
    noClick: true,
    noKeyboard: true,
    maxFiles: MAX_FILES,
    maxSize: MAX_FILE_SIZE,
    onDropAccepted,
    onDropRejected,
  });

  const contextValue = useMemo(
    () => ({
      files,
      isPending,
      isDisabled,
      dropzone,
      removeFile,
      clearFiles,
    }),
    [files, isPending, isDisabled, dropzone, removeFile, clearFiles],
  );

  return <FileUploadContext.Provider value={contextValue}>{children}</FileUploadContext.Provider>;
}

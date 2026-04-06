'use client';

import { useEffect, useState } from 'react';
import { getFiles, deleteFile } from '@/lib/api';
import { FileInfo } from '@/types';

export function FileList() {
  const [files, setFiles] = useState<FileInfo[]>([]);

  const loadFiles = async () => {
    const data = await getFiles();
    setFiles(data.files || []);
  };

  useEffect(() => {
    loadFiles();
    // Listen for upload completion events
    const handleFilesUpdated = () => loadFiles();
    window.addEventListener('files-updated', handleFilesUpdated);
    return () => window.removeEventListener('files-updated', handleFilesUpdated);
  }, []);

  const handleDelete = async (filename: string) => {
    if (!confirm(`确定删除文件 "${filename}" 吗？`)) return;
    await deleteFile(filename);
    loadFiles();
  };

  if (files.length === 0) {
    return <p className="text-sm text-gray-500">暂无文件</p>;
  }

  return (
    <div className="space-y-1">
      {files.map((file) => (
        <div
          key={file.id}
          className="group flex items-center justify-between p-2 rounded hover:bg-gray-50"
        >
          <span className="truncate text-sm" title={file.filename}>
            {file.filename}
          </span>
          <button
            onClick={() => handleDelete(file.filename)}
            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500"
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}

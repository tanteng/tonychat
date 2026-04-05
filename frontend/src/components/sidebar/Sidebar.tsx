'use client';

import { SessionList } from './SessionList';
import { FileList } from './FileList';
import { UploadArea } from './UploadArea';

export function Sidebar() {
  return (
    <aside className="w-80 border-r border-gray-200 flex flex-col bg-white">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-lg font-bold">TonyChat</h1>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-xs font-semibold text-gray-500 uppercase mb-2">上传文档</h2>
          <UploadArea />
        </div>

        <div className="p-4 border-t border-gray-100">
          <h2 className="text-xs font-semibold text-gray-500 uppercase mb-2">会话管理</h2>
          <SessionList />
        </div>

        <div className="p-4 border-t border-gray-100">
          <h2 className="text-xs font-semibold text-gray-500 uppercase mb-2">已上传文件</h2>
          <FileList />
        </div>
      </div>
    </aside>
  );
}

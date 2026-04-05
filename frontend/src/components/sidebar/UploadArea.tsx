'use client';

import { useState, useRef } from 'react';
import { uploadFiles, processFiles } from '@/lib/api';
import { ProgressBar } from '@/components/ui/ProgressBar';

export function UploadArea() {
  const [isDragging, setIsDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchProcessProgress = async (filenames: string[], onComplete: () => void) => {
    const response = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: filenames }),
    });

    if (!response.ok) throw new Error('处理失败');

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          try {
            const parsed = JSON.parse(data);
            if (parsed.error) {
              alert('处理失败: ' + parsed.error);
            } else if (parsed.stage === 'complete') {
              setProgress(100);
              setStatus('完成');
            } else if (parsed.progress) {
              setProgress(parsed.progress);
              setStatus(`${parsed.filename} - ${parsed.stage}`);
            }
          } catch {}
        }
      }
    }

    onComplete();
  };

  const handleFiles = async (files: FileList) => {
    if (files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          setProgress(pct);
          setStatus(`上传中 ${pct}%`);
        }
      };

      xhr.onload = async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText);
            if (result.files && result.files.length > 0) {
              setStatus('处理中...');
              await fetchProcessProgress(result.files, () => {
                setTimeout(() => {
                  setProgress(0);
                  setStatus('');
                }, 1500);
              });
            }
          } catch {}
          resolve();
        } else {
          reject(new Error('Upload failed'));
        }
      };

      xhr.onerror = () => reject(new Error('Network error'));

      xhr.open('POST', '/api/upload');
      xhr.send(formData);
    });
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
        isDragging
          ? 'border-gray-900 bg-gray-50'
          : 'border-gray-300 hover:border-gray-400'
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        multiple
        accept=".txt,.md,.pdf,.docx"
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
      />
      <p className="text-sm text-gray-600">点击或拖拽文件到此处</p>
      <p className="text-xs text-gray-400 mt-1">支持 .txt, .md, .pdf, .docx</p>

      {status && (
        <div className="mt-3">
          <ProgressBar progress={progress} />
          <p className="text-xs text-gray-500 mt-1">{status}</p>
        </div>
      )}
    </div>
  );
}

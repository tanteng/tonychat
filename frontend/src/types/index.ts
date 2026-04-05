export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface FileInfo {
  id: string;
  filename: string;
  file_type: string;
  uploaded_at: string;
  chunk_count: number;
}

export interface UploadResponse {
  success: boolean;
  files: string[];
  error?: string;
}

export interface ProgressEvent {
  filename: string;
  stage: 'loading' | 'parsing' | 'splitting' | 'vectorizing' | 'complete';
  progress: number;
  error?: string;
}

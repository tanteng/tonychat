const API_BASE = '/api';

export async function chat(message: string, sessionId: string, signal?: AbortSignal) {
  const response = await fetch(`/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });
  return response;
}

export async function getSessions() {
  try {
    const response = await fetch(`/api/sessions`);
    if (!response.ok) throw new Error('Failed to fetch sessions');
    return response.json();
  } catch (error) {
    throw error;
  }
}

export async function createSession() {
  try {
    const response = await fetch(`/api/sessions`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to create session');
    return response.json();
  } catch (error) {
    throw error;
  }
}

export async function deleteSession(sessionId: string) {
  try {
    const response = await fetch(`/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete session');
    return response.json();
  } catch (error) {
    throw error;
  }
}

export async function getSessionMessages(sessionId: string) {
  try {
    const response = await fetch(`/api/sessions/${sessionId}/messages`);
    if (!response.ok) throw new Error('Failed to fetch session messages');
    return response.json();
  } catch (error) {
    throw error;
  }
}

export async function getFiles() {
  try {
    const response = await fetch(`/api/files`);
    if (!response.ok) throw new Error('Failed to fetch files');
    return response.json();
  } catch (error) {
    throw error;
  }
}

export async function deleteFile(filename: string) {
  try {
    const response = await fetch(`/api/files/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete file');
    return response.json();
  } catch (error) {
    throw error;
  }
}

export async function uploadFiles(formData: FormData) {
  try {
    const response = await fetch(`/api/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload files');
    return response;
  } catch (error) {
    throw error;
  }
}

export async function processFiles(filenames: string[]) {
  try {
    const response = await fetch(`/api/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: filenames }),
    });
    if (!response.ok) throw new Error('Failed to process files');
    return response;
  } catch (error) {
    throw error;
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function chat(message: string, sessionId: string) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  return response;
}

export async function getSessions() {
  const response = await fetch(`${API_BASE}/sessions`);
  return response.json();
}

export async function createSession() {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
  });
  return response.json();
}

export async function deleteSession(sessionId: string) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  return response.json();
}

export async function getSessionMessages(sessionId: string) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
  return response.json();
}

export async function getFiles() {
  const response = await fetch(`${API_BASE}/files`);
  return response.json();
}

export async function deleteFile(filename: string) {
  const response = await fetch(`${API_BASE}/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  return response.json();
}

export async function uploadFiles(formData: FormData) {
  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  return response;
}

export async function processFiles(filenames: string[]) {
  const response = await fetch(`${API_BASE}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ files: filenames }),
  });
  return response;
}

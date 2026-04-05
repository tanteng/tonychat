import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const files = formData.getAll('files');

  const uploadFormData = new FormData();
  files.forEach((file) => {
    uploadFormData.append('files', file);
  });

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: uploadFormData,
  });

  if (!response.ok) {
    return Response.json({ error: 'Upload failed' }, { status: response.status });
  }

  const data = await response.json();
  return Response.json(data);
}

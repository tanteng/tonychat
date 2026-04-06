import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const response = await fetch(`${API_BASE}/sessions/${params.id}`, {
    method: 'DELETE',
  });
  const data = await response.json();
  const headers: HeadersInit = {};
  const requestId = response.headers.get('X-Request-ID');
  if (requestId) headers['X-Request-ID'] = requestId;
  if (!response.ok) {
    return Response.json({ error: 'Failed to delete session' }, { status: response.status, headers });
  }
  return Response.json(data, { headers });
}

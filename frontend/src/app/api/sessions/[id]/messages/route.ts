import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const response = await fetch(`${API_BASE}/sessions/${params.id}/messages`);
  if (!response.ok) {
    return Response.json({ error: 'Failed to fetch messages' }, { status: response.status });
  }
  const data = await response.json();
  return Response.json(data);
}

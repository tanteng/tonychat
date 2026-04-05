import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const response = await fetch(`${API_BASE}/sessions/${params.id}/messages`);
  const data = await response.json();
  return Response.json(data);
}

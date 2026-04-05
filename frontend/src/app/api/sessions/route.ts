import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function GET() {
  const response = await fetch(`${API_BASE}/sessions`);
  const data = await response.json();
  return Response.json(data);
}

export async function POST(req: NextRequest) {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
  });
  const data = await response.json();
  return Response.json(data, { status: 201 });
}

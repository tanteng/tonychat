import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function DELETE(
  req: NextRequest,
  { params }: { params: { filename: string } }
) {
  const response = await fetch(
    `${API_BASE}/files/${encodeURIComponent(params.filename)}`,
    { method: 'DELETE' }
  );
  const data = await response.json();
  return Response.json(data);
}

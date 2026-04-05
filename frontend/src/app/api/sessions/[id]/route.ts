import { NextRequest } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(`${API_BASE}/sessions/${params.id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete session');
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    throw error;
  }
}

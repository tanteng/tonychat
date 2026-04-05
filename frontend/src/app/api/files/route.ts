const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function GET() {
  const response = await fetch(`${API_BASE}/files`);
  const data = await response.json();
  return Response.json(data);
}

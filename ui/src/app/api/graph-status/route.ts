import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { uuid, auth } = body;

    if (!uuid) {
      return NextResponse.json(
        { error: 'UUID is required in the request body' },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/knowledge-graphs/status/${uuid}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error fetching graph status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch graph status' },
      { status: 500 }
    );
  }
}

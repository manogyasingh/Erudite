import { NextResponse } from 'next/server';
import { headers } from 'next/headers';

const BACKEND_URL = process.env.BACKEND_URL;

export async function GET() {
  try {
    // Get the authorization header from the incoming request
    const headersList = await headers();
    const token = headersList.get('authorization');

    if (!token) {
      return NextResponse.json(
        { error: 'Authorization token required' },
        { status: 401 }
      );
    }

    // Forward the request to the backend with the Bearer token
    const response = await fetch(`${BACKEND_URL}/knowledge-graphs/`, {
      method: 'GET',
      headers: {
        'Authorization': token,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error listing knowledge graphs:', error);
    return NextResponse.json(
      { error: 'Failed to list knowledge graphs' },
      { status: 500 }
    );
  }
}
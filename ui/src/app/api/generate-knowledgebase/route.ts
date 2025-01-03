import { NextResponse } from 'next/server';
import { headers } from 'next/headers';

const BACKEND_URL = process.env.BACKEND_URL;

export async function POST(request: Request) {
    try {
        const headersList = await headers();
        const token = headersList.get('authorization');

        if (!token) {
            return NextResponse.json(
                { error: 'Authorization token required' },
                { status: 401 }
            );
        }

        // Get user info
        const userResponse = await fetch(`${BACKEND_URL}/auth/me`, {
            headers: {
                'Authorization': token,
            },
        });

        if (!userResponse.ok) {
            return NextResponse.json(
                { error: 'Failed to get user info' },
                { status: userResponse.status }
            );
        }

        const userInfo = await userResponse.json();

        // Get the query from the request body
        const body = await request.json();

        if (!body.text) {
            return NextResponse.json(
                { error: 'Query is required' },
                { status: 400 }
            );
        }

        // Create the knowledge graph
        const response = await fetch(`${BACKEND_URL}/knowledge-graphs/`, {
            method: 'POST',
            headers: {
                'Authorization': token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: body.text,
                user_id: userInfo.id
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(error, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error creating knowledge graph:', error);
        return NextResponse.json(
            { error: 'Failed to create knowledge graph' },
            { status: 500 }
        );
    }
}
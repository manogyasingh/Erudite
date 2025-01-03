import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { action, username, password, email } = body;

    let response;

    if (action === 'login') {
      // Use form-data for login
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      response = await fetch(`${BACKEND_URL}/auth/token`, {
        method: 'POST',
        body: formData,
      });

    } else if (action === 'register') {
      // Use JSON body for register
      response = await fetch(`${BACKEND_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password, email }),
      });
    } else if (action === 'logout') {
      const logoutResponse = NextResponse.json(
        { message: 'Logout successful' },
        { status: 200 }
      );

      logoutResponse.cookies.delete('token');
      logoutResponse.cookies.delete('username');
      
      return logoutResponse;
    } else {
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
    }

    const data = await response.json();

    if (action === 'login' && data.access_token) {
      const loginResponse = NextResponse.json(
        { message: 'Login successful' },
        { status: 200 }
      );

      loginResponse.cookies.set({
        name: 'token',
        value: data.access_token,
        httpOnly: false,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });

      loginResponse.cookies.set({
        name: 'username',
        value: username,
        httpOnly: false, 
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7,
      });

      return loginResponse;
    } else if (action === 'register') {
      if (response.status === 400) {
        return NextResponse.json(
          { error: 'User already exists' },
          { status: 400 }
        );
      } else if (response.status === 200) {
        // Auto-login after registration
        const loginFormData = new FormData();
        loginFormData.append('username', username);
        loginFormData.append('password', password);

        const loginResponse = await fetch(`${BACKEND_URL}/auth/token`, {
          method: 'POST',
          body: loginFormData,
        });

        const loginData = await loginResponse.json();

        if (loginData.access_token) {
          const response = NextResponse.json(
            { message: 'Registration successful, and login successful' },
            { status: 200 }
          );

          response.cookies.set({
            name: 'token',
            value: loginData.access_token,
            httpOnly: false,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: 60 * 60 * 24 * 7,
          });

          response.cookies.set({
            name: 'username',
            value: username,
            httpOnly: false, 
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: 60 * 60 * 24 * 7,
          });

          return response;
        } else {
          return NextResponse.json(
            { error: 'Login failed after registration' },
            { status: 500 }
          );
        }
      }
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
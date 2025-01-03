'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import * as Radix from "@radix-ui/themes";
import { User, Lock, Mail } from "lucide-react";
import Link from 'next/link';

interface AuthFormProps {
  mode: 'login' | 'register';
}

export default function AuthForm({ mode }: AuthFormProps) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState(''); // New state for email
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    try {
      const body: { action: 'login' | 'register'; username: string; password: string; email?: string } = {
        action: mode,
        username,
        password,
      };

      if (mode === 'register') {
        body.email = email; // Include email in the request body for registration
      }

      const response = await fetch('/api/auth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      console.log(data);

      if (!response.ok) {
        throw new Error(data.error || 'Authentication failed');
      }

      if (mode === 'login') {
        router.push('/'); // Redirect to home after login
      } else {
        router.push('/login'); // Redirect to login after registration
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };

  return (
    <Radix.Card size="4" style={{ 
      background: 'rgba(255,255,255,0.02)',  // More transparent background
      width: '100%',
      maxWidth: '400px',
      padding: '3rem'                    // Increased padding for more space inside
    }}>
      <form onSubmit={handleSubmit}>
        <Radix.Flex direction="column" gap="4">
          {error && <Radix.Text color="red" size="2">{error}</Radix.Text>}
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <User size={16} />
            <input
              type="text"
              size={3}
              placeholder="Username"
              value={username}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
              required
              style={{
                padding: '0.5rem',
                borderRadius: '4px',
                border: '1px solid #aaa',
                flex: '1'
              }}
            />
          </div>

          {mode === 'register' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Mail size={16} />
              <input
                type="email"
                size={3}
                placeholder="Email"
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                required
                style={{
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: '1px solid #aaa',
                  flex: '1'
                }}
              />
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Lock size={16} />
            <input
              type="password"
              size={3}
              placeholder="Password"
              value={password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              required
              style={{
                padding: '0.5rem',
                borderRadius: '4px',
                border: '1px solid #aaa',
                flex: '1'
              }}
            />
          </div>

          <Radix.Button size="3" style={{ 
            background: '#0066ff',
            cursor: 'pointer'
          }}>
            {mode === 'login' ? 'Log In' : 'Sign Up'}
          </Radix.Button>

          <Radix.Separator size="4" />

          <Radix.Text size="2" align="center">
            {mode === 'login' ? (
              <Radix.Text size="2" color="gray">
                Don&apos;t have an account?{' '}
                <Link href="/register" className="text-blue-500 hover:underline">
                  Sign up
                </Link>
              </Radix.Text>
            ) : (
              <Radix.Text size="2" color="gray">
                Already have an account?{' '}
                <Link href="/login" className="text-blue-500 hover:underline">
                  Sign in
                </Link>
              </Radix.Text>
            )}
          </Radix.Text>
        </Radix.Flex>
      </form>
    </Radix.Card>
  );
}
'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card, Text, Box, ScrollArea, Flex, Button, TextField, IconButton } from '@radix-ui/themes'
import { Send, Copy } from 'lucide-react'

interface AgentThoughtsProps {
  className?: string
}

const AgentThoughts: React.FC<AgentThoughtsProps> = ({ className }) => {
  const [prompt, setPrompt] = useState('')
  const [thoughts, setThoughts] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [thoughts])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || isStreaming) return

    setIsStreaming(true)
    setThoughts([])

    try {
      const response = await fetch('/api/agents/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('token')
        },
        body: JSON.stringify({ prompt }),
      })

      if (!response.ok) throw new Error('Stream request failed')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        // Split buffer by newlines and process complete messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep the last incomplete line in buffer
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line)
              let formattedMessage = ''
              
              switch (data.type) {
                case 'thought':
                  formattedMessage = `🤔 ${data.content}\n`
                  break
                case 'action':
                  formattedMessage = `🔍 ${data.content}\n`
                  break
                case 'observation':
                  formattedMessage = `📝 ${data.content}\n`
                  break
                case 'error':
                  formattedMessage = `❌ ${data.content}\n`
                  break
                default:
                  formattedMessage = `${data.content}\n`
              }
              
              setThoughts(prev => [...prev, formattedMessage])
            } catch (e) {
              console.error('Failed to parse JSON:', line)
            }
          }
        }
      }
    } catch (error) {
      setThoughts(prev => [...prev, `❌ Error: ${error}\n`])
    } finally {
      setIsStreaming(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(thoughts.join(''))
  }

  return (
    <Card className={className}>
      <Flex direction="column" gap="3" style={{ height: '100%' }}>
        <ScrollArea type="always" scrollbars="vertical" style={{ height: 'calc(100vh - 200px)' }}>
          <Box ref={scrollRef} style={{ whiteSpace: 'pre-wrap', padding: '1rem' }}>
            {thoughts.length > 0 ? (
              thoughts.map((thought, i) => (
                <Text key={i} as="div" size="2" style={{ 
                  marginBottom: '0.5rem',
                  color: thought.startsWith('❌') ? 'var(--red-11)' : 
                         thought.startsWith('🤔') ? 'var(--blue-11)' :
                         thought.startsWith('🔍') ? 'var(--purple-11)' :
                         'var(--gray-12)'
                }}>
                  {thought}
                </Text>
              ))
            ) : (
              <Text color="gray">Enter a prompt to start the agent&apos;s thought process...</Text>
            )}
          </Box>
        </ScrollArea>

        <Flex gap="2" align="center">
          <form onSubmit={handleSubmit} style={{ flex: 1, display: 'flex', gap: '0.5rem' }}>
            <TextField.Root style={{ flex: 1 }}>
              <TextField.Input 
                placeholder="Enter your prompt..." 
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isStreaming}
              />
            </TextField.Root>
            <Button type="submit" disabled={isStreaming}>
              <Send size={16} />
              Send
            </Button>
          </form>
          {thoughts.length > 0 && (
            <IconButton onClick={copyToClipboard} variant="outline">
              <Copy size={16} />
            </IconButton>
          )}
        </Flex>
      </Flex>
    </Card>
  )
}

export default AgentThoughts

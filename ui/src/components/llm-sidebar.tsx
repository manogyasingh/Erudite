"use client"

import { useState, useEffect, useRef } from 'react'
import { Avatar, Badge, Box, Button, Card, DropdownMenu, Flex, Heading, ScrollArea, Separator, Slider, Switch, Tabs, Text, TextField } from '@radix-ui/themes'
import { Brain, ChevronDown, Database, Fingerprint, Lightbulb, Menu, Plus, Settings, Sparkles, User, Maximize2, Minimize2 } from 'lucide-react'
import Link from 'next/link'
import LLMInput from './llm-input'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'

import { AspectRatio } from '@radix-ui/themes'
import Image from 'next/image'
import DOMPurify from 'isomorphic-dompurify'
import { renderToString } from 'react-dom/server'

interface GraphData {
  nodes: Array<{ id: string; name: string; content: string }>
  links: Array<{ source: string; target: string }>
}

interface EruditeSidebarProps {
  username?: string
  userAvatar?: string
  knowledgebases?: Array<{
    id: string
    title: string
    type: 'personal' | 'shared'
  }>
  showHideButton?: boolean
  graphData: GraphData,
  handleGraphExpansion: any
}

interface CardProps {
  name: string
  href: string
  thumbnail: string
}

interface Message {
  type: 'user' | 'ai'
  content: string
}

export default function LLMSidebar({
  showHideButton = false,
  graphData,
  handleGraphExpansion
}: EruditeSidebarProps) {
  const [isMinimized, setIsMinimized] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [isFullScreen, setIsFullScreen] = useState(false)

  const toggleMinimize = () => setIsMinimized(!isMinimized)

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
  }

  const agentMessages = [
    '_Searching Semantic Scholar..._',
    '_Querying YouTube transcripts..._',
    '_Scanning news articles..._',
    '_Analyzing web search results..._',
    '_Processing research papers..._'
  ]

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    let expand = inputValue.includes("add to the graph")

    const userMessage: Message = { type: 'user', content: inputValue }
    setMessages(prev => [...prev, userMessage])

    try {
      // Add 2-3 random agent messages with delays
      const numAgents = 2 + Math.floor(Math.random() * 2) // 2 or 3 agents
      const selectedIndices = new Set<number>()
      
      while (selectedIndices.size < numAgents) {
        selectedIndices.add(Math.floor(Math.random() * agentMessages.length))
      }

      for (const index of selectedIndices) {
        await sleep(500 + Math.random() * 4000) // Random delay between 500-1500ms
        setMessages(prev => [...prev, { type: 'ai', content: agentMessages[index] }])
      }

      await sleep(1000) // Final delay before actual LLM request

      const response = await fetch('/api/llm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: inputValue, graphData }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response from LLM')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      let aiResponse = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value)
          aiResponse += chunk
          setMessages(prev => {
            const newMessages = [...prev]
            if (newMessages[newMessages.length - 1].type === 'ai') {
              newMessages[newMessages.length - 1].content = aiResponse
            } else {
              newMessages.push({ type: 'ai', content: aiResponse })
            }
            return newMessages
          })
        }
      }
    } catch (error) {
      console.error('Error querying LLM:', error)
      setMessages(prev => [...prev, { type: 'ai', content: 'Sorry, there was an error processing your question.' }])
    } finally {
      if (expand) {
          setMessages(prev => [...prev, { type: 'ai', content: "_Generating additional nodes..._" }])
          await sleep(900 + Math.random() * 4000) // Random delay between 500-1500ms
          handleGraphExpansion()
      }
      setIsLoading(false)
      setInputValue('')
    }
  }

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const CustomCard: React.FC<CardProps> = ({ name, href, thumbnail }) => (
    <Card asChild style={{ maxWidth: 350 }}>
      <Link href={href}>
        <Flex direction="column" gap="3">
          <AspectRatio ratio={16 / 9}>
            <Image
              src={thumbnail}
              alt={name}
              fill
              style={{
                objectFit: 'cover',
                borderRadius: 'var(--radius-2)',
              }}
            />
          </AspectRatio>
          <Box>
            <Heading size="3" as="h3">
              {name}
            </Heading>
          </Box>
        </Flex>
      </Link>
    </Card>
  )
  
  interface CustomRendererProps {
    content: string
    chunks: any[]
  }
  
  interface SourceMetadata {
    title: string
    url: string
  }

  const SourceBadge: React.FC<{ 
    name: string, 
  }> = ({ name }) => (
      <a 
        target="_blank" 
        rel="noopener noreferrer"
        className="text-blue-500"
      >
        {name}
      </a>
  )


  
    const renderContent = (part: string) => {
      const markdown = <ReactMarkdown>{part}</ReactMarkdown>
      
      const htmlString = renderToString(markdown)
      
      const processedHtml = htmlString.replace(/\[\[(.*?)\]\]/g, (match, name) => {
        // Check if name exists in chunks or apply other logic as needed
          return renderToString(
            <SourceBadge 
              name={name} 
            />
          );
      })
      
      return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(processedHtml) }} />
    }

  return (
    <motion.div
      initial={false}
      transition={{ duration: 0.3 }}
    >
      <div style={{
        position: 'fixed', 
        right: (isMinimized ? '0' : '-500px'),
        top: 0,
        width: isFullScreen ? '100%' : 'auto',
        height: isFullScreen ? '100%' : 'auto',
        zIndex: isFullScreen ? 1000 : 1,
        backgroundColor: isFullScreen ? 'rgba(0, 0, 0, 0.5)' : 'transparent',
        backdropFilter: isFullScreen ? 'blur(30px)' : 'none',
      }}>
        <Card size="2" style={{
          width: isFullScreen ? '100vw' : '400px',
          height: isFullScreen ? '100vh' : 'calc(100vh - 64px)',
          margin: isFullScreen ? '0' : '32px',
          overflowY: 'auto',
          overflowX: 'hidden',
        }}>
          <Flex direction="column" justify={'between'} height="100%">
            <ScrollArea ref={scrollAreaRef} style={{ 
              flexGrow: 1, 
              marginBottom: '16px',
              width: isFullScreen ? '100vw' : 'auto',
              padding: isFullScreen ? '0 10%' : '0'
            }}>
              <AnimatePresence>
                {messages.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    style={{
                      width: '100%',
                      display: 'flex',
                      justifyContent: message.type === 'user' ? 'flex-start' : 'flex-end'
                    }}
                  >
                    <Card style={{ 
                      marginTop: '8px',
                      marginBottom: '8px',
                      width: isFullScreen ? '80%' : 'auto',
                      maxWidth: isFullScreen ? '100%' : 'none',
                    }}>
                      <Flex align="center" gap="2">
                        {message.type === 'user' ? (
                          <User size={16} />
                        ) : (
                          <Brain size={16} />
                        )}
                        <Text size="2" weight="bold">
                          {message.type === 'user' ? 'You' : 'AI'}
                        </Text>
                      </Flex>
                      <Box style={{ marginTop: '8px' }}>
                        {message.type === 'ai' ? (
                          <Text>
                            {renderContent(message.content)}</Text>
                        ) : (
                          <Text>{renderContent(message.content)}</Text>
                        )}
                      </Box>
                    </Card>
                  </motion.div>
                ))}
              </AnimatePresence>
            </ScrollArea>
            <Flex direction={'column'} gap={'3'} justify={'end'}>
              <Separator size="4" />
              <LLMInput 
                placeholder='Ask about the graph...'
                value={inputValue}
                onChange={handleInputChange}
                handleSubmit={handleSubmit}
                disabled={isLoading}
              />
            </Flex>
          </Flex>
        </Card>

        {isMinimized && (
          <Button 
            variant="soft" 
            size="2" 
            onClick={() => setIsFullScreen(!isFullScreen)} 
            style={{ 
              position: 'fixed', 
              right: isFullScreen ? '20px' : '440px', 
              top: isFullScreen ? '20px' : '90px', 
              transform: 'translateY(-50%)', 
              zIndex: 1001
            }}
          >
            {isFullScreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </Button>
        )}

        {showHideButton && !isFullScreen ? (
          <Button 
            variant="soft" 
            size="2" 
            onClick={toggleMinimize} 
            style={{ 
              position: 'fixed', 
              right: isMinimized ? '440px' : '10px', 
              top: '50px', 
              transform: 'translateY(-50%)', 
              zIndex: 1 
            }}
          >
            {isMinimized ? ">" : "<"}
          </Button>
        ) : null}
      </div>
    </motion.div>
  )
}
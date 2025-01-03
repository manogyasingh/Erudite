'use client'

import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Card, Flex, Text, AspectRatio, Box, Heading, Badge } from '@radix-ui/themes'
import Image from 'next/image'
import Link from 'next/link'
import DOMPurify from 'isomorphic-dompurify'
import { renderToString } from 'react-dom/server'

interface CardProps {
  name: string
  href: string
  thumbnail: string
}

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
  index: number, 
  metadata: SourceMetadata,
  onHover: (metadata: SourceMetadata | null) => void 
}> = ({ index, metadata, onHover }) => (
  <Badge 
    asChild 
    variant="outline" 
    radius="full"
    style={{ cursor: 'pointer' }}
  >
    <a 
      href={metadata.url} 
      target="_blank" 
      rel="noopener noreferrer"
      onClick={() => onHover(metadata)}
    >
      Source {index + 1}
    </a>
  </Badge>
)

const MetadataCard: React.FC<{ metadata: SourceMetadata | null }> = ({ metadata }) => {
  if (!metadata) return null;

  return (
    <Card
      style={{
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        maxWidth: '400px',
        zIndex: 1000,
        backgroundColor: 'var(--gray-1)',
        boxShadow: 'var(--shadow-5)',
      }}
    >
      <Flex direction="column" gap="2">
        <Heading size="2">{metadata.title}</Heading>
        <Text size="1" style={{ wordBreak: 'break-all' }}>{metadata.url}</Text>
      </Flex>
    </Card>
  )
}

const CustomRenderer: React.FC<CustomRendererProps> = ({ content, chunks }) => {
  const [hoveredSource, setHoveredSource] = useState<SourceMetadata | null>(null);
  const parts = content.split(/```card|```/)

  const renderContent = (part: string) => {
    const markdown = <ReactMarkdown>{part}</ReactMarkdown>
    
    const htmlString = renderToString(markdown)
    
    const processedHtml = htmlString.replace(/\[S(\d+)\]/g, (match, number) => {
      const index = parseInt(number) - 1
      if (index >= 0 && index < chunks.length && chunks[index]?.content?.metadata) {
        const metadata = {
          title: chunks[index].content.metadata.title,
          url: chunks[index].content.metadata.url
        }
        return renderToString(
          <SourceBadge 
            index={index} 
            metadata={metadata}
            onHover={setHoveredSource}
          />
        )
      }
      return match
    })

    return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(processedHtml) }} />
  }

  return (
    <>
      {parts.map((part, index) => {
        if (index % 2 === 0) {
          return (
            <div key={index} className="markdown-renderer">
              {renderContent(part)}
            </div>
          )
        } else {
          try {
            const cardProps: CardProps = JSON.parse(part)
            return <CustomCard key={index} {...cardProps} />
          } catch (error) {
            console.error('Failed to parse card props:', error)
            return <Text color="red">Error rendering card</Text>
          }
        }
      })}
      <MetadataCard metadata={hoveredSource} />
    </>
  )
}

export default CustomRenderer
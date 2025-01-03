'use client'

import { useState, useEffect } from "react"
import { useRouter, useParams } from 'next/navigation'
import { Box, Container, Flex, Heading, Text, Card, ScrollArea } from '@radix-ui/themes'
import { Brain, Database, FileSearch, FileText, Sparkles } from 'lucide-react'

interface LoadingStage {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const stages: LoadingStage[] = [
  {
    icon: <Brain className="animate-pulse" size={32} />,
    title: "Analyzing Query",
    description: "Understanding your request and planning the knowledge graph",
  },
  {
    icon: <Sparkles className="animate-bounce" size={32} />,
    title: "Generating Topics",
    description: "Identifying key topics and relationships",
  },
  {
    icon: <FileSearch className="animate-spin" size={32} />,
    title: "Searching Sources",
    description: "Gathering information from multiple sources",
  },
  {
    icon: <FileText className="animate-pulse" size={32} />,
    title: "Creating Articles",
    description: "Synthesizing comprehensive articles for each topic",
  },
  {
    icon: <Database className="animate-bounce" size={32} />,
    title: "Building Graph",
    description: "Finalizing the knowledge graph structure",
  },
];

declare global {
  interface Window {
    particlesJS: (id: string, options: any) => void;
    pJSDom: Array<{ pJS: { particles: { fn: { vendors: { destroypJS: () => void } } } } }>;
  }
}

export default function LoadingPage() {
  const [currentStage, setCurrentStage] = useState(0);
  const [graphTitle, setGraphTitle] = useState('Creating Knowledge Graph...');
  const [topics, setTopics] = useState<string[]>([]);
  const router = useRouter();
  const params = useParams();

  useEffect(() => {
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('token='))
      ?.split('=')[1];

    if (!token) {
      router.push('/login');
      return;
    }

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/graph-status`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ uuid: params.slug, auth: token })
        });
        
        if (!response.ok) throw new Error('Failed to fetch status');
        
        const data = await response.json();
        console.log(data);
        const status = data.status;
        const title = data.title;

        setGraphTitle(title || 'Creating Knowledge Graph...');

        if (status === 'done') {
          router.push(`/graph/${params.slug}`);
          return;
        }

        if (status.startsWith('topics_found:')) {
          setCurrentStage(1+1);
          const topicList = status.split(':')[1].split('|');
          console.log(topicList);
          setTopics(topicList);
        } else if (status === 'search_results_found') {
          setCurrentStage(2+1);
        } else if (status === 'articles_generated') {
          setCurrentStage(3+1);
        } else if (status === 'done') {
          router.push(`/graph/${params.slug}`);
          return;
        }

      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [params.slug, router]);

  return (
    <div className="relative min-h-screen">
      {/* <div id="particles-js" className="absolute inset-0 z-0" /> */}
      
      <Container size="3" className="relative z-10">
        <Flex direction="column" gap="6" align="center" justify="center" style={{ minHeight: '80vh' }}>
          <Heading size="8" align="center">{graphTitle}</Heading>
          
          {topics.length > 0 && (
            <Card style={{ width: '100%', maxWidth: '600px', maxHeight: '300px' }}>
              <ScrollArea style={{ height: '100%' }}>
                <Flex direction="column" gap="2">
                  {topics.map((topic, index) => (
                    <Text key={index} size="3">{topic}</Text>
                  ))}
                </Flex>
              </ScrollArea>
            </Card>
          )}

          <Card>
            <Flex direction="column" gap="4" style={{ width: '100%', maxWidth: '600px' }}>
              {stages.map((stage, index) => (
                <Flex
                  key={stage.title}
                  gap="3"
                  align="center"
                  style={{
                    opacity: index <= currentStage ? 1 : 0.5,
                    transition: 'all 0.3s ease',
                    padding: '16px',
                    borderRadius: '8px'
                  }}
                >
                  <Box className={index === currentStage ? 'animate-bounce' : ''}>
                    {stage.icon}
                  </Box>
                  <Box>
                    <Text size="5" weight={index === currentStage ? "bold" : "regular"}>
                      {stage.title}<br />
                    </Text>
                    <Text color="gray" size="2">
                      {stage.description}
                    </Text>
                  </Box>
                </Flex>
              ))}
            </Flex>
          </Card>
        </Flex>
      </Container>
    </div>
  );
}
'use client'

import Image from "next/image";
import { Vortex } from "@/components/ui/vortex";
import { Box, Flex, Card, TextField, Text, Grid, Heading, Container } from "@radix-ui/themes";
import { Database, Sparkles, Brain, Lightbulb } from "lucide-react";
import { useState, useEffect } from "react";
import TextLoop from "react-text-loop";
import { useRouter } from 'next/navigation';
import Sidebar from "@/components/sidebar";


import LLMInput from "@/components/llm-input";

const getCookie = (name: string) => {
    const matches = document.cookie.match(
      new RegExp(`(?:^|; )${name.replace(/([\.$?*|{}()\[\]\\\/\+^])/g, '\\$1')}=([^;]*)`)
    );
    return matches ? decodeURIComponent(matches[1]) : null;
  };

export default function Home() {
    const [mode, setMode] = useState('explorer');
    const [textAreaValue, setTextAreaValue] = useState('');
    const router = useRouter();

    useEffect(() => {
        const script = document.createElement('script');
        script.src = "https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js";
        script.async = true;
        script.onload = () => {
            // @ts-ignore
            window.particlesJS('particles-js', {
                "particles": {
                    "number": {
                        "value": 80,
                        "density": {
                            "enable": true,
                            "value_area": 800
                        }
                    },
                    "color": {
                        "value": mode === 'explorer' ? '#666666' : mode === 'discoverer' ? '#666666' : '#666666'
                    },
                    "shape": {
                        "type": "circle"
                    },
                    "opacity": {
                        "value": 0.5,
                        "random": false
                    },
                    "size": {
                        "value": 3,
                        "random": true
                    },
                    "line_linked": {
                        "enable": true,
                        "distance": 150,
                        "color": mode === 'explorer' ? '#666666' : mode === 'discoverer' ? '#666666' : '#666666',
                        "opacity": 0.4,
                        "width": 1
                    },
                    "move": {
                        "enable": true,
                        "speed": mode === 'explorer' ? 4 : mode === 'discoverer' ? 6 : 8,
                        "direction": "none",
                        "random": false,
                        "straight": false,
                        "out_mode": "out",
                        "bounce": false
                    }
                },
                "interactivity": {
                    "detect_on": "canvas",
                    "events": {
                        "onhover": {
                            "enable": true,
                            "mode": "grab"
                        },
                        "onclick": {
                            "enable": true,
                            "mode": "push"
                        },
                        "resize": true
                    }
                },
                "retina_detect": true
            });
        };
        document.body.appendChild(script);

        return () => {
            document.body.removeChild(script);
        };
    }, []); // Only run once on mount

    useEffect(() => {
        // @ts-ignore
        if (window.pJSDom && window.pJSDom[0]?.pJS?.particles) {
            // @ts-ignore
            const particles: any = window.pJSDom[0].pJS.particles;
            particles.color.value = mode === 'explorer' ? '#666666' : mode === 'discoverer' ? '#666666' : '#666666';
            particles.line_linked.color = mode === 'explorer' ? '#666666' : mode === 'discoverer' ? '#666666' : '#666666';
            particles.move.speed = mode === 'explorer' ? 4 : mode === 'discoverer' ? 8 : 10;
            // @ts-ignore
        }
    }, [mode]);

    const handleTextAreaChange = (e: any) => {
        setTextAreaValue(e.target.value);
    };

    const handleSubmit = async (e: any) => {
        e.preventDefault();
        const token = getCookie('token');
        const response = await fetch('/api/generate-knowledgebase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ text: textAreaValue, mode: mode }),
        });
        const data = await response.json();
        console.log(data);
        if (data.uuid) {
            router.push(`/loading/${data.uuid}`);
        }
    };

    return (
        <div className="w-screen h-screen">
            <div className="fixed top-0 left-0 w-screen h-screen -z-10 opacity-80" id="particles-js"></div>
          
            <Box className="h-full" style={{
                width: 'calc(100vw - 320px - 32px)',
                height: 'calc(100vh - 64px)',
                margin: '32px',
                position: 'fixed',
                left: '320px',
                top: 0,
                overflowY: 'auto',
            }}>
                <Flex direction="row" gap="9" justify='start' className="h-full">
                    <Container className="h-full" minHeight={'90vh'}>
                      <Flex direction={'column'} justify={'center'} gap="8" className="h-full">
                      <Flex direction="row" justify={'center'} gap="2">

                      <Text size="8">Get started and</Text>
                        <TextLoop>
                          <Text size="8">unlock deep knowledge</Text>
                          <Text size="8">discover incredible ideas</Text>
                          <Text size="8">explore cutting-edge research</Text>
                          <Text size="8">transform your perspectives</Text>
                          <Text size="8">refine your understanding</Text>
                        </TextLoop>
                      </Flex>

                        {/* AI Prompt Box */}
                            {/* <Flex direction="column" gap="4" p="4">
                                <TextField.Root placeholder="Generate a knowledgebase on..." size={"3"}>
                                    <TextField.Slot>
                                        <Sparkles height="24" width="24" />
                                    </TextField.Slot>
                                </TextField.Root>
                            </Flex> */}

                            <LLMInput value={textAreaValue} onChange={handleTextAreaChange} handleSubmit={handleSubmit} placeholder="Create a new knowledgebase about anything!" />

                        {/* Mode Cards */}
                        <Grid columns="3" gap="4">
                            <Card 
                                size="4" 
                                style={{ 
                                    background: 'rgba(0,120,255,0.15)', 
                                    backdropFilter: 'blur(5px)',
                                    border: mode === 'explorer' ? '2px solid #0066ff' : 'none',
                                    cursor: 'pointer'
                                }}
                                onClick={() => setMode('explorer')}
                            >
                                <Flex direction="column" gap="3" p="4" style={{ height: '100%' }}>
                                    <Flex gap="2" align="center">
                                        <Box style={{ background: '#0066ff', padding: '8px', borderRadius: '8px' }}>
                                            <Lightbulb size={24} />
                                        </Box>
                                        <Heading size="7">Explorer</Heading>
                                    </Flex>
                                    <Text size="2" color="gray">
                                        Perfect for beginners. Provides clear, straightforward knowledgebases with helpful context and examples.
                                    </Text>
                                </Flex>
                            </Card>

                            <Card 
                                size="4" 
                                style={{ 
                                    background: 'rgba(255,120,0,0.15)', 
                                    backdropFilter: 'blur(5px)',
                                    border: mode === 'discoverer' ? '2px solid #ff6600' : 'none',
                                    cursor: 'pointer'
                                }}
                                onClick={() => setMode('discoverer')}
                            >
                                <Flex direction="column" gap="3" p="4" style={{ height: '100%' }}>
                                    <Flex gap="2" align="center">
                                        <Box style={{ background: '#ff6600', padding: '8px', borderRadius: '8px' }}>
                                            <Database size={24} />
                                        </Box>
                                        <Heading size="7">Discoverer</Heading>
                                    </Flex>
                                    <Text size="2" color="gray">
                                        Dives deeper into topics with detailed analysis and connections between different concepts.
                                    </Text>
                                </Flex>
                            </Card>

                            <Card 
                                size="4" 
                                style={{ 
                                    background: 'rgba(255,0,120,0.15)', 
                                    backdropFilter: 'blur(5px)',
                                    border: mode === 'pioneer' ? '2px solid #ff0066' : 'none',
                                    cursor: 'pointer'
                                }}
                                onClick={() => setMode('pioneer')}
                            >
                                <Flex direction="column" gap="3" p="4" style={{ height: '100%' }}>
                                    <Flex gap="2" align="center">
                                        <Box style={{ background: '#ff0066', padding: '8px', borderRadius: '8px' }}>
                                            <Brain size={24} />
                                        </Box>
                                        <Heading size="7">Pioneer</Heading>
                                    </Flex>
                                    <Text size="2" color="gray">
                                        Advanced mode for experts. Generates novel insights and dives into current state-of-the-art research.
                                    </Text>
                                </Flex>
                            </Card>
                        </Grid></Flex>
                    </Container>
                </Flex>
            </Box>
            <Sidebar />
        </div>
    );
}

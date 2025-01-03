'use client';

import AuthForm from '@/components/ui/auth-form';
import { Box, Flex, Container, Text } from "@radix-ui/themes";
import Sidebar from "@/components/sidebar";
import { useEffect } from "react";
import MainLogo from '@/components/main-logo';

export default function LoginPage() {
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
            "value": '#666666'
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
            "color": '#666666',
            "opacity": 0.4,
            "width": 1
          },
          "move": {
            "enable": true,
            "speed": 4,
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
  }, []);

  return (
    <div className="w-screen h-screen">
      <div className="fixed top-0 left-0 w-screen h-screen -z-10 opacity-80" id="particles-js"></div>
      
      <Box className="h-full" style={{
        width: 'calc(100vw - 32px)',
        height: 'calc(100vh - 64px)',
        margin: '32px',
        position: 'fixed',
        left: 0,
        top: 0,
        overflowY: 'auto',
      }}>
        <Container className="h-full" minHeight={'90vh'}>
          <Flex 
            direction="column" 
            gap="4" 
            justify="center" 
            align="center" 
            style={{ height: '100%' }}
          >
            <MainLogo variant="vertical" className="mb-8" />

            <Text size="8" align="center" mb="6">Welcome back!</Text>
            <AuthForm mode="login" />
          </Flex>
        </Container>
      </Box>
      {/* <Sidebar /> */}
    </div>
  );
}
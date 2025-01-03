"use client";

import { useState, useEffect } from "react";
import { Avatar, Badge, Box, Button, Card, DropdownMenu, Flex, Heading, ScrollArea, Separator, Tabs, Text } from "@radix-ui/themes";
import { ChevronDown, Database, Fingerprint, Lightbulb, Settings, Sparkles, User } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import MainLogo from './main-logo';

interface KnowledgeGraph {
  uuid: string;
  title: string;
  user_id: string;
  status: string;
}

interface EruditeSidebarProps {
  showHideButton?: boolean;
}

// Utility functions for cookies
const getCookie = (name: string) => {
  const matches = document.cookie.match(
    new RegExp(`(?:^|; )${name.replace(/([\.$?*|{}()\[\]\\\/\+^])/g, '\\$1')}=([^;]*)`)
  );
  return matches ? decodeURIComponent(matches[1]) : null;
};

const setCookie = (name: string, value: string, options: { [key: string]: any } = {}) => {
  let cookieString = `${name}=${encodeURIComponent(value)}`;
  if (options) {
    if (options.path) cookieString += `; path=${options.path}`;
    if (options.maxAge) cookieString += `; max-age=${options.maxAge}`;
    if (options.secure) cookieString += `; Secure`;
  }
  document.cookie = cookieString;
};

const removeCookie = (name: string) => {
  document.cookie = `${name}=; path=/; max-age=0`;
};

export default function Sidebar({
  showHideButton = false,
}: { showHideButton?: boolean }) {
  const [isMinimized, setIsMinimized] = useState(true);
  const [username, setUsername] = useState<string | null>(null);
  const [knowledgeGraphs, setKnowledgeGraphs] = useState<KnowledgeGraph[]>([]);
  const router = useRouter();

  useEffect(() => {
    const token = getCookie('token');
    if (token) {
      // Fetch knowledge graphs
      fetch('/api/list-graphs', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => response.json())
      .then(data => {
        if (Array.isArray(data)) {
          setKnowledgeGraphs(data);
        }
      })
      .catch(error => console.error('Error fetching knowledge graphs:', error));

      // Get username from token
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUsername(payload.sub);
    }
  }, []);

  const toggleMinimize = () => setIsMinimized(!isMinimized);

  const handleLogout = async () => {
        console.log("Logging out");
        // Clear all cookies client-side
        document.cookie.split(";").forEach((cookie) => {
          const name = cookie.split("=")[0].trim();
          removeCookie(name);
        });

        // Redirect to the login page
        window.location.href = "/login";
    
  };

  return (
    <motion.div initial={false} transition={{ duration: 0.3 }}>
      <div
        style={{
          position: "fixed",
          left: isMinimized ? 0 : "-400px",
          top: 0,
        }}
      >
        <Card
          size="2"
          style={{
            width: "320px",
            height: "calc(100vh - 64px)",
            margin: "32px",
            overflowY: "auto",
            overflowX: "hidden",
          }}
        >
          <Flex direction="column" height="100%">
            {/* Header */}
            <Box pb="4">
              <Flex direction="column" align="center" gap="2">
                <MainLogo variant="horizontal" />
              </Flex>
            </Box>

            <Separator size="4" />

            {username ? (
              // Logged in view
              <>
                <Box py="4">
                  <Heading size="5">Quick Actions</Heading>
                  <Flex direction="column" gap="2" mt="2">
                    <Button variant="soft" size="2" asChild>
                      <Link href="/">
                        <Lightbulb size={16} />
                        Create a new knowledgebase
                      </Link>
                    </Button>
                    <Button variant="soft" size="2" color="yellow" asChild>
                      <Link href="/">
                        <Sparkles size={16} />
                        Generate ideas
                      </Link>
                    </Button>
                  </Flex>
                </Box>

                <Separator size="4" />

                {/* Knowledgebases List */}
                <Box pb="4" style={{ flexGrow: 1, overflowY: "auto" }}>
                  <Tabs.Root defaultValue="personal">
                    <Tabs.List>
                      <Tabs.Trigger value="personal">Personal</Tabs.Trigger>
                      <Tabs.Trigger value="shared">Shared</Tabs.Trigger>
                    </Tabs.List>
                    <ScrollArea>
                      <Box pt="2">
                        {knowledgeGraphs.map((graph) => (
                          <Button key={graph.uuid} variant="ghost" size="2" asChild>
                            <Link href={`/graph/${graph.uuid}`}>
                              <Flex align="center" gap="2" style={{ width: '100%' }}>
                                <Database size={16} />
                                <Text style={{ 
                                  overflow: 'hidden', 
                                  textOverflow: 'ellipsis', 
                                  whiteSpace: 'nowrap',
                                  maxWidth: 'calc(100%)' // Account for icon and badge
                                }}>
                                  {graph.title}
                                </Text>
                              </Flex>
                            </Link>
                          </Button>
                        ))}
                      </Box>
                    </ScrollArea>
                  </Tabs.Root>
                </Box>

                <Separator size="4" />

                {/* User Section */}
                <Box mt="auto" pt="4">
                  <DropdownMenu.Root>
                    <DropdownMenu.Trigger>
                      <Button variant="ghost" size="2">
                        <Flex align="center" gap="2">
                          <Avatar
                            size="2"
                            src="/placeholder.svg"
                            fallback={username[0]}
                            radius="full"
                          />
                          <Text size="2" weight="medium">
                            {username}
                          </Text>
                          <ChevronDown size={16} />
                        </Flex>
                      </Button>
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Content>
                      <DropdownMenu.Item>
                        <User size={16} />
                        Profile
                      </DropdownMenu.Item>
                      <DropdownMenu.Item>
                        <Settings size={16} />
                        Settings
                      </DropdownMenu.Item>
                      <DropdownMenu.Separator />
                      <DropdownMenu.Item color="red" onClick={handleLogout}>
                        <Fingerprint size={16} />
                        Log out
                      </DropdownMenu.Item>
                    </DropdownMenu.Content>
                  </DropdownMenu.Root>
                </Box>
              </>
            ) : (
              // Not logged in view
              <Box py="4">
                <Flex direction="column" gap="2">
                  <Button variant="soft" size="2" asChild>
                    <Link href="/login">
                      <User size={16} />
                      Log In
                    </Link>
                  </Button>
                  <Button variant="outline" size="2" asChild>
                    <Link href="/register">
                      <Fingerprint size={16} />
                      Sign Up
                    </Link>
                  </Button>
                </Flex>
              </Box>
            )}
          </Flex>
        </Card>

        {showHideButton && (
          <Button
            variant="soft"
            size="2"
            onClick={toggleMinimize}
            style={{
              position: "fixed",
              left: isMinimized ? "360px" : "10px",
              top: "50px",
              transform: "translateY(-50%)",
              zIndex: 1,
            }}
          >
            {isMinimized ? "<" : ">"}
          </Button>
        )}
      </div>
    </motion.div>
  );
}

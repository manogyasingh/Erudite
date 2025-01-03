'use client';

import "./globals.css";
import "@radix-ui/themes/styles.css";
import { Theme, ThemePanel } from "@radix-ui/themes";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <title>Erudite</title>
      <body>
          
      <Theme appearance="dark" grayColor="slate" scaling="110%">
        <main className="min-h-screen">
          
        {children}

        </main>
        
        {/* <ThemePanel /> */}
        </Theme>
      </body>
    </html>
  );
}

# Erudite Frontend

## Overview

The Erudite frontend is built with Next.js 14, featuring a modern, responsive interface for knowledge graph exploration and agent interaction. It provides real-time streaming capabilities, interactive visualizations, and a seamless user experience.

## Project Structure

```
ui/
├── src/
│   ├── app/                 # Next.js app router pages
│   │   ├── agent/          # Agent interaction pages
│   │   ├── graph/          # Knowledge graph pages
│   │   └── api/            # API route handlers
│   ├── components/         # Reusable components
│   │   ├── agent-thoughts/ # Agent streaming components
│   │   ├── graph/         # Graph visualization components
│   │   └── ui/            # Common UI components
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility functions
│   ├── styles/            # Global styles
│   └── types/             # TypeScript definitions
├── public/                # Static assets
└── tests/                # Frontend tests
```

## Key Features

1. **Real-time Agent Interaction**
   - Streaming thought process visualization
   - Interactive agent commands
   - Multi-type message display

2. **Knowledge Graph Visualization**
   - Interactive graph exploration
   - Node expansion and navigation
   - Custom graph layouts

3. **Modern UI Components**
   - Radix UI integration
   - Dark/light theme support
   - Responsive design

4. **Performance Optimizations**
   - Server-side rendering
   - Incremental static regeneration
   - Optimized asset loading

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your settings
```

3. Run development server:
```bash
npm run dev
# or
yarn dev
```

4. Build for production:
```bash
npm run build
npm start
# or
yarn build
yarn start
```

## Configuration

### Environment Variables

Create `.env.local` with:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Authentication
NEXT_PUBLIC_AUTH_DOMAIN=your-auth-domain
NEXT_PUBLIC_AUTH_CLIENT_ID=your-client-id

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_DARK_MODE=true

# Performance
NEXT_PUBLIC_ISR_REVALIDATE_TIME=3600
```

## Component Documentation

### Agent Thoughts Component

The `AgentThoughts` component handles real-time streaming of agent responses:

```typescript
<AgentThoughts
  initialPrompt="Your research query"
  onThoughtReceived={(thought) => {}}
  onComplete={() => {}}
/>
```

### Graph Visualization

The `GraphViewer` component renders interactive knowledge graphs:

```typescript
<GraphViewer
  graphData={data}
  onNodeClick={(node) => {}}
  layout="force"
/>
```

## Styling Guidelines

1. **Theme System**
   - Use Radix UI theme tokens
   - Support dark/light modes
   - Maintain consistent spacing

2. **CSS Modules**
   - Local scope for components
   - Reusable utility classes
   - Responsive design patterns

3. **Animation Guidelines**
   - Use CSS transitions
   - Implement reduced motion
   - Optimize performance

## State Management

1. **React Context**
   - Theme context
   - Auth context
   - Agent state context

2. **Local Storage**
   - User preferences
   - Cache management
   - Session data

## Responsive Design

- Mobile-first approach
- Breakpoint system
- Flexible layouts

## Security Best Practices

1. **Authentication**
   - JWT handling
   - Secure storage
   - Route protection

2. **Data Safety**
   - Input sanitization
   - XSS prevention
   - CSRF protection

## Performance Optimization

1. **Code Splitting**
   - Dynamic imports
   - Route-based splitting
   - Component lazy loading

2. **Asset Optimization**
   - Image optimization
   - Font loading
   - Bundle analysis

## Debugging

1. Enable debug mode in `.env.local`:
```bash
NEXT_PUBLIC_DEBUG=true
```

2. Use React Developer Tools

3. Check browser console

## Analytics Integration

1. **Usage Tracking**
   - Page views
   - User interactions
   - Performance metrics

2. **Error Tracking**
   - Error boundaries
   - Error logging
   - Performance monitoring

## CI/CD Pipeline

1. **GitHub Actions**
   - Automated testing
   - Lint checking
   - Build verification

2. **Deployment**
   - Vercel integration
   - Environment management
   - Release automation

## Future Improvements

1. Implement real-time collaboration
2. Add more graph layouts
3. Enhance mobile experience
4. Improve accessibility
5. Add more visualization options

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## Development Guidelines

1. **Code Style**
   - ESLint configuration
   - Prettier formatting
   - TypeScript strict mode

2. **Component Structure**
   - Atomic design principles
   - Composition patterns
   - Props documentation

3. **Performance**
   - Memoization
   - Virtual scrolling
   - Image optimization
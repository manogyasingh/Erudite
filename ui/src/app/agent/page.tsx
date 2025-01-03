'use client'
import dynamic from 'next/dynamic'

const AgentThoughts = dynamic(() => import('@/components/agent-thoughts'), {
  ssr: false
})

export default function AgentPage() {
  return (
      <div className="p-4">
        <AgentThoughts />
      </div>
  )
}

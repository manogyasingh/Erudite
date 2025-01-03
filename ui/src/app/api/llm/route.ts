import { NextRequest, NextResponse } from 'next/server'
import { createGroqClient } from '@/lib/groq'

const groq = createGroqClient(process.env.GROQ_API_KEY)

export async function POST(req: NextRequest) {
  const { question, graphData } = await req.json()

  const len = 5000 / graphData.nodes.length

  const prompt = `
    You are an AI assistant that answers questions about a knowledge graph on machine learning.
    The graph contains the following nodes and links:
    
    Nodes:
    ${graphData.nodes.map((node: { name: any; content: string }) => `- ${node.name}: ${node.content.substring(0,len)}...`).join('\n')}
    
    Please answer the following question based on this knowledge graph:
    ${question}

    Cite the nodes where you are getting the answer from, by enclosing it in double brackets [[Node Name]].
  `
    console.log(prompt);
  const stream = await groq.chat.completions.create({
    model: 'llama-3.2-90b-vision-preview',
    messages: [{ role: 'system', content: prompt }, { role: 'user', content: question }],
    stream: true,
  })

  const encoder = new TextEncoder()

  return new NextResponse(
    new ReadableStream({
      async start(controller) {
        for await (const chunk of stream) {
          const content = chunk.choices[0]?.delta?.content || ''
          controller.enqueue(encoder.encode(content))
        }
        controller.close()
      },
    }),
    {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    }
  )
}
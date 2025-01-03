import { Configuration, OpenAIApi } from 'openai-edge'
import { OpenAIStream, StreamingTextResponse } from 'ai'

// Create an OpenAI API client (that's edge friendly!) with a custom URL
const config = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
  basePath: process.env.OPENAI_API_URL
})
const openai = new OpenAIApi(config)

// IMPORTANT! Set the runtime to edge
export const runtime = 'edge'

export async function POST(req: Request) {
  // Extract the `messages` from the body of the request
  const { messages } = await req.json()

  // Ask OpenAI for a streaming chat completion given the prompt
  const response = await openai.createChatCompletion({
    model: 'gpt-4o-mini',
    stream: true,
    messages: messages.map((message: any) => ({
      content: message.content,
      role: message.role,
    })),
  })

  console.log(response);

  // Convert the response into a friendly text-stream
  const stream = OpenAIStream(response)
  // Respond with the stream
  return new StreamingTextResponse(stream)
}
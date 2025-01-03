import { NextRequest, NextResponse } from 'next/server'

const statusTexts = [
  'Initializing...',
  'Loading data...',
  'Processing information...',
  'Analyzing results...',
  'Finalizing...',
]

var hitCount = -1;

export async function GET(request: NextRequest) {

  const { searchParams } = new URL(request.url)
  const slug = searchParams.get('slug')


  // Simulate a delay
  hitCount = hitCount + 1;


  // Get the current step based on the number of requests for this slug
  const currentStep = (hitCount + 1) % (statusTexts.length + 1)

  if (currentStep === statusTexts.length) {
    return NextResponse.json({ status: 'completed', statusText: 'Completed!' })
  }

  return NextResponse.json({ status: 'loading', statusText: statusTexts[currentStep] })
}
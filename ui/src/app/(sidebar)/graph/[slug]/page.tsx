'use client'

import Sidebar from "@/components/sidebar";
import ForceGraph from "@/components/force-graph";

export default function GraphPage({ params }: { params: { slug: string } }) { 

  return (
    <div className="w-screen h-screen">
      <ForceGraph uuid={params.slug} />
      <Sidebar showHideButton={true} />
    </div>
  )
}
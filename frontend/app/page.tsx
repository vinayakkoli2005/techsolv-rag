"use client"

import { useState } from "react"
import { UrlForm } from "@/components/UrlForm"
import { VideoCard } from "@/components/VideoCard"
import { ChatPanel } from "@/components/ChatPanel"
import { ingestVideos } from "@/lib/api"
import type { VideoMeta } from "@/lib/types"

export default function Home() {
  const [metaA, setMetaA] = useState<VideoMeta | null>(null)
  const [metaB, setMetaB] = useState<VideoMeta | null>(null)
  const [ingesting, setIngesting] = useState(false)
  const [ready, setReady] = useState(false)
  const [chatKey, setChatKey] = useState(0)

  async function handleSubmit(youtubeUrl: string, instagramUrl: string) {
    setIngesting(true)
    setReady(false)
    try {
      const result = await ingestVideos(youtubeUrl, instagramUrl)
      setMetaA(result.A)
      setMetaB(result.B)
      setReady(true)
      setChatKey((k) => k + 1)
    } catch (e) {
      console.error("Ingestion failed:", e)
    } finally {
      setIngesting(false)
    }
  }

  return (
    <main className="min-h-screen p-6 flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-white">Video RAG Compare</h1>
      <UrlForm onSubmit={handleSubmit} disabled={ingesting} />
      <div className="grid grid-cols-2 gap-4">
        <VideoCard label="A" meta={metaA} />
        <VideoCard label="B" meta={metaB} />
      </div>
      <ChatPanel key={chatKey} ready={ready} />
    </main>
  )
}

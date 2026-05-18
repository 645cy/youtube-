"use client"

import { useGSAPReveal } from "@/hooks/useGSAPReveal"
import { ChannelCard } from "@/components/dashboard/ChannelCard"
import type { IntelChannel } from "@/lib/store"

interface ChannelGridProps {
  channels: IntelChannel[]
  onChannelClick: (channel: IntelChannel) => void
}

export function ChannelGrid({ channels, onChannelClick }: ChannelGridProps) {
  const gridRef = useGSAPReveal<HTMLDivElement>({
    y: 24,
    opacity: 0,
    duration: 0.5,
    stagger: 0.06,
    ease: "power3.out",
  })

  return (
    <div ref={gridRef} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {channels.map((channel) => (
        <div key={channel.id} className="depth-hover">
          <ChannelCard channel={channel} onClick={onChannelClick} />
        </div>
      ))}
    </div>
  )
}

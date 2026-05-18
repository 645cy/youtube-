"use client"

import { Sparkles } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="space-y-6">
      {/* CRG: Loading mirrors the redesigned dashboard layout so route transitions do not feel like a different app. */}
      <div className="lux-card overflow-hidden p-6">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-primary/12 text-primary">
            <Sparkles className="h-5 w-5 animate-pulse" />
          </span>
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-8 w-72 max-w-[70vw]" />
          </div>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="lux-card space-y-4 p-5">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-28" />
            <Skeleton className="h-4 w-40" />
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="lux-card space-y-4 p-5">
          <Skeleton className="h-5 w-36" />
          <Skeleton className="h-[320px] w-full" />
        </div>
        <div className="lux-card space-y-4 p-5">
          <Skeleton className="h-5 w-32" />
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-12 w-full" />
          ))}
        </div>
      </div>
    </div>
  )
}

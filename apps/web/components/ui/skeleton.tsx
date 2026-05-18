"use client"

import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl bg-muted/70 before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer before:bg-gradient-to-r before:from-transparent before:via-white/24 before:to-transparent dark:before:via-white/8",
        className
      )}
      {...props}
    />
  )
}

function CardSkeleton({ className }: { className?: string; delay?: number }) {
  return (
    <div className={cn("lux-card space-y-3 p-5", className)}>
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
    </div>
  )
}

function StatSkeleton({ className }: { className?: string; delay?: number }) {
  return (
    <div className={cn("lux-card space-y-4 p-5", className)}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-9 w-9" />
      </div>
      <Skeleton className="h-9 w-28" />
      <Skeleton className="h-4 w-20" />
    </div>
  )
}

function ChartSkeleton({ className }: { className?: string; delay?: number }) {
  const heights = [48, 72, 42, 86, 58, 66, 50, 90, 44, 70, 60, 78]
  return (
    <div className={cn("lux-card space-y-4 p-5", className)}>
      <Skeleton className="h-5 w-36" />
      <div className="flex h-[240px] items-end gap-2">
        {heights.map((height, index) => (
          <Skeleton key={index} className="flex-1" style={{ height: `${height}%` }} />
        ))}
      </div>
    </div>
  )
}

function SidebarSkeleton() {
  return (
    <div className="w-64 space-y-3 p-4">
      <Skeleton className="h-11 w-44" />
      {Array.from({ length: 7 }).map((_, index) => (
        <Skeleton key={index} className="h-12 w-full" />
      ))}
    </div>
  )
}

function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex gap-4 py-3">
      {Array.from({ length: columns }).map((_, index) => (
        <Skeleton key={index} className="h-4 flex-1" />
      ))}
    </div>
  )
}

export { Skeleton, CardSkeleton, StatSkeleton, ChartSkeleton, SidebarSkeleton, TableRowSkeleton }

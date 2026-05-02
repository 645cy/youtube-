/**
 * Skeleton 骨架屏组件 - shadcn/ui
 * 用于加载状态占位，比 Spinner 更好的用户体验
 */

import { cn } from "@/lib/utils"

/**
 * Skeleton 组件
 * 使用 animate-pulse 实现呼吸动画
 * 通过类名控制尺寸（w-full h-16）
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

/**
 * 卡片骨架屏 - 组合组件
 */
function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border bg-card p-4 space-y-3", className)}>
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <div className="flex gap-2">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  )
}

/**
 * 统计卡片骨架屏
 */
function StatSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border bg-card p-6 space-y-3", className)}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-3 w-16" />
    </div>
  )
}

/**
 * 图表骨架屏
 */
function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border bg-card p-6 space-y-4", className)}>
      <Skeleton className="h-5 w-32" />
      <div className="flex items-end gap-2 h-[250px]">
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1"
            style={{ height: `${Math.random() * 60 + 20}%` }}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * 侧边栏骨架屏
 */
function SidebarSkeleton() {
  return (
    <div className="w-64 space-y-4 p-4">
      <Skeleton className="h-8 w-3/4" />
      <div className="space-y-2 pt-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  )
}

/**
 * 表格行骨架屏
 */
function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex gap-4 py-3">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className={`h-4 flex-1`} style={{ maxWidth: `${20 + Math.random() * 30}%` }} />
      ))}
    </div>
  )
}

export {
  Skeleton,
  CardSkeleton,
  StatSkeleton,
  ChartSkeleton,
  SidebarSkeleton,
  TableRowSkeleton,
}
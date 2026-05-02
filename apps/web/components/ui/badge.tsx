/**
 * Badge 组件 - shadcn/ui
 * 标签/徽标组件，支持多种颜色变体
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        // 默认 - 次级背景
        default:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        // 主色
        primary:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/90",
        // 描边样式
        outline: "text-foreground",
        // 成功状态
        success:
          "border-transparent bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30",
        // 警告状态
        warning:
          "border-transparent bg-amber-500/20 text-amber-400 hover:bg-amber-500/30",
        // 危险状态
        danger:
          "border-transparent bg-red-500/20 text-red-400 hover:bg-red-500/30",
        // 信息状态
        info:
          "border-transparent bg-blue-500/20 text-blue-400 hover:bg-blue-500/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
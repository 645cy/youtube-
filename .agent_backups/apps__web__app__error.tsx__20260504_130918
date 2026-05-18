/**
 * 全局错误边界 Error Boundary
 * 捕获子组件渲染错误，防止整个应用崩溃
 */

"use client"

import { useEffect } from "react"
import { AlertTriangle, RefreshCw, Home } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // 上报错误到监控系统
    console.error("Error Boundary 捕获错误:", error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-4">
        <AlertTriangle className="h-8 w-8 text-red-400" />
      </div>

      <h2 className="text-xl font-bold mb-2">出错了</h2>
      <p className="text-sm text-muted-foreground max-w-md mb-2">
        应用遇到了意外错误。错误信息已记录，请尝试刷新页面。
      </p>

      {/* 错误详情（开发环境显示） */}
      {process.env.NODE_ENV === "development" && (
        <div className="mt-4 p-4 rounded-lg bg-red-500/5 border border-red-500/20 max-w-lg overflow-auto">
          <p className="text-xs font-mono text-red-400 text-left">
            {error.message}
          </p>
          {error.digest && (
            <p className="text-xs text-muted-foreground mt-2">
              Error ID: {error.digest}
            </p>
          )}
        </div>
      )}

      <div className="flex items-center gap-3 mt-6">
        <Button onClick={reset} variant="default">
          <RefreshCw className="h-4 w-4 mr-2" />
          重试
        </Button>
        <Link href="/dashboard">
          <Button variant="outline">
            <Home className="h-4 w-4 mr-2" />
            返回首页
          </Button>
        </Link>
      </div>
    </div>
  )
}
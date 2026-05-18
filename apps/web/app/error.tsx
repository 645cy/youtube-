"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { AlertTriangle, Home, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const router = useRouter()

  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-[68vh] items-center justify-center px-4">
      {/* CRG: Error state keeps debugging detail but matches the high-end control-room surface. */}
      <div className="lux-card max-w-2xl p-6 text-center sm:p-8">
        <div className="mx-auto mb-5 grid h-14 w-14 place-items-center rounded-2xl border border-destructive/25 bg-destructive/10 text-destructive">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">页面遇到问题</h2>
        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
          当前视图没有正确加载。可以重试当前操作，或返回工作台检查集成与数据状态。
        </p>
        {process.env.NODE_ENV === "development" ? (
          <pre className="mt-5 max-h-44 overflow-auto rounded-xl border border-border/70 bg-secondary/60 p-4 text-left text-xs text-muted-foreground">
            {error.message}
            {error.digest ? `\nError ID: ${error.digest}` : ""}
          </pre>
        ) : null}
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Button onClick={reset}>
            <RefreshCw className="h-4 w-4" />
            重试
          </Button>
          <Button variant="outline" onClick={() => router.push("/workspace")}>
            <Home className="h-4 w-4" />
            返回工作台
          </Button>
        </div>
      </div>
    </div>
  )
}

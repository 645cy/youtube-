"use client"

import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import Link from "next/link"

// 动态导入背景层（避免 SSR 问题）
const BackgroundLayer = dynamic(
  () => import("@/components/BackgroundLayer"),
  { ssr: false }
)
import { usePathname } from "next/navigation"
import { ThemeProvider, useTheme } from "next-themes"
import { motion, AnimatePresence } from "framer-motion"
import {
  LayoutDashboard,
  FlaskConical,
  Radar,
  Factory,
  DatabaseZap,
  Menu,
  X,
  Sun,
  Moon,
  Bell,
  Compass,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"

// Toast 类型
interface ToastItem {
  id: string
  type: "success" | "error" | "info"
  message: string
}

/** 导航项配置 */
const NAV_ITEMS = [
  {
    title: "工作台",
    href: "/workspace",
    icon: Compass,
    description: "发现到生产",
  },
  {
    title: "情报总控台",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "频道监控与数据分析",
  },
  {
    title: "OCP实验室",
    href: "/lab",
    icon: FlaskConical,
    description: "变现路径规划",
  },
  {
    title: "竞品雷达",
    href: "/radar",
    icon: Radar,
    description: "竞品增长追踪",
  },
  {
    title: "爬虫任务中心",
    href: "/crawler",
    icon: DatabaseZap,
    description: "任务触发与执行日志",
  },
  {
    title: "内容工厂",
    href: "/factory",
    icon: Factory,
    description: "AI内容生产",
  },
]

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <BackgroundLayer />
      <LayoutInner>{children}</LayoutInner>
    </ThemeProvider>
  )
}

function LayoutInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [toasts, setToasts] = useState<ToastItem[]>([])

  // 监听 Toast 事件
  useEffect(() => {
    const handleToast = (e: Event) => {
      const detail = (e as CustomEvent).detail
      const toast: ToastItem = {
        id: Date.now().toString(),
        type: detail.type,
        message: detail.message,
      }
      setToasts((prev) => [...prev, toast])
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id))
      }, 3000)
    }
    window.addEventListener("api-toast", handleToast)
    return () => window.removeEventListener("api-toast", handleToast)
  }, [])

  // 监听移动端
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false)
      } else {
        setSidebarOpen(true)
      }
    }
    handleResize()
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* 桌面端 Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r bg-card transition-all duration-300 z-40",
          sidebarOpen ? "w-64" : "w-16"
        )}
      >
        {/* Logo */}
        <div className="h-14 flex items-center border-b px-4">
          {sidebarOpen ? (
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <Radar className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="font-bold text-lg">情报总控台</span>
            </Link>
          ) : (
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center mx-auto">
              <Radar className="h-4 w-4 text-primary-foreground" />
            </div>
          )}
        </div>

        {/* 导航 */}
        <ScrollArea className="flex-1 py-4">
          <nav className={cn("grid gap-1", sidebarOpen ? "px-2" : "px-1")}>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                    "hover:bg-accent hover:text-accent-foreground",
                    isActive
                      ? "bg-primary/10 text-primary ring-1 ring-primary/20"
                      : "text-muted-foreground",
                    !sidebarOpen && "justify-center px-2"
                  )}
                  title={!sidebarOpen ? item.title : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {sidebarOpen && (
                    <div className="flex flex-col items-start overflow-hidden">
                      <span className="truncate">{item.title}</span>
                      <span className="text-[10px] text-muted-foreground font-normal truncate">
                        {item.description}
                      </span>
                    </div>
                  )}
                </Link>
              )
            })}
          </nav>
        </ScrollArea>

        {/* 底部操作区 */}
        <div className="border-t p-2 space-y-2">
          <Button
            variant="ghost"
            size="sm"
            className={cn("w-full", !sidebarOpen && "px-0")}
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
            {sidebarOpen && (
              <span className="ml-2">{theme === "dark" ? "亮色" : "暗色"}</span>
            )}
          </Button>
        </div>
      </aside>

      {/* 移动端 Sidebar Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-50 md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 bottom-0 w-[280px] bg-card border-r z-50 flex flex-col md:hidden"
            >
              <div className="h-14 flex items-center justify-between border-b px-4">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2"
                  onClick={() => setMobileOpen(false)}
                >
                  <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                    <Radar className="h-4 w-4 text-primary-foreground" />
                  </div>
                  <span className="font-bold">情报总控台</span>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setMobileOpen(false)}
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <nav className="flex-1 p-4 space-y-2">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon
                  const isActive = pathname === item.href
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-all",
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-muted-foreground hover:bg-accent"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{item.title}</span>
                    </Link>
                  )
                })}
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* 主内容区 */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* 顶部 Header */}
        <header className="h-14 border-b bg-card/50 backdrop-blur flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="hidden md:flex"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            {/* 面包屑 */}
            <span className="text-sm text-muted-foreground hidden sm:inline">
              {NAV_ITEMS.find((item) => item.href === pathname)?.title ||
                "情报总控台"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-[10px] text-white flex items-center justify-center">
                3
              </span>
            </Button>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>

      {/* Toast 容器 */}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              className={cn(
                "pointer-events-auto rounded-xl border p-4 pr-8 shadow-lg max-w-sm relative",
                toast.type === "success" &&
                  "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
                toast.type === "error" &&
                  "border-red-500/30 bg-red-500/10 text-red-400",
                toast.type === "info" &&
                  "border-blue-500/30 bg-blue-500/10 text-blue-400"
              )}
            >
              <p className="text-sm font-medium">{toast.message}</p>
              <button
                onClick={() =>
                  setToasts((prev) => prev.filter((t) => t.id !== toast.id))
                }
                className="absolute top-2 right-2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}

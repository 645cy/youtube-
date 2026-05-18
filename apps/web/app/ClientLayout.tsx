"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ThemeProvider, useTheme } from "next-themes"
import gsap from "gsap"
import {
  BarChart3,
  Bell,
  ChevronLeft,
  ChevronRight,
  Compass,
  DatabaseZap,
  Factory,
  FlaskConical,
  Menu,
  Moon,
  Radar,
  Search,
  Settings,
  Sparkles,
  Sun,
  X,
  Youtube,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import PageFlipTransition from "@/components/transitions/PageFlipTransition"
import BackgroundLayer from "@/components/BackgroundLayer"

interface ToastItem {
  id: string
  type: "success" | "error" | "info" | "warning"
  message: string
}

const NAV_ITEMS = [
  { title: "工作台", href: "/workspace", icon: Compass, detail: "运营总控" },
  { title: "情报总览", href: "/dashboard", icon: BarChart3, detail: "频道与视频" },
  { title: "竞品雷达", href: "/radar", icon: Radar, detail: "增长监控" },
  { title: "爬虫任务", href: "/crawler", icon: DatabaseZap, detail: "数据采集" },
  { title: "频道发现", href: "/discovery", icon: Sparkles, detail: "机会挖掘" },
  { title: "内容工厂", href: "/factory", icon: Factory, detail: "脚本生产" },
  { title: "变现实验室", href: "/lab", icon: FlaskConical, detail: "路径推荐" },
  { title: "接入诊断", href: "/settings/integrations", icon: Settings, detail: "API 健康" },
]

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <BackgroundLayer />
      <LayoutShell>{children}</LayoutShell>
    </ThemeProvider>
  )
}

function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { resolvedTheme, setTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const toastRefs = useRef<Map<string, HTMLDivElement>>(new Map())
  const themeIconRef = useRef<HTMLDivElement>(null)

  useEffect(() => setMounted(true), [])

  useEffect(() => {
    const handleResize = () => setSidebarOpen(window.innerWidth >= 1024)
    handleResize()
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  const removeToast = useCallback((id: string) => {
    const node = toastRefs.current.get(id)
    if (!node) {
      setToasts((items) => items.filter((item) => item.id !== id))
      return
    }
    gsap.to(node, {
      autoAlpha: 0,
      y: -10,
      scale: 0.98,
      duration: 0.24,
      ease: "power2.in",
      onComplete: () => setToasts((items) => items.filter((item) => item.id !== id)),
    })
  }, [])

  useEffect(() => {
    const handleToast = (event: Event) => {
      const detail = (event as CustomEvent).detail
      const toast: ToastItem = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        type: detail.type ?? "info",
        message: detail.message ?? "",
      }
      setToasts((items) => {
        // CRG: Collapse repeated API errors so typography and primary content stay readable under failure states.
        if (items.some((item) => item.type === toast.type && item.message === toast.message)) return items
        return [...items.slice(-1), toast]
      })
      window.setTimeout(() => removeToast(toast.id), detail.duration ?? 3600)
    }
    window.addEventListener("api-toast", handleToast)
    return () => window.removeEventListener("api-toast", handleToast)
  }, [removeToast])

  useEffect(() => {
    toasts.forEach((toast) => {
      const node = toastRefs.current.get(toast.id)
      if (!node || node.dataset.animated === "true") return
      node.dataset.animated = "true"
      gsap.fromTo(
        node,
        { autoAlpha: 0, y: -12, scale: 0.98 },
        { autoAlpha: 1, y: 0, scale: 1, duration: 0.32, ease: "power3.out" }
      )
    })
  }, [toasts])

  const activeItem = useMemo(
    () => NAV_ITEMS.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`)) ?? NAV_ITEMS[0],
    [pathname]
  )
  const isDark = mounted && resolvedTheme === "dark"

  const toggleTheme = useCallback(() => {
    const nextTheme = isDark ? "light" : "dark"
    if (themeIconRef.current) {
      gsap.to(themeIconRef.current, {
        rotate: isDark ? 180 : -180,
        scale: 0.9,
        duration: 0.28,
        ease: "power2.inOut",
        onComplete: () => {
          setTheme(nextTheme)
          gsap.set(themeIconRef.current, { rotate: 0, scale: 1 })
        },
      })
      return
    }
    setTheme(nextTheme)
  }, [isDark, setTheme])

  return (
    <div className="lux-app min-h-screen overflow-hidden text-foreground">
      <DesktopSidebar open={sidebarOpen} pathname={pathname} />
      {mobileOpen ? <MobileSidebar pathname={pathname} onClose={() => setMobileOpen(false)} /> : null}

      <div className={cn("lux-shell transition-[padding] duration-300", sidebarOpen ? "lg:pl-[280px]" : "lg:pl-[88px]")}>
        <header className="lux-topbar">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="打开导航"
            >
              <Menu className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="hidden lg:inline-flex"
              onClick={() => setSidebarOpen((value) => !value)}
              aria-label={sidebarOpen ? "收起导航" : "展开导航"}
            >
              {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
            <div className="min-w-0">
              <p className="lux-kicker">TubeFactory OCP</p>
              <h1 className="lux-card-title truncate text-base text-foreground sm:text-lg">
                {activeItem.title}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="lux-search-pill hidden items-center gap-2 rounded-full border border-border/70 bg-card/70 px-3 py-2 text-xs text-muted-foreground backdrop-blur md:flex">
              {/* CRG: Search pill is visual scaffolding for a premium command bar without wiring a new search API. */}
              <Search className="h-3.5 w-3.5 text-primary" />
              <span>搜索频道、视频、任务</span>
            </div>
            <Button variant="ghost" size="icon" aria-label="通知">
              <Bell className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={toggleTheme} aria-label="切换主题">
              <div ref={themeIconRef} className="grid place-items-center">
                {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </div>
            </Button>
          </div>
        </header>

        <main className="lux-main book-page">
          {/* CRG: Keep the legacy transition wrapper while the redesign replaces the visual shell around it. */}
          <PageFlipTransition>
            <div className="mx-auto w-[calc(100vw-2rem)] max-w-[1480px] py-5 sm:w-full sm:px-6 lg:px-8 lg:py-8">
              {children}
            </div>
          </PageFlipTransition>
        </main>
      </div>

      <ToastStack toasts={toasts} refs={toastRefs} onClose={removeToast} />
    </div>
  )
}

function DesktopSidebar({ open, pathname }: { open: boolean; pathname: string }) {
  return (
    <aside className={cn("lux-sidebar hidden lg:flex", open ? "w-[280px]" : "w-[88px]")}>
      <Link href="/workspace" className={cn("lux-brand", !open && "justify-center")}>
        <span className="lux-brand-mark grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-[0_18px_45px_hsl(var(--primary)/0.24)]">
          <Youtube className="h-5 w-5" />
        </span>
        {open ? (
          <span className="min-w-0">
            {/* CRG: Brand text uses display typography so the shell feels less like a generic admin template. */}
            <span className="block font-display text-xl font-semibold leading-none text-foreground">TubeFactory</span>
            <span className="block text-[10px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">Creator Intelligence</span>
          </span>
        ) : null}
      </Link>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.href} item={item} open={open} active={pathname === item.href || pathname.startsWith(`${item.href}/`)} />
        ))}
      </nav>

      <div className={cn("lux-sidebar-card m-3 rounded-2xl border border-border/70 p-3", !open && "p-2")}>
        {/* CRG: Sidebar status card deepens the luxury shell while preserving the same navigation behavior. */}
        {open ? (
          <>
            <p className="text-xs font-semibold text-foreground">今日控制台</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">轻量查看集成、抓取和内容生产状态。</p>
          </>
        ) : (
          <Sparkles className="mx-auto h-4 w-4 text-primary" />
        )}
      </div>
    </aside>
  )
}

function MobileSidebar({ pathname, onClose }: { pathname: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button type="button" className="absolute inset-0 bg-black/55 backdrop-blur-sm" onClick={onClose} aria-label="关闭导航遮罩" />
      <aside className="lux-sidebar relative h-full w-[304px] max-w-[86vw]">
        <div className="flex items-center justify-between p-4">
          <Link href="/workspace" onClick={onClose} className="lux-brand">
            <span className="lux-brand-mark grid h-10 w-10 place-items-center rounded-2xl bg-primary text-primary-foreground">
              <Youtube className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-bold">TubeFactory</span>
              <span className="block text-[10px] uppercase tracking-[0.2em] text-muted-foreground">OCP</span>
            </span>
          </Link>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="关闭导航">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <nav className="space-y-1 px-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              open
              active={pathname === item.href || pathname.startsWith(`${item.href}/`)}
              onClick={onClose}
            />
          ))}
        </nav>
      </aside>
    </div>
  )
}

function NavLink({
  item,
  open,
  active,
  onClick,
}: {
  item: (typeof NAV_ITEMS)[number]
  open: boolean
  active: boolean
  onClick?: () => void
}) {
  const Icon = item.icon
  const optionalLinkProps = {
    ...(onClick ? { onClick } : {}),
    ...(!open ? { title: item.title } : {}),
  }
  return (
    <Link
      href={item.href}
      {...optionalLinkProps}
      className={cn("lux-nav-item", active && "is-active", !open && "justify-center px-0")}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {open ? (
        <span className="min-w-0">
          {/* CRG: Navigation labels use the refined card-title role for calmer hierarchy. */}
          <span className="lux-card-title block truncate text-sm">{item.title}</span>
          <span className="block truncate text-[11px] text-muted-foreground">{item.detail}</span>
        </span>
      ) : null}
    </Link>
  )
}

function ToastStack({
  toasts,
  refs,
  onClose,
}: {
  toasts: ToastItem[]
  refs: React.MutableRefObject<Map<string, HTMLDivElement>>
  onClose: (id: string) => void
}) {
  return (
    <div className="fixed inset-x-4 bottom-4 z-[100] flex flex-col gap-2 sm:inset-x-auto sm:bottom-auto sm:right-4 sm:top-4 sm:w-[min(420px,calc(100vw-2rem))]">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          ref={(node) => {
            if (node) refs.current.set(toast.id, node)
            else refs.current.delete(toast.id)
          }}
          className={cn("lux-toast", `lux-toast-${toast.type}`)}
        >
          <span className="h-2 w-2 shrink-0 rounded-full bg-current" />
          <p className="min-w-0 flex-1 text-sm font-medium leading-5">{toast.message}</p>
          <button type="button" onClick={() => onClose(toast.id)} className="rounded-full p-1 text-muted-foreground hover:text-foreground">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}

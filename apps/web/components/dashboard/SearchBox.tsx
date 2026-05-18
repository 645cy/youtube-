/**
 * SearchBox 组件 - Phase 3 精致化
 * 增加 paper-card 风格下拉、动画、排版呼吸感
 */

"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Search, SlidersHorizontal, X, TrendingUp, Filter } from "lucide-react"
import { cn, debounce } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useIntelStore } from "@/lib/store"
import { channelApi } from "@/lib/api"
import { mapChannelToIntelChannel } from "@/lib/mappers"
import { toastError } from "@/lib/toast"

interface SearchBoxProps {
  className?: string
}

/** 搜索排序选项 */
const SORT_OPTIONS = [
  { value: "subscribers", label: "订阅数" },
  { value: "growth", label: "增长率" },
  { value: "videos", label: "视频数" },
]

/** 来源分类 */
const SOURCE_TYPES = [
  { value: "youtube", label: "YouTube" },
  { value: "twitter", label: "Twitter" },
  { value: "rss", label: "RSS" },
  { value: "custom", label: "自定义" },
]

export function SearchBox({ className }: SearchBoxProps) {
  const [query, setQuery] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const { searchFilters, setSearchFilters, setSearchQuery, setChannels } = useIntelStore()

  const [isSearching, setIsSearching] = useState(false)

  const latestQueryRef = useRef(query)
  const debouncedSearch = useCallback(
    debounce(async (value: string) => {
      setSearchQuery(value)
      if (value.length >= 2) {
        setShowSuggestions(true)
        try {
          const res = await channelApi.list({ search: value, limit: 5 })
          if (latestQueryRef.current !== value) return
          const items = res?.items || []
          const names = items.map((ch: any) => ch.title).filter(Boolean)
          if (names.length > 0) {
            setSuggestions([...names, `搜索 YouTube 添加「${value}」`])
          } else {
            setSuggestions([`搜索 YouTube 添加「${value}」`])
          }
        } catch {
          if (latestQueryRef.current === value) {
            setSuggestions([`搜索 YouTube 添加「${value}」`])
          }
        }
      } else {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 400),
    []
  )

  useEffect(() => {
    latestQueryRef.current = query
  }, [query])

  useEffect(() => {
    debouncedSearch(query)
  }, [query, debouncedSearch])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false)
        setShowFilters(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleClear = () => {
    setQuery("")
    setSearchQuery("")
    setSuggestions([])
    inputRef.current?.focus()
  }

  const handleSortChange = (sortBy: string) => {
    setSearchFilters({ sortBy })
  }

  const toggleSourceType = (type: string) => {
    const current = searchFilters.categories
    const updated = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type]
    setSearchFilters({ categories: updated })
  }

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      <div className="flex items-center gap-2 p-3 border paper-card page-corner bg-background/80 shadow-[0_1px_0_rgba(255,255,255,0.4)_inset]">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => query.length >= 2 && setShowSuggestions(true)}
            placeholder="搜索频道、情报关键词..."
            className={cn(
              "pl-10 pr-10 h-11 bg-transparent shadow-none border-border/60",
              "focus-visible:ring-primary/30 font-serif tracking-wide"
            )}
          />
          {query && (
            <button
              onClick={handleClear}
              aria-label="清空搜索"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={() => setShowFilters(!showFilters)}
          aria-label={showFilters ? "关闭筛选" : "打开筛选"}
          className={cn("h-11 w-11 shrink-0 border-border/60 bg-background/70", showFilters && "bg-accent border-primary/50")}
        >
          <SlidersHorizontal className="h-4 w-4" />
        </Button>
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden paper-card page-corner animate-page-fade-in bg-popover/95 backdrop-blur">
          <div className="px-4 py-2.5 text-[10px] text-muted-foreground font-serif tracking-[0.18em] uppercase flex items-center gap-1.5">
            <TrendingUp className="inline h-3 w-3" />
            搜索建议
          </div>
          <div className="gold-rule mx-3" />
          {suggestions.map((s, i) => (
            <button
              key={i}
              className="w-full text-left px-4 py-2.5 text-sm hover:bg-accent/50 transition-all duration-200 flex items-center gap-2 tracking-wide"
              onClick={async () => {
                if (s.startsWith("搜索 YouTube 添加")) {
                  const q = query
                  setIsSearching(true)
                  try {
                    const newChannel = await channelApi.search(q)
                    if (newChannel) {
                      const converted = mapChannelToIntelChannel(newChannel)
                      const current = useIntelStore.getState().channels
                      const exists = current.some((channel) => channel.id === converted.id)
                      setChannels(exists ? current : [...current, converted])
                    }
                    setQuery("")
                    setShowSuggestions(false)
                  } catch (e: any) {
                    toastError("搜索失败: " + (e.message || "未知错误"))
                  } finally {
                    setIsSearching(false)
                  }
                } else {
                  setQuery(s)
                  setShowSuggestions(false)
                  setSearchQuery(s)
                }
              }}
            >
              <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              <span className="truncate">{isSearching && s.startsWith("搜索 YouTube") ? "搜索中..." : s}</span>
            </button>
          ))}
        </div>
      )}

      {showFilters && (
        <div className="absolute z-40 mt-2 w-full overflow-hidden paper-card page-corner animate-page-fade-in bg-card/95 backdrop-blur p-5 space-y-5">
          <div>
            <h4 className="text-[10px] font-serif tracking-[0.18em] uppercase text-muted-foreground mb-3 flex items-center gap-1.5">
              <Filter className="h-3 w-3" />
              排序方式
            </h4>
            <div className="flex gap-2 flex-wrap">
              {SORT_OPTIONS.map((opt) => (
                <Badge
                  key={opt.value}
                  variant={searchFilters.sortBy === opt.value ? "default" : "outline"}
                  className="cursor-pointer transition-all duration-200 paper-hover-lift"
                  onClick={() => handleSortChange(opt.value)}
                >
                  {opt.label}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-[10px] font-serif tracking-[0.18em] uppercase text-muted-foreground mb-3">
              来源类型
            </h4>
            <div className="flex gap-2 flex-wrap">
              {SOURCE_TYPES.map((type) => (
                <Badge
                  key={type.value}
                  variant={searchFilters.categories.includes(type.value) ? "default" : "outline"}
                  className="cursor-pointer transition-all duration-200 paper-hover-lift"
                  onClick={() => toggleSourceType(type.value)}
                >
                  {type.label}
                </Badge>
              ))}
            </div>
          </div>

          {(searchFilters.categories.length > 0 || searchFilters.sortBy) && (
            <div className="pt-3 border-t flex items-center justify-between">
              <span className="text-xs text-muted-foreground tracking-wide">
                已启用 {searchFilters.categories.length} 个筛选
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs font-serif tracking-wide"
                onClick={() => setSearchFilters({ categories: [], sortBy: "subscribers" })}
              >
                重置
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

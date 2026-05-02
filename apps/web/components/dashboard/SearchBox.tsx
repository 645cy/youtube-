/**
 * SearchBox 组件 - 情报总控台搜索栏
 * 功能：
 * - 频道/关键词搜索
 * - 防抖自动搜索（300ms）
 * - 搜索建议下拉
 * - 高级筛选面板（分类/状态/排序）
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

  // 防抖搜索（本地过滤 + 后端搜索建议）
  const debouncedSearch = useCallback(
    debounce(async (value: string) => {
      setSearchQuery(value)
      if (value.length >= 2) {
        setShowSuggestions(true)
        // 尝试从数据库搜索匹配的频道名
        try {
          const res = await channelApi.list({ search: value, limit: 5 })
          const items = res?.items || []
          const names = items.map((ch: any) => ch.title).filter(Boolean)
          if (names.length > 0) {
            setSuggestions(names)
          } else {
            setSuggestions([`搜索 YouTube 添加「${value}」`])
          }
        } catch {
          setSuggestions([`搜索 YouTube 添加「${value}」`])
        }
      } else {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 400),
    []
  )

  useEffect(() => {
    debouncedSearch(query)
  }, [query, debouncedSearch])

  // 点击外部关闭建议
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
      {/* 搜索输入框 */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => query.length >= 2 && setShowSuggestions(true)}
            placeholder="搜索频道、情报关键词..."
            className={cn(
              "pl-10 pr-10 h-11 bg-background/50 backdrop-blur",
              "border-muted focus-visible:ring-primary/50"
            )}
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
          className={cn(
            "h-11 w-11 shrink-0",
            showFilters && "bg-accent border-primary/50"
          )}
        >
          <SlidersHorizontal className="h-4 w-4" />
        </Button>
      </div>

      {/* 搜索建议下拉 */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 mt-2 w-full rounded-xl border bg-popover/95 backdrop-blur shadow-xl overflow-hidden">
          <div className="px-3 py-2 text-xs text-muted-foreground font-medium">
            <TrendingUp className="inline h-3 w-3 mr-1" />
            搜索建议
          </div>
          {suggestions.map((s, i) => (
            <button
              key={i}
              className="w-full text-left px-4 py-2.5 text-sm hover:bg-accent transition-colors flex items-center gap-2"
              onClick={async () => {
                if (s.startsWith("搜索 YouTube 添加")) {
                  const q = query
                  setIsSearching(true)
                  try {
                    const newChannel = await channelApi.search(q)
                    // 搜索成功，追加到频道列表
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
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              {isSearching && s.startsWith("搜索 YouTube") ? "搜索中..." : s}
            </button>
          ))}
        </div>
      )}

      {/* 高级筛选面板 */}
      {showFilters && (
        <div className="absolute z-40 mt-2 w-full rounded-xl border bg-card/95 backdrop-blur shadow-xl p-4 space-y-4">
          {/* 排序 */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
              <Filter className="h-3 w-3" />
              排序方式
            </h4>
            <div className="flex gap-2 flex-wrap">
              {SORT_OPTIONS.map((opt) => (
                <Badge
                  key={opt.value}
                  variant={
                    searchFilters.sortBy === opt.value ? "default" : "outline"
                  }
                  className="cursor-pointer"
                  onClick={() => handleSortChange(opt.value)}
                >
                  {opt.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* 来源类型 */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2">
              来源类型
            </h4>
            <div className="flex gap-2 flex-wrap">
              {SOURCE_TYPES.map((type) => (
                <Badge
                  key={type.value}
                  variant={
                    searchFilters.categories.includes(type.value)
                      ? "default"
                      : "outline"
                  }
                  className="cursor-pointer"
                  onClick={() => toggleSourceType(type.value)}
                >
                  {type.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* 当前激活的筛选 */}
          {(searchFilters.categories.length > 0 || searchFilters.sortBy) && (
            <div className="pt-2 border-t flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                已启用 {searchFilters.categories.length} 个筛选
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={() =>
                  setSearchFilters({ categories: [], sortBy: "subscribers" })
                }
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
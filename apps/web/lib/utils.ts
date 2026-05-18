/**
 * 工具函数库
 * - cn(): className 合并工具（clsx + tailwind-merge）
 * - formatNumber(): 数字格式化
 * - formatDate(): 日期格式化
 */

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * 合并 TailwindCSS className
 * 使用 clsx 处理条件类，tailwind-merge 解决冲突
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 格式化数字（千分位 + 缩写）
 * 例: 1234567 → "1.2M"
 *     12345 → "12.3K"
 */
export function formatCompactNumber(num: number): string {
  const n = typeof num === "number" && Number.isFinite(num) ? num : 0
  if (n >= 1_000_000) {
    return (n / 1_000_000).toFixed(1) + "M"
  }
  if (n >= 1_000) {
    return (n / 1_000).toFixed(1) + "K"
  }
  return n.toString()
}

/**
 * 格式化数字（千分位）
 * 例: 1234567 → "1,234,567"
 */
export function formatNumber(num: number): string {
  const n = typeof num === "number" && Number.isFinite(num) ? num : 0
  return n.toLocaleString("zh-CN")
}

/**
 * 格式化日期
 * 例: 2024-01-15T08:30:00 → "2024-01-15 08:30"
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date
  if (Number.isNaN(d.getTime())) return "-"
  return d.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

/**
 * 格式化相对时间
 * 例: 2024-01-15T08:30:00 → "3小时前"
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date
  if (Number.isNaN(d.getTime())) return "-"
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  if (diffMs < 0) return "刚刚"
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMinutes < 60) return diffMinutes + "分钟前"
  if (diffHours < 24) return diffHours + "小时前"
  if (diffDays < 30) return diffDays + "天前"
  return d.toLocaleDateString("zh-CN")
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

/**
 * 休眠函数（异步延迟）
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
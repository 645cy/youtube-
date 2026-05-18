"use client"

interface KeyValueProps {
  label: string
  value?: string | number
}

export function KeyValue({ label, value }: KeyValueProps) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground tracking-wide">{label}</span>
      <span className="text-xs font-medium tabular-nums">{value ?? "-"}</span>
    </div>
  )
}

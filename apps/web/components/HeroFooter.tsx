export function HeroFooter({ segment }: { segment?: string }) {
  const year = new Date().getFullYear()
  return (
    <div className="relative z-10 mt-5 flex min-w-0 flex-wrap items-center gap-3 text-xs text-muted-foreground">
      {/* CRG: Keep this tiny shared footer for existing pages while aligning it with the new control-room tone. */}
      <span className="font-semibold text-foreground/80">TubeFactory</span>
      <div className="h-px min-w-12 flex-1 bg-border/80" />
      <span className="w-full shrink-0 tabular-nums sm:w-auto">{segment ? `${segment} · ${year}` : year}</span>
    </div>
  )
}

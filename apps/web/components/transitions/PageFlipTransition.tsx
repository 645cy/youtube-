"use client"

import { useEffect, useRef } from "react"
import { usePathname } from "next/navigation"
import gsap from "gsap"

interface PageFlipTransitionProps {
  children: React.ReactNode
}

export default function PageFlipTransition({ children }: PageFlipTransitionProps) {
  const pathname = usePathname()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (prefersReduced) return
    // CRG: Keep the legacy component contract but replace book-flip motion with a calmer dashboard transition.
    gsap.fromTo(
      ref.current,
      { autoAlpha: 0, y: 14, filter: "blur(6px)" },
      { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.42, ease: "power3.out" }
    )
  }, [pathname])

  return (
    <div ref={ref} className="relative min-h-full w-full">
      {children}
    </div>
  )
}

"use client"

import { useEffect, useRef } from "react"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

// SSR-safe plugin registration
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger)
}

export type ScrollRevealDirection = "up" | "down" | "left" | "right" | "scale"

interface UseGSAPScrollRevealOptions {
  /** Animation direction */
  direction?: ScrollRevealDirection
  /** Distance to travel (px) */
  distance?: number
  /** Initial opacity */
  opacity?: number
  /** Animation duration (s) */
  duration?: number
  /** Delay before animation starts (s) */
  delay?: number
  /** Easing function */
  ease?: string
  /** Stagger delay between children (s) */
  stagger?: number
  /** ScrollTrigger start position */
  start?: string
  /** ScrollTrigger end position */
  end?: string
  /** Whether to animate children instead of container */
  children?: boolean
  /** Whether animation should only play once */
  once?: boolean
  /** Additional GSAP from vars */
  fromVars?: gsap.TweenVars
  /** Additional GSAP to vars */
  toVars?: gsap.TweenVars
}

/**
 * GSAP ScrollTrigger reveal animation Hook
 * Triggers entrance animation when element enters viewport.
 * Auto-cleans up ScrollTrigger instances on unmount.
 */
export function useGSAPScrollReveal<T extends HTMLElement>(
  options: UseGSAPScrollRevealOptions = {}
) {
  const ref = useRef<T>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const {
      direction = "up",
      distance = 32,
      opacity = 0,
      duration = 0.6,
      delay = 0,
      ease = "power3.out",
      stagger = 0.08,
      start = "top 88%",
      end = "bottom 12%",
      children: animateChildren = false,
      once = true,
      fromVars = {},
      toVars = {},
    } = options

    const targets = animateChildren && el.children.length > 0
      ? Array.from(el.children)
      : el

    const from: gsap.TweenVars = { opacity, ...fromVars }

    switch (direction) {
      case "up":
        from.y = distance
        break
      case "down":
        from.y = -distance
        break
      case "left":
        from.x = distance
        break
      case "right":
        from.x = -distance
        break
      case "scale":
        from.scale = 0.92
        break
    }

    gsap.set(targets, from)

    const anim = gsap.to(targets, {
      x: 0,
      y: 0,
      scale: 1,
      opacity: 1,
      duration,
      delay,
      ease,
      stagger: animateChildren ? stagger : 0,
      scrollTrigger: {
        trigger: el,
        start,
        end,
        toggleActions: once ? "play none none none" : "play reverse play reverse",
      },
      ...toVars,
    })

    return () => {
      anim.kill()
      if (anim.scrollTrigger) {
        anim.scrollTrigger.kill()
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return ref
}

/**
 * GSAP ScrollTrigger counter animation Hook
 * Animates a number counting up when scrolled into view.
 */
export function useGSAPScrollCounter(
  value: number,
  options?: {
    duration?: number
    ease?: string
    start?: string
  }
) {
  const ref = useRef<HTMLSpanElement>(null)
  const hasAnimatedRef = useRef(false)
  const prevValueRef = useRef(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const duration = options?.duration ?? 1.2
    const ease = options?.ease ?? "power2.out"
    const start = options?.start ?? "top 88%"

    const from = prevValueRef.current
    const to = value

    const obj = { val: from }

    const anim = gsap.to(obj, {
      val: to,
      duration,
      ease,
      scrollTrigger: {
        trigger: el,
        start,
        toggleActions: "play none none none",
        onEnter: () => {
          if (hasAnimatedRef.current) return
          hasAnimatedRef.current = true
        },
      },
      onUpdate: () => {
        el.textContent = Math.round(obj.val).toLocaleString()
      },
    })

    prevValueRef.current = to

    return () => {
      anim.kill()
      if (anim.scrollTrigger) {
        anim.scrollTrigger.kill()
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return ref
}

/**
 * Batch apply scroll reveal to multiple refs.
 * Useful when you need dynamic stagger without a single parent wrapper.
 */
export function useGSAPScrollRevealBatch(
  count: number,
  options: UseGSAPScrollRevealOptions = {}
) {
  const refs = useRef<(HTMLElement | null)[]>([])

  useEffect(() => {
    if (count === 0) return

    const {
      direction = "up",
      distance = 32,
      opacity = 0,
      duration = 0.6,
      delay = 0,
      ease = "power3.out",
      stagger = 0.08,
      start = "top 88%",
      once = true,
      fromVars = {},
      toVars = {},
    } = options

    const validEls = refs.current.filter(Boolean) as HTMLElement[]
    if (validEls.length === 0) return

    const from: gsap.TweenVars = { opacity, ...fromVars }

    switch (direction) {
      case "up":
        from.y = distance
        break
      case "down":
        from.y = -distance
        break
      case "left":
        from.x = distance
        break
      case "right":
        from.x = -distance
        break
      case "scale":
        from.scale = 0.92
        break
    }

    gsap.set(validEls, from)

    const anim = gsap.to(validEls, {
      x: 0,
      y: 0,
      scale: 1,
      opacity: 1,
      duration,
      delay,
      ease,
      stagger,
      scrollTrigger: {
        trigger: validEls[0],
        start,
        toggleActions: once ? "play none none none" : "play reverse play reverse",
      },
      ...toVars,
    })

    return () => {
      anim.kill()
      if (anim.scrollTrigger) {
        anim.scrollTrigger.kill()
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count])

  const setRef = (index: number) => (el: HTMLElement | null) => {
    refs.current[index] = el
  }

  return setRef
}

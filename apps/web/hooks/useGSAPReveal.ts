"use client"

import { useEffect, useRef } from "react"
import gsap from "gsap"

/**
 * GSAP 元素 reveal 动画 Hook
 * 元素进入视口时触发 stagger 入场动画
 */
export function useGSAPReveal<T extends HTMLElement>(
  options?: {
    y?: number
    opacity?: number
    duration?: number
    delay?: number
    ease?: string
    stagger?: number
  }
) {
  const ref = useRef<T>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const children = el.children.length > 0 ? el.children : [el]

    gsap.set(children, {
      y: options?.y ?? 20,
      opacity: options?.opacity ?? 0,
    })

    const anim = gsap.to(children, {
      y: 0,
      opacity: 1,
      duration: options?.duration ?? 0.6,
      delay: options?.delay ?? 0.1,
      ease: options?.ease ?? "power3.out",
      stagger: options?.stagger ?? 0.08,
    })

    return () => {
      anim.kill()
    }
  }, [options?.y, options?.opacity, options?.duration, options?.delay, options?.ease, options?.stagger])

  return ref
}

/**
 * GSAP 数字滚动动画 Hook
 */
export function useGSAPCounter(
  value: number,
  options?: {
    duration?: number
    delay?: number
    ease?: string
  }
) {
  const ref = useRef<HTMLSpanElement>(null)
  const prevValueRef = useRef(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const from = prevValueRef.current
    const to = value

    const obj = { val: from }
    const anim = gsap.to(obj, {
      val: to,
      duration: options?.duration ?? 1.2,
      delay: options?.delay ?? 0.2,
      ease: options?.ease ?? "power2.out",
      onUpdate: () => {
        el.textContent = Math.round(obj.val).toLocaleString()
      },
    })

    prevValueRef.current = to

    return () => {
      anim.kill()
    }
  }, [value, options?.duration, options?.delay, options?.ease])

  return ref
}

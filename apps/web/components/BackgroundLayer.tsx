"use client"

import { useEffect, useRef } from "react"

/**
 * HUD 深空背景层
 * 参考 health-ai-butler 的 SceneBackground 设计
 * 纯 CSS 实现：多层渐变 + 网格 + 粒子 + 扫描线 + 暗角
 */
export default function BackgroundLayer() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // 粒子动画（轻量 canvas）
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animationId: number
    let w: number, h: number

    interface Particle {
      x: number
      y: number
      vx: number
      vy: number
      size: number
      alpha: number
      hue: number
    }

    const particles: Particle[] = []
    const PARTICLE_COUNT = 180

    function resize() {
      w = canvas!.width = window.innerWidth
      h = canvas!.height = window.innerHeight
    }

    function initParticles() {
      particles.length = 0
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          size: Math.random() * 1.5 + 0.3,
          alpha: Math.random() * 0.5 + 0.2,
          hue: 160 + Math.random() * 40,
        })
      }
    }

    function draw() {
      ctx!.clearRect(0, 0, w, h)

      for (const p of particles) {
        p.x += p.vx
        p.y += p.vy

        // 边界环绕
        if (p.x < 0) p.x = w
        if (p.x > w) p.x = 0
        if (p.y < 0) p.y = h
        if (p.y > h) p.y = 0

        ctx!.beginPath()
        ctx!.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx!.fillStyle = `hsla(${p.hue}, 70%, 60%, ${p.alpha})`
        ctx!.fill()
      }

      // 连接线（距离近的粒子）
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx!.beginPath()
            ctx!.moveTo(particles[i].x, particles[i].y)
            ctx!.lineTo(particles[j].x, particles[j].y)
            ctx!.strokeStyle = `hsla(170, 60%, 50%, ${0.06 * (1 - dist / 120)})`
            ctx!.lineWidth = 0.5
            ctx!.stroke()
          }
        }
      }

      animationId = requestAnimationFrame(draw)
    }

    resize()
    initParticles()
    draw()

    window.addEventListener("resize", resize)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener("resize", resize)
    }
  }, [])

  return (
    // CRG: keep the HUD atmosphere strong in dark mode without washing out the light theme.
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden opacity-20 dark:opacity-100 transition-opacity duration-300">
      {/* 基础渐变背景 */}
      <div className="absolute inset-0 bg-hud-gradient" />

      {/* 网格叠加 */}
      <div className="absolute inset-0 bg-grid-overlay animate-[grid-pulse_8s_ease-in-out_infinite]" />

      {/* 粒子层 */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ opacity: 0.7 }}
      />

      {/* 顶部光束 */}
      <div
        className="absolute inset-x-0 top-0 h-[45%] bg-godray"
        style={{ transform: "translateY(-10%)" }}
      />

      {/* 底部辉光 */}
      <div
        className="absolute left-1/2 bottom-0 w-[60%] h-[40%] -translate-x-1/2"
        style={{
          background:
            "radial-gradient(ellipse at 50% 100%, rgba(57,255,208,0.08), transparent 55%)",
          filter: "blur(30px)",
        }}
      />

      {/* 暗角 */}
      <div className="absolute inset-0 bg-vignette" />

      {/* 扫描线 */}
      <div className="scan-line" />

      {/* 噪点纹理 */}
      <div
        className="absolute inset-0 opacity-[0.035] mix-blend-screen"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 220 220' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E")`,
          backgroundSize: "180px 180px",
        }}
      />
    </div>
  )
}

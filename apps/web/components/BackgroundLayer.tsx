"use client"

import { Suspense, useEffect, useMemo, useRef, useState } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { useTheme } from "next-themes"
import * as THREE from "three"

const NODE_COUNT = 150
const LINE_COUNT = 70

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

function isLowEndDevice() {
  if (typeof navigator === "undefined") return true
  const nav = navigator as Navigator & { deviceMemory?: number }
  return (navigator.hardwareConcurrency ?? 2) <= 4 || (nav.deviceMemory ?? 4) <= 4
}

function IntelligenceField({ dark }: { dark: boolean }) {
  const pointsRef = useMemo(() => ({ current: null as THREE.Points | null }), [])
  const linesRef = useMemo(() => ({ current: null as THREE.LineSegments | null }), [])
  const ringsRef = useRef<THREE.Group>(null)

  const geometry = useMemo(() => {
    const positions = new Float32Array(NODE_COUNT * 3)
    const colors = new Float32Array(NODE_COUNT * 3)
    for (let i = 0; i < NODE_COUNT; i += 1) {
      const r = 5 + (i % 17) * 0.08
      const a = i * 2.399963
      positions[i * 3] = Math.cos(a) * r + (Math.sin(i * 1.7) * 0.8)
      positions[i * 3 + 1] = Math.sin(a) * r * 0.52 + (Math.cos(i * 0.9) * 0.6)
      positions[i * 3 + 2] = ((i % 11) - 5) * 0.42
      colors[i * 3] = dark ? 0.86 : 0.72
      colors[i * 3 + 1] = dark ? 0.68 : 0.56
      colors[i * 3 + 2] = dark ? 0.42 : 0.33
    }
    return { positions, colors }
  }, [dark])

  const lineGeometry = useMemo(() => {
    const positions = new Float32Array(LINE_COUNT * 2 * 3)
    for (let i = 0; i < LINE_COUNT; i += 1) {
      const from = (i * 7) % NODE_COUNT
      const to = (from + 13 + (i % 9)) % NODE_COUNT
      positions.set(geometry.positions.slice(from * 3, from * 3 + 3), i * 6)
      positions.set(geometry.positions.slice(to * 3, to * 3 + 3), i * 6 + 3)
    }
    return positions
  }, [geometry.positions])

  const pointMaterial = useMemo(
    () =>
      new THREE.PointsMaterial({
        size: dark ? 0.045 : 0.035,
        transparent: true,
        opacity: dark ? 0.48 : 0.36,
        vertexColors: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    [dark]
  )

  const lineMaterial = useMemo(
    () =>
      new THREE.LineBasicMaterial({
        color: dark ? "#d7b675" : "#b8985f",
        transparent: true,
        opacity: dark ? 0.12 : 0.08,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    [dark]
  )

  const ringMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: dark ? "#e4c27b" : "#b99658",
        transparent: true,
        opacity: dark ? 0.08 : 0.055,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    [dark]
  )

  useFrame(({ clock, pointer }) => {
    const t = clock.elapsedTime
    if (pointsRef.current) {
      pointsRef.current.rotation.z = t * 0.012
      pointsRef.current.rotation.x = pointer.y * 0.035
      pointsRef.current.rotation.y = pointer.x * 0.035
    }
    if (linesRef.current) {
      linesRef.current.rotation.z = -t * 0.008
      linesRef.current.rotation.y = pointer.x * 0.02
    }
    if (ringsRef.current) {
      // CRG: Slow orbital motion adds premium depth without becoming an attention-heavy animation.
      ringsRef.current.rotation.z = t * 0.018
      ringsRef.current.rotation.x = 0.42 + pointer.y * 0.025
      ringsRef.current.rotation.y = pointer.x * 0.04
    }
  })

  return (
    <group position={[0, 0, -1]}>
      {/* CRG: The field is decorative only, so all geometry stays isolated from page state and API data. */}
      <points ref={(node) => { pointsRef.current = node }} material={pointMaterial}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={NODE_COUNT} array={geometry.positions} itemSize={3} />
          <bufferAttribute attach="attributes-color" count={NODE_COUNT} array={geometry.colors} itemSize={3} />
        </bufferGeometry>
      </points>
      <lineSegments ref={(node) => { linesRef.current = node }} material={lineMaterial}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" count={LINE_COUNT * 2} array={lineGeometry} itemSize={3} />
        </bufferGeometry>
      </lineSegments>
      <group ref={ringsRef} position={[1.1, -0.2, -0.8]} rotation={[0.42, 0, 0.18]}>
        <mesh material={ringMaterial}>
          <torusGeometry args={[3.25, 0.006, 8, 160]} />
        </mesh>
        <mesh material={ringMaterial} rotation={[0, 0, Math.PI / 2.8]}>
          <torusGeometry args={[2.35, 0.005, 8, 140]} />
        </mesh>
        <mesh material={ringMaterial} rotation={[0, 0, -Math.PI / 3.4]}>
          <torusGeometry args={[4.05, 0.004, 8, 180]} />
        </mesh>
      </group>
    </group>
  )
}

export default function BackgroundLayer() {
  const { resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [canvasEnabled, setCanvasEnabled] = useState(false)
  const [pointer, setPointer] = useState({ x: 68, y: 24 })
  const dark = resolvedTheme === "dark"

  useEffect(() => {
    setMounted(true)
    setCanvasEnabled(!isLowEndDevice() && !prefersReducedMotion())
  }, [])

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      // CRG: Pointer light is CSS-only and decorative, so it cannot disturb app data or layout.
      setPointer({
        x: Math.round((event.clientX / window.innerWidth) * 100),
        y: Math.round((event.clientY / window.innerHeight) * 100),
      })
    }
    window.addEventListener("pointermove", handlePointerMove, { passive: true })
    return () => window.removeEventListener("pointermove", handlePointerMove)
  }, [])

  if (!mounted) return null

  return (
    <div
      className="lux-background fixed inset-0 z-0 overflow-hidden pointer-events-none"
      style={{ "--lux-pointer-x": `${pointer.x}%`, "--lux-pointer-y": `${pointer.y}%` } as React.CSSProperties}
      aria-hidden
    >
      <div className="lux-background-media" />
      <div className="lux-background-grid" />
      <div className="lux-pointer-light" />
      {canvasEnabled ? (
        <Canvas
          camera={{ position: [0, 0, 8], fov: 52 }}
          dpr={[1, 1.5]}
          gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
          style={{ position: "absolute", inset: 0 }}
        >
          <Suspense fallback={null}>
            <IntelligenceField dark={dark} />
          </Suspense>
        </Canvas>
      ) : (
        <div className="lux-background-static" />
      )}
    </div>
  )
}

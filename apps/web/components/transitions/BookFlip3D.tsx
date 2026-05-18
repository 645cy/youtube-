"use client"

import { useRef, useEffect, useState } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import * as THREE from "three"

interface BookPageMeshProps {
  isFlipping: boolean
}

/**
 * 3D 书页模型
 * - 正面 + 背面 Plane 模拟纸张两面
 * - 薄 Box 模拟厚度边缘
 * - 绕左侧装订线翻转
 */
function BookPageMesh({ isFlipping }: BookPageMeshProps) {
  const groupRef = useRef<THREE.Group>(null)
  const progressRef = useRef(0)

  const pageWidth = 3.2
  const pageHeight = 4.2
  const pageThickness = 0.015

  useEffect(() => {
    progressRef.current = 0
    if (groupRef.current) {
      groupRef.current.rotation.y = -Math.PI / 2
    }
  }, [isFlipping])

  useFrame((_, delta) => {
    if (!groupRef.current || !isFlipping) return
    const speed = 2.8
    progressRef.current = Math.min(progressRef.current + delta * speed, 1)
    // ease-out cubic
    const eased = 1 - Math.pow(1 - progressRef.current, 3)
    groupRef.current.rotation.y = (-Math.PI / 2) * (1 - eased)
  })

  return (
    <group ref={groupRef} rotation-y={-Math.PI / 2}>
      {/* 正面 */}
      <mesh position={[pageWidth / 2, 0, pageThickness / 2 + 0.001]}>
        <planeGeometry args={[pageWidth, pageHeight]} />
        <meshPhysicalMaterial
          color="#f5f0e6"
          roughness={0.88}
          metalness={0.0}
          clearcoat={0.05}
          side={THREE.FrontSide}
        />
      </mesh>
      {/* 背面 */}
      <mesh position={[pageWidth / 2, 0, -pageThickness / 2 - 0.001]} rotation-y={Math.PI}>
        <planeGeometry args={[pageWidth, pageHeight]} />
        <meshPhysicalMaterial
          color="#ede6d8"
          roughness={0.88}
          metalness={0.0}
          clearcoat={0.05}
          side={THREE.FrontSide}
        />
      </mesh>
      {/* 厚度边缘（薄层） */}
      <mesh position={[pageWidth / 2, 0, 0]}>
        <boxGeometry args={[pageWidth, pageHeight, pageThickness]} />
        <meshPhysicalMaterial
          color="#dcd4c4"
          roughness={0.92}
          metalness={0.0}
          transparent
          opacity={0.6}
        />
      </mesh>
      {/* 右侧边缘高光条 */}
      <mesh position={[pageWidth - 0.01, 0, 0]}>
        <boxGeometry args={[0.008, pageHeight * 0.96, pageThickness + 0.004]} />
        <meshPhysicalMaterial
          color="#fff8ee"
          roughness={0.6}
          metalness={0.1}
          transparent
          opacity={0.25}
        />
      </mesh>
    </group>
  )
}

interface BookFlip3DProps {
  trigger: number
}

/**
 * 3D 书页翻书过渡效果（装饰层）
 * 仅在支持 WebGL 的客户端设备上渲染
 */
export default function BookFlip3D({ trigger }: BookFlip3DProps) {
  const [visible, setVisible] = useState(false)
  const [isFlipping, setIsFlipping] = useState(false)

  useEffect(() => {
    if (trigger <= 0) return
    setVisible(true)
    setIsFlipping(true)
    const timer = setTimeout(() => {
      setIsFlipping(false)
    }, 600)
    const fadeTimer = setTimeout(() => {
      setVisible(false)
    }, 850)
    return () => {
      clearTimeout(timer)
      clearTimeout(fadeTimer)
    }
  }, [trigger])

  if (!visible) return null

  return (
    <div
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 9999, opacity: 1, transition: "opacity 0.3s ease" }}
    >
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[4, 4, 5]} intensity={0.7} color="#fff5e6" />
        <pointLight position={[-1, 2, 3]} intensity={0.4} color="#ffe8cc" />
        <BookPageMesh isFlipping={isFlipping} />
      </Canvas>
    </div>
  )
}

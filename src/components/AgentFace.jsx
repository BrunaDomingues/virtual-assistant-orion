import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'
import FaceMesh from './FaceMesh'

// ── Scene sub-components (rendered inside Canvas) ─────────────────────────────

/** Primary thin torus that rotates and glows based on aiState. */
function StatusRing({ aiState }) {
  const meshRef = useRef()

  useFrame(({ clock }) => {
    if (!meshRef.current) return
    const t     = clock.getElapsedTime()
    const speed = aiState === 'speaking' ? 2.8 : aiState === 'listening' ? 1.3 : aiState === 'standby' ? 0.7 : 0.45
    meshRef.current.rotation.z += 0.01 * speed
    meshRef.current.rotation.x  = Math.sin(t * 0.45) * 0.22
    const opacity =
      aiState === 'speaking'  ? 0.88 :
      aiState === 'listening' ? 0.58 :
      aiState === 'standby'   ? 0.38 : 0.28
    meshRef.current.material.opacity = opacity
    const hue   = aiState === 'speaking' ? 0.75 : 0.52   // purple vs cyan
    const color = new THREE.Color().setHSL(hue, 0.9, 0.65)
    meshRef.current.material.color.copy(color)
  })

  return (
    <mesh ref={meshRef} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[1.1, 0.007, 8, 128]} />
      <meshBasicMaterial color="#22d3ee" transparent opacity={0.28} />
    </mesh>
  )
}

/** Secondary outer torus rotating in the opposite direction. */
function SecondaryRing() {
  const meshRef = useRef()

  useFrame(({ clock }) => {
    if (!meshRef.current) return
    meshRef.current.rotation.z -= 0.005
    meshRef.current.rotation.x  = Math.sin(clock.getElapsedTime() * 0.3) * 0.18
    meshRef.current.rotation.y += 0.003
  })

  return (
    <mesh ref={meshRef} rotation={[Math.PI / 3, 0, 0]}>
      <torusGeometry args={[1.38, 0.004, 8, 128]} />
      <meshBasicMaterial color="#22d3ee" transparent opacity={0.13} />
    </mesh>
  )
}

/** Thin horizontal plane that sweeps up and down in a sine loop. */
function ScanLine() {
  const meshRef = useRef()

  useFrame(({ clock }) => {
    if (!meshRef.current) return
    const t = clock.getElapsedTime()
    meshRef.current.position.y   = Math.sin(t * 0.65) * 1.05
    meshRef.current.material.opacity = 0.12 + Math.abs(Math.sin(t * 0.65)) * 0.1
  })

  return (
    <mesh ref={meshRef}>
      <planeGeometry args={[3.2, 0.004]} />
      <meshBasicMaterial color="#22d3ee" transparent opacity={0.12} />
    </mesh>
  )
}

/** ~320 random background particles rotating slowly. */
function BackgroundParticles() {
  const groupRef = useRef()

  const geo = useMemo(() => {
    const pos = new Float32Array(320 * 3)
    for (let i = 0; i < 320; i++) {
      pos[i * 3]     = (Math.random() - 0.5) * 9
      pos[i * 3 + 1] = (Math.random() - 0.5) * 9
      pos[i * 3 + 2] = -2.5 + (Math.random() - 0.5) * 3
    }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    return g
  }, [])

  useFrame(() => {
    if (!groupRef.current) return
    groupRef.current.rotation.y += 0.0004
    groupRef.current.rotation.x += 0.00018
  })

  return (
    <group ref={groupRef}>
      <points geometry={geo}>
        <pointsMaterial
          size={0.016}
          color="#22d3ee"
          transparent
          opacity={0.28}
          sizeAttenuation
        />
      </points>
    </group>
  )
}

// ── Canvas root ───────────────────────────────────────────────────────────────

/**
 * AgentFace
 *
 * Props:
 *   aiState      – 'idle' | 'listening' | 'speaking'
 *   blendShapes  – Record<string, number>
 *   voiceJawRef  – React.MutableRefObject<number>  0–1
 *   onLoaded     – () => void  fired when OBJ mesh is ready
 */
export default function AgentFace({ aiState, blendShapes, voiceJawRef, onLoaded }) {
  return (
    <Canvas
      camera={{ position: [0, 0, 2.8], fov: 45 }}
      gl={{ antialias: true }}
      style={{ width: '100%', height: '100%' }}
    >
      <color attach="background" args={['#050505']} />

      {/* Subtle fill lights in cyan to contribute to bloom */}
      <ambientLight intensity={0.08} />
      <pointLight position={[2,  2, 2]}  intensity={0.6}  color="#22d3ee" />
      <pointLight position={[-2, -2, 2]} intensity={0.3}  color="#0ea5e9" />

      <OrbitControls enablePan={false} minDistance={1.6} maxDistance={6} />

      <BackgroundParticles />
      <FaceMesh
        aiState={aiState}
        blendShapes={blendShapes}
        voiceJawRef={voiceJawRef}
        onLoaded={onLoaded}
      />
      <StatusRing    aiState={aiState} />
      <SecondaryRing />
      <ScanLine />

      <EffectComposer>
        <Bloom
          intensity={0.85}
          luminanceThreshold={0.08}
          luminanceSmoothing={0.9}
          mipmapBlur
        />
      </EffectComposer>
    </Canvas>
  )
}

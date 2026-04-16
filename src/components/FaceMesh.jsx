import { useRef, useState, useEffect, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import {
  loadFaceModel,
  MOUTH_UPPER,
  MOUTH_LOWER,
  JAW_INDICES,
  LEFT_EYE_INDICES,
  RIGHT_EYE_INDICES,
} from '../data/faceLandmarks'

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Build a flat array of alternating vertex-index pairs for every unique edge. */
function buildEdgeList(indices) {
  const seen = new Set()
  const list = []
  for (let i = 0; i < indices.length; i += 3) {
    const a = indices[i], b = indices[i + 1], c = indices[i + 2]
    for (const [u, v] of [[a, b], [b, c], [a, c]]) {
      const key = u < v ? `${u}|${v}` : `${v}|${u}`
      if (!seen.has(key)) { seen.add(key); list.push(u, v) }
    }
  }
  return list // length = 2 * numEdges
}

/** Average position of a set of vertex indices. */
function centroid(positions, indices) {
  let x = 0, y = 0, z = 0
  for (const i of indices) {
    x += positions[i * 3]; y += positions[i * 3 + 1]; z += positions[i * 3 + 2]
  }
  return [x / indices.length, y / indices.length, z / indices.length]
}

/** Average XY-plane distance from a set of vertices to a centre point. */
function ringRadius(positions, indices, cx, cy) {
  let r = 0
  for (const i of indices) {
    const dx = positions[i * 3] - cx
    const dy = positions[i * 3 + 1] - cy
    r += Math.sqrt(dx * dx + dy * dy)
  }
  return r / indices.length
}

/** Procedural noise value for a vertex index at time t. */
function noise(i, t, amp) {
  return Math.sin(i * 7.31 + t * 2.1) * Math.cos(i * 3.73 + t * 1.7) * amp
}

/**
 * Synthetic jaw-open value when no voice/MediaPipe input is present.
 * Produces a natural-feeling open/close oscillation.
 */
function simulateJaw(t) {
  return Math.max(0, Math.sin(t * 4.5) * 0.5 + Math.sin(t * 7.3) * 0.3)
}

// ── Sub-components ────────────────────────────────────────────────────────────

/** Animated torus ring for each eye. */
function EyeRing({ center, radius }) {
  const meshRef = useRef()
  useFrame(({ clock }) => {
    if (!meshRef.current) return
    const t = clock.getElapsedTime()
    meshRef.current.material.opacity = 0.35 + 0.25 * Math.abs(Math.sin(t * 1.6))
  })
  return (
    <mesh ref={meshRef} position={center}>
      <torusGeometry args={[radius, radius * 0.065, 6, 52]} />
      <meshBasicMaterial color="#22d3ee" transparent opacity={0.45} />
    </mesh>
  )
}

/** Wireframe icosahedron shown while the OBJ is loading. */
function LoadingFallback() {
  const meshRef = useRef()
  useFrame(({ clock }) => {
    if (!meshRef.current) return
    const t = clock.getElapsedTime()
    meshRef.current.scale.setScalar(1 + Math.sin(t * 2) * 0.04)
    meshRef.current.material.opacity = 0.18 + Math.abs(Math.sin(t * 1.3)) * 0.14
  })
  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[0.55, 2]} />
      <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.22} />
    </mesh>
  )
}

// ── FaceMeshRenderer (needs faceData) ─────────────────────────────────────────

function FaceMeshRenderer({ faceData, aiState, blendShapes, voiceJawRef }) {
  const groupRef = useRef()

  /**
   * Create all mutable geometry objects once per faceData change.
   * Both pointsMesh and lineMesh reference typed arrays we mutate every frame.
   */
  const { pointsMesh, lineMesh, anim } = useMemo(() => {
    const base    = faceData.positions                 // Float32Array — read-only source
    const deform  = new Float32Array(base)             // mutable deformed positions
    const edgeList = buildEdgeList(faceData.indices)   // flat array [u0,v0, u1,v1, ...]
    const wirePos  = new Float32Array(edgeList.length * 3)

    // Initialise wire positions from base
    for (let i = 0; i < edgeList.length; i++) {
      const vi = edgeList[i] * 3
      wirePos[i * 3]     = base[vi]
      wirePos[i * 3 + 1] = base[vi + 1]
      wirePos[i * 3 + 2] = base[vi + 2]
    }

    const pointsGeo = new THREE.BufferGeometry()
    pointsGeo.setAttribute('position', new THREE.BufferAttribute(deform, 3))

    const wireGeo = new THREE.BufferGeometry()
    wireGeo.setAttribute('position', new THREE.BufferAttribute(wirePos, 3))

    const pm = new THREE.Points(
      pointsGeo,
      new THREE.PointsMaterial({ size: 0.004, color: '#22d3ee', sizeAttenuation: true, transparent: true, opacity: 0.85 }),
    )
    const lm = new THREE.LineSegments(
      wireGeo,
      new THREE.LineBasicMaterial({ color: '#22d3ee', transparent: true, opacity: 0.22 }),
    )

    return { pointsMesh: pm, lineMesh: lm, anim: { base, deform, edgeList, wirePos } }
  }, [faceData])

  // Dispose when unmounted or faceData changes
  useEffect(() => {
    return () => {
      pointsMesh.geometry.dispose()
      pointsMesh.material.dispose()
      lineMesh.geometry.dispose()
      lineMesh.material.dispose()
    }
  }, [pointsMesh, lineMesh])

  // Pre-compute eye ring parameters from base positions
  const leftEye = useMemo(() => {
    const c = centroid(faceData.positions, LEFT_EYE_INDICES)
    return { center: c, radius: ringRadius(faceData.positions, LEFT_EYE_INDICES, c[0], c[1]) }
  }, [faceData])

  const rightEye = useMemo(() => {
    const c = centroid(faceData.positions, RIGHT_EYE_INDICES)
    return { center: c, radius: ringRadius(faceData.positions, RIGHT_EYE_INDICES, c[0], c[1]) }
  }, [faceData])

  useFrame(({ clock }) => {
    if (!groupRef.current) return

    const t   = clock.getElapsedTime()
    const { base, deform, edgeList, wirePos } = anim

    // ── 1. Noise amplitude by state
    let noiseAmp = 0
    if (aiState === 'listening') noiseAmp = 0.0075
    else if (aiState === 'speaking') noiseAmp = 0.0045

    const vertCount = base.length / 3
    for (let i = 0; i < vertCount; i++) {
      deform[i * 3]     = base[i * 3]     + noise(i,       t, noiseAmp)
      deform[i * 3 + 1] = base[i * 3 + 1] + noise(i + 100, t, noiseAmp)
      deform[i * 3 + 2] = base[i * 3 + 2] + noise(i + 200, t, noiseAmp * 0.45)
    }

    // ── 2. Jaw / mouth animation
    const rawJaw = voiceJawRef ? voiceJawRef.current : (aiState === 'speaking' ? simulateJaw(t) : 0)
    const jawOpen = Math.max(rawJaw, (blendShapes && blendShapes.jawOpen) || 0)
    const ma = jawOpen * 0.048

    for (const idx of MOUTH_UPPER) deform[idx * 3 + 1] += ma * 0.5
    for (const idx of MOUTH_LOWER) {
      deform[idx * 3 + 1] -= ma * 0.65
      deform[idx * 3 + 2] += ma * 0.28
    }
    for (const idx of JAW_INDICES) {
      deform[idx * 3 + 1] -= ma * 0.85
      deform[idx * 3 + 2] += ma * 0.5
    }

    // ── 3. Push updates to GPU
    pointsMesh.geometry.attributes.position.needsUpdate = true

    for (let i = 0; i < edgeList.length; i++) {
      const vi = edgeList[i] * 3
      wirePos[i * 3]     = deform[vi]
      wirePos[i * 3 + 1] = deform[vi + 1]
      wirePos[i * 3 + 2] = deform[vi + 2]
    }
    lineMesh.geometry.attributes.position.needsUpdate = true

    // ── 4. Group-level breathing + state scale
    const breathScale = 1 + Math.sin(t * 0.8) * 0.015
    const stateScale  = aiState === 'listening' ? 1.05 : 1.0
    groupRef.current.scale.setScalar(breathScale * stateScale)

    // ── 5. Wireframe opacity pulse
    lineMesh.material.opacity = 0.18 + Math.sin(t * 0.55) * 0.08
  })

  return (
    <group ref={groupRef}>
      <primitive object={pointsMesh} />
      <primitive object={lineMesh}   />
      <EyeRing center={leftEye.center}  radius={leftEye.radius}  />
      <EyeRing center={rightEye.center} radius={rightEye.radius} />
    </group>
  )
}

// ── Public component ──────────────────────────────────────────────────────────

/**
 * FaceMesh
 *
 * Props:
 *   aiState      – 'idle' | 'listening' | 'speaking'
 *   blendShapes  – Record<string, number>  (may be empty)
 *   voiceJawRef  – React.MutableRefObject<number>  0–1
 *   onLoaded     – () => void  called when OBJ finishes loading
 */
export default function FaceMesh({ aiState, blendShapes, voiceJawRef, onLoaded }) {
  const [faceData, setFaceData] = useState(null)

  useEffect(() => {
    loadFaceModel()
      .then((data) => {
        setFaceData(data)
        window.dispatchEvent(new CustomEvent('facemesh:loaded'))
        if (onLoaded) onLoaded()
      })
      .catch((err) => console.error('[FaceMesh] load error', err))
  }, [])

  if (!faceData) return <LoadingFallback />

  return (
    <FaceMeshRenderer
      faceData={faceData}
      aiState={aiState}
      blendShapes={blendShapes}
      voiceJawRef={voiceJawRef}
    />
  )
}

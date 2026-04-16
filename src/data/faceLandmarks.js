/**
 * Canonical MediaPipe Face Mesh model — 468 vertices.
 * Vertex indices here correspond directly to MediaPipe landmark IDs (0-based),
 * so they can be used without any remapping against the OBJ positions array.
 *
 * OBJ source (do not change URL):
 * https://raw.githubusercontent.com/google/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj
 */

const OBJ_URL =
  'https://raw.githubusercontent.com/google/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj'

// ── Landmark index sets ───────────────────────────────────────────────────────

/** Outer upper-lip ring */
export const MOUTH_UPPER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 306]
/** Outer lower-lip ring */
export const MOUTH_LOWER = [17, 84, 181, 91, 146, 375, 321, 405, 314]
/** Jaw / chin cluster */
export const JAW_INDICES = [152, 175, 140, 136, 150, 149, 176, 148]

/** Left-eye boundary (from viewer's perspective) */
export const LEFT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
/** Right-eye boundary (from viewer's perspective) */
export const RIGHT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

// ── OBJ parser + normalizer ───────────────────────────────────────────────────

/**
 * Parse a Wavefront OBJ string.
 * Handles  `v x y z`  and  `f i  |  f i/t/n`  lines (1-indexed).
 * Returns Float32Array positions and Uint32Array indices.
 */
function parseOBJ(text) {
  const rawPos = []
  const rawIdx = []

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim()
    if (line.startsWith('v ')) {
      const [, x, y, z] = line.split(/\s+/)
      rawPos.push(parseFloat(x), parseFloat(y), parseFloat(z))
    } else if (line.startsWith('f ')) {
      const parts = line.split(/\s+/).slice(1)
      const getIdx = (s) => parseInt(s.split('/')[0], 10) - 1
      // triangulate (face should already be tris in this model)
      rawIdx.push(getIdx(parts[0]), getIdx(parts[1]), getIdx(parts[2]))
    }
  }

  // Center + normalize so the largest axis span fits within ±0.8
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity
  let minZ = Infinity, maxZ = -Infinity

  for (let i = 0; i < rawPos.length; i += 3) {
    if (rawPos[i]   < minX) minX = rawPos[i]
    if (rawPos[i]   > maxX) maxX = rawPos[i]
    if (rawPos[i+1] < minY) minY = rawPos[i+1]
    if (rawPos[i+1] > maxY) maxY = rawPos[i+1]
    if (rawPos[i+2] < minZ) minZ = rawPos[i+2]
    if (rawPos[i+2] > maxZ) maxZ = rawPos[i+2]
  }

  const cx = (minX + maxX) / 2
  const cy = (minY + maxY) / 2
  const cz = (minZ + maxZ) / 2
  const halfExtent = Math.max(maxX - minX, maxY - minY, maxZ - minZ) / 2
  const scale = 0.8 / halfExtent

  const positions = new Float32Array(rawPos.length)
  for (let i = 0; i < rawPos.length; i += 3) {
    positions[i]   = (rawPos[i]   - cx) * scale
    positions[i+1] = (rawPos[i+1] - cy) * scale
    positions[i+2] = (rawPos[i+2] - cz) * scale
  }

  return { positions, indices: new Uint32Array(rawIdx) }
}

// ── Public loader ─────────────────────────────────────────────────────────────

/**
 * Fetch and parse the MediaPipe canonical face model.
 * Returns { positions: Float32Array, indices: Uint32Array }.
 */
export async function loadFaceModel() {
  const res = await fetch(OBJ_URL)
  if (!res.ok) throw new Error(`Failed to fetch face model: ${res.status}`)
  const text = await res.text()
  return parseOBJ(text)
}

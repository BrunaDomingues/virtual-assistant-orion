import { useRef, useState, useEffect, useCallback } from 'react'
import AgentFace from './components/AgentFace'
import { useOrionSocket } from './hooks/useOrionSocket'

const STATE_LABELS = {
  idle:       'DESLIGADO',
  standby:    'AGUARDANDO',
  listening:  'ESCUTANDO',
  processing: 'PROCESSING',
  speaking:   'SPEAKING',
}

const BLEND_KEYS = ['jawOpen', 'mouthSmile', 'eyeBlinkLeft', 'eyeBlinkRight', 'browDown']

// ── Blend-shape simulation ────────────────────────────────────────────────────

function simulateBlendShapes(aiState) {
  const t = Date.now() * 0.001
  if (aiState === 'speaking') {
    return {
      jawOpen:       Math.max(0, Math.sin(t * 4.5) * 0.55 + Math.sin(t * 7.3) * 0.28 + Math.random() * 0.06),
      mouthSmile:    Math.max(0, Math.sin(t * 1.8) * 0.22 + 0.08),
      eyeBlinkLeft:  Math.random() > 0.97  ? Math.random() * 0.8 : 0,
      eyeBlinkRight: Math.random() > 0.97  ? Math.random() * 0.8 : 0,
      browDown:      Math.max(0, Math.sin(t * 2.5) * 0.18 + 0.05),
    }
  }
  if (aiState === 'processing') {
    return {
      jawOpen:       0,
      mouthSmile:    0.02,
      eyeBlinkLeft:  Math.random() > 0.98  ? Math.random() * 0.85 : 0,
      eyeBlinkRight: Math.random() > 0.98  ? Math.random() * 0.85 : 0,
      browDown:      0.1 + Math.sin(t * 1.6) * 0.06,
    }
  }
  if (aiState === 'listening') {
    return {
      jawOpen:       0,
      mouthSmile:    0.04,
      eyeBlinkLeft:  Math.random() > 0.985 ? Math.random() * 0.9 : 0,
      eyeBlinkRight: Math.random() > 0.985 ? Math.random() * 0.9 : 0,
      browDown:      0.06 + Math.sin(t * 1.2) * 0.04,
    }
  }
  if (aiState === 'standby') {
    return {
      jawOpen:       0,
      mouthSmile:    0.02,
      eyeBlinkLeft:  Math.random() > 0.992 ? Math.random() * 0.5 : 0,
      eyeBlinkRight: Math.random() > 0.992 ? Math.random() * 0.5 : 0,
      browDown:      0.03 + Math.sin(t * 0.8) * 0.02,
    }
  }
  return { jawOpen: 0, mouthSmile: 0, eyeBlinkLeft: 0, eyeBlinkRight: 0, browDown: 0 }
}

// ── VU meter ──────────────────────────────────────────────────────────────────

const VU_COUNT = 14

const isPetMode = new URLSearchParams(window.location.search).get('mode') === 'pet'

function VuMeter() {
  return (
    <div className="vu-meter">
      {Array.from({ length: VU_COUNT }, (_, i) => (
        <div
          key={i}
          className="vu-bar"
          style={{ animationDelay: `${i * 0.04}s`, animationDuration: `${0.2 + Math.random() * 0.15}s` }}
        />
      ))}
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  // ── WebSocket (backend) ────────────────────────────────────────────────────
  const {
    connected,
    aiState: socketState,
    lastText,
    lastCommand,
    assistantName,
    wakeWord,
    startListening,
    stopListening,
  } = useOrionSocket()

  const [meshLoaded,   setMeshLoaded]   = useState(false)
  const [blendShapes,  setBlendShapes]  = useState({})
  const [lastCmdLabel, setLastCmdLabel] = useState('')
  const [visualState,  setVisualState]  = useState('idle')
  const voiceJawRef = useRef(0)
  const processingTimerRef = useRef(null)

  // Active state: real backend state when connected, idle fallback otherwise
  const aiState = connected ? socketState : 'idle'

  // Track last executed command label for HUD display
  useEffect(() => {
    if (lastCommand) setLastCmdLabel(lastCommand.label)
  }, [lastCommand])

  useEffect(() => {
    document.documentElement.classList.toggle('pet-mode', isPetMode)
    document.body.classList.toggle('pet-mode', isPetMode)
  }, [])

  // Visual pipeline: listening -> processing -> speaking -> listening/idle
  useEffect(() => {
    if (!connected) {
      setVisualState('idle')
      return
    }

    if (aiState === 'speaking') {
      setVisualState('speaking')
      return
    }

    if (aiState === 'idle') {
      setVisualState('idle')
      return
    }

    if (aiState === 'standby') {
      setVisualState('standby')
      return
    }

    // Preserve processing until timer ends.
    setVisualState((prev) => (prev === 'processing' ? prev : 'listening'))
  }, [aiState, connected])

  useEffect(() => {
    if (!lastCommand || !connected) return
    if (processingTimerRef.current) clearTimeout(processingTimerRef.current)

    setVisualState('processing')
    processingTimerRef.current = setTimeout(() => {
      setVisualState((prev) => {
        if (prev === 'speaking') return 'speaking'
        return aiState === 'idle' ? 'idle' : aiState === 'standby' ? 'standby' : 'listening'
      })
      processingTimerRef.current = null
    }, 900)
  }, [lastCommand, connected, aiState])

  useEffect(() => {
    return () => {
      if (processingTimerRef.current) clearTimeout(processingTimerRef.current)
    }
  }, [])

  // Sync voiceJawRef with simulated jawOpen
  useEffect(() => {
    voiceJawRef.current = blendShapes.jawOpen || 0
  }, [blendShapes])

  // Anima rosto em standby, listening, processing e speaking
  useEffect(() => {
    if (visualState === 'idle') { setBlendShapes({}); return }
    const id = setInterval(() => setBlendShapes(simulateBlendShapes(visualState)), 50)
    return () => clearInterval(id)
  }, [visualState])

  const voiceActive = connected && aiState !== 'idle'

  const toggleListening = useCallback(() => {
    if (!connected) return
    if (voiceActive) stopListening()
    else startListening()
  }, [connected, voiceActive, startListening, stopListening])

  const stateLabels = {
    ...STATE_LABELS,
    standby: `AGUARDANDO ${assistantName.toUpperCase()}`,
  }

  const formatPct = (v) => `${Math.round((v || 0) * 100)}%`
  const barWidth  = (v) => `${Math.min(100, Math.round((v || 0) * 100))}%`

  const bubbleText = {
    processing: 'Processando comando',
    standby:    `Diga "${wakeWord}" para ativar`,
    listening:  lastText || 'Fale o comando e pause ao terminar',
    speaking:   lastCmdLabel ? `Falando: ${lastCmdLabel}` : 'Reproduzindo resposta em voz',
  }

  return (
    <div className={`app-container${isPetMode ? ' pet-shell' : ''}`}>

      {/* ── 3-D canvas ──────────────────────────────────────────────────── */}
      <div className="canvas-container">
        <AgentFace
          aiState={aiState}
          blendShapes={blendShapes}
          voiceJawRef={voiceJawRef}
          onLoaded={() => setMeshLoaded(true)}
        />
      </div>

      {/* ── HUD overlay ─────────────────────────────────────────────────── */}
      <div className="hud-overlay">

        <div className={`scan-line${isPetMode ? ' pet-hidden' : ''}`} />

        <div className={`corner corner-tl${isPetMode ? ' pet-hidden' : ''}`} />
        <div className={`corner corner-tr${isPetMode ? ' pet-hidden' : ''}`} />
        <div className={`corner corner-bl${isPetMode ? ' pet-hidden' : ''}`} />
        <div className={`corner corner-br${isPetMode ? ' pet-hidden' : ''}`} />

        {/* ── Top bar ────────────────────────────────────────────────────── */}
        <div className={`hud-top${isPetMode ? ' pet-status-bar' : ''}`}>
          <span className={`hud-label${isPetMode ? ' pet-hidden' : ''}`}>{assistantName.toUpperCase()} AI&nbsp;v2.0</span>
          <div className={`hud-status status-${visualState}`}>
            <span className="status-dot" />
            {stateLabels[visualState]}
          </div>
          <span className={`hud-label${isPetMode ? ' pet-hidden' : ''}`}>
            {meshLoaded ? 'MESH·468V' : 'MESH·LOADING…'}
          </span>
        </div>

        {/* ── Left panel — Neural params ─────────────────────────────────── */}
        <div className={`hud-panel hud-left${isPetMode ? ' pet-hidden' : ''}`}>
          <div className="panel-title">NEURAL PARAMS</div>
          {BLEND_KEYS.map((key) => (
            <div key={key} className="bar-row">
              <div className="bar-label">{key.toUpperCase()}</div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: barWidth(blendShapes[key]) }} />
              </div>
              <div className="bar-value">{formatPct(blendShapes[key])}</div>
            </div>
          ))}
        </div>

        {/* ── Right panel — System info ──────────────────────────────────── */}
        <div className={`hud-panel hud-right${isPetMode ? ' pet-hidden' : ''}`}>
          <div className="panel-title">SYS INFO</div>
          {[
            ['MODEL',   'MEDIAPIPE 468V'],
            ['RENDER',  'WEBGL 2.0'],
            ['LANG',    'PT-BR'],
            ['STATE',   stateLabels[visualState]],
            ['AUDIO',   visualState === 'speaking' ? 'PLAYING' : 'IDLE'],
            ['BACKEND', connected ? 'ONLINE' : 'OFFLINE'],
          ].map(([label, value]) => (
            <div key={label} className="info-row">
              <span>{label}</span>
              <span
                className={
                  label === 'STATE'   ? `status-${visualState}` :
                  label === 'BACKEND' ? (connected ? 'backend-online' : 'backend-offline') :
                  ''
                }
              >
                {value}
              </span>
            </div>
          ))}

          {/* Last command result */}
          {lastCommand && (
            <div className="info-row last-cmd">
              <span>LAST CMD</span>
              <span className={lastCommand.success ? 'cmd-ok' : 'cmd-fail'}>
                {lastCommand.success ? '✓' : '✗'}&nbsp;{lastCommand.label}
              </span>
            </div>
          )}
        </div>

        {/* ── VU meter (speaking) ────────────────────────────────────────── */}
        {visualState === 'speaking' && <VuMeter />}

        {/* ── Speech bubble ─────────────────────────────────────────────── */}
        {(visualState === 'speaking' || visualState === 'listening' || visualState === 'standby' || visualState === 'processing') && (
          <div className={`speech-bubble${isPetMode ? ' pet-bubble' : ''}`}>
            <span className={visualState === 'processing' ? 'typing-cursor' : ''}>{bubbleText[visualState]}</span>
          </div>
        )}

        {/* ── Bottom bar ─────────────────────────────────────────────────── */}
        <div className={`hud-bottom${isPetMode ? ' pet-bottom' : ''}`}>
          <span className={`hud-label blink${isPetMode ? ' pet-hidden' : ''}`}>◉ {assistantName.toUpperCase()} NEURAL INTERFACE</span>

          <div className="bottom-center">
            {!isPetMode && (
            <button
              disabled={!connected}
              title={connected ? undefined : 'Backend offline — conecte o servidor para ativar escuta'}
              className={`state-btn${voiceActive ? ' active' : ''}${!connected ? ' ws-driven' : ''}`}
              onClick={toggleListening}
            >
              {voiceActive ? 'SILENCIAR' : 'ATIVAR VOZ'}
            </button>
            )}
          </div>

          <span className={`hud-label${isPetMode ? ' pet-hidden' : ''}`}>
            {connected ? 'WS·CONNECTED' : 'WS·OFFLINE'}
          </span>
        </div>

        {isPetMode && (
          <div className="pet-drag-hint">arraste para mover</div>
        )}

      </div>
    </div>
  )
}

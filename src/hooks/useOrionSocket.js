import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL          = 'ws://localhost:8765'
const RECONNECT_DELAY = 2000   // ms between reconnect attempts
const PING_INTERVAL   = 20000  // ms between keep-alive pings

/**
 * useOrionSocket
 *
 * Mantém uma conexão WebSocket com o backend Python (ws://localhost:8765).
 * Reconecta automaticamente quando a conexão cai.
 *
 * Returns:
 *   connected   – boolean: backend está acessível
 *   aiState     – 'idle' | 'listening' | 'speaking'
 *   lastText    – último texto reconhecido pela voz (string)
 *   lastCommand – último objeto de comando executado { label, success }
 */
export function useOrionSocket(url = WS_URL) {
  const [connected,   setConnected]   = useState(false)
  const [aiState,     setAiState]     = useState('idle')
  const [lastText,    setLastText]    = useState('')
  const [lastCommand, setLastCommand] = useState(null)

  const wsRef          = useRef(null)
  const mountedRef     = useRef(true)
  const reconnectTimer = useRef(null)
  const pingTimer      = useRef(null)

  const clearTimers = useCallback(() => {
    if (reconnectTimer.current) { clearTimeout(reconnectTimer.current);  reconnectTimer.current = null }
    if (pingTimer.current)      { clearInterval(pingTimer.current);       pingTimer.current      = null }
  }, [])

  const sendMessage = useCallback((payload) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(JSON.stringify(payload))
    return true
  }, [])

  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (!mountedRef.current) return
      setConnected(true)
      // periodic keep-alive ping
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, PING_INTERVAL)
    }

    ws.onmessage = (event) => {
      if (!mountedRef.current) return
      let msg
      try { msg = JSON.parse(event.data) } catch { return }

      switch (msg.type) {
        case 'state':
          setAiState(msg.state)
          break
        case 'recognized':
          setLastText(msg.text ?? '')
          break
        case 'command':
          setLastCommand({ label: msg.label, success: msg.success })
          break
        case 'error':
          console.warn('[OrionSocket] Backend error:', msg.message)
          break
        case 'pong':
          break
        default:
          break
      }
    }

    ws.onerror = () => {
      // silently ignore — onclose will handle reconnect
    }

    ws.onclose = () => {
      if (!mountedRef.current) return
      clearTimers()
      setConnected(false)
      setAiState('idle')
      // schedule reconnect
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
    }
  }, [url, clearTimers])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      clearTimers()
      if (wsRef.current) {
        wsRef.current.onclose = null  // prevent reconnect on unmount
        wsRef.current.close()
      }
    }
  }, [connect, clearTimers])

  const startListening = useCallback(() => {
    return sendMessage({ type: 'start_listening' })
  }, [sendMessage])

  const stopListening = useCallback(() => {
    return sendMessage({ type: 'stop_listening' })
  }, [sendMessage])

  return { connected, aiState, lastText, lastCommand, startListening, stopListening }
}

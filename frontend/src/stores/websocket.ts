import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

interface WSMessage {
  type: string
  data?: any
  timestamp?: string
}

export const useWebSocketStore = defineStore('websocket', () => {
  const connected = ref(false)
  const messages = ref<WSMessage[]>([])
  const subscriptions = ref<Set<string>>(new Set())
  
  let ws: WebSocket | null = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  const connect = (url: string = 'ws://localhost:8000/ws') => {
    if (ws && connected.value) return

    try {
      ws = new WebSocket(url)

      ws.onopen = () => {
        console.log('WebSocket connected')
        connected.value = true
        reconnectAttempts = 0
      }

      ws.onmessage = (event) => {
        const message: WSMessage = JSON.parse(event.data)
        messages.value.push(message)
        // Keep only last 100 messages
        if (messages.value.length > 100) {
          messages.value.shift()
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        connected.value = false
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        connected.value = false
        attemptReconnect(url)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      attemptReconnect(url)
    }
  }

  const attemptReconnect = (url: string) => {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++
      console.log(`Reconnecting... Attempt ${reconnectAttempts}/${maxReconnectAttempts}`)
      setTimeout(() => connect(url), reconnectDelay)
    } else {
      console.error('Max reconnect attempts reached')
    }
  }

  const send = (message: WSMessage) => {
    if (ws && connected.value) {
      ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected')
    }
  }

  const subscribe = (channel: string) => {
    subscriptions.value.add(channel)
    send({
      type: 'subscribe',
      data: { channel }
    })
  }

  const unsubscribe = (channel: string) => {
    subscriptions.value.delete(channel)
    send({
      type: 'unsubscribe',
      data: { channel }
    })
  }

  const disconnect = () => {
    if (ws) {
      ws.close()
      ws = null
      connected.value = false
    }
  }

  const isConnected = computed(() => connected.value)
  const messageCount = computed(() => messages.value.length)

  return {
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    isConnected,
    messageCount,
    messages,
    subscriptions,
  }
})

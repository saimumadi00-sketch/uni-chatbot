import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const sendingRef = useRef(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, error])

  useEffect(() => {
    const input = inputRef.current
    input.style.height = 'auto'
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`
  }, [draft])

  async function send(event) {
    event.preventDefault()
    const message = draft.trim()
    if (!message || sendingRef.current) return
    sendingRef.current = true
    const history = [...messages]
    setMessages([...history, { role: 'user', content: message }])
    setDraft('')
    setError('')
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history }),
        signal: AbortSignal.timeout(75000),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Could not send this message. Please try again.')
      }
      if (typeof data.response !== 'string' || !data.response.trim()) {
        throw new Error('The server returned an empty response. Please try again.')
      }
      setMessages([...history, { role: 'user', content: message }, { role: 'assistant', content: data.response }])
    } catch (err) {
      // Restore the draft and prior context so a retry never duplicates a turn.
      setMessages(history)
      setDraft(message)
      setError(err.name === 'TimeoutError'
        ? 'The request timed out. Please try again.'
        : err instanceof TypeError
          ? 'Could not reach the backend. Make sure it is running on port 8000.'
          : err.message)
    } finally {
      sendingRef.current = false
      setLoading(false)
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }

  return (
    <div className="flex h-dvh flex-col bg-[#111315] text-zinc-100">
      <header className="shrink-0 border-b border-white/[0.07] px-6 py-5">
        <div className="mx-auto flex max-w-[700px] items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-200 text-lg text-zinc-950" aria-hidden="true">✳</span>
            <h1 className="text-sm font-semibold tracking-wide">Simple Chat</h1>
          </div>
          <span className="text-xs text-zinc-500">AI chat</span>
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto px-5">
        <div className="mx-auto flex min-h-full max-w-[700px] flex-col">
          {messages.length === 0 && !loading ? (
            <div className="flex flex-1 flex-col items-center justify-center py-16 text-center">
              <span className="mb-6 text-5xl text-teal-200" aria-hidden="true">✳</span>
              <p className="text-3xl font-medium tracking-tight sm:text-4xl">Ask me anything.</p>
              <p className="mt-3 max-w-sm text-sm leading-6 text-zinc-400">A question, an idea, a place to start.<br />Let’s think it through together.</p>
            </div>
          ) : (
            <div role="log" aria-label="Conversation" aria-live="polite" className="space-y-7 py-8">
              {messages.map((message, index) => (
                <article key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={message.role === 'user' ? 'max-w-[85%] rounded-2xl rounded-tr-sm bg-[#283a37] px-5 py-3' : 'min-w-0 max-w-full pr-4'}>
                    <p className="mb-2 text-[11px] font-medium uppercase tracking-widest text-zinc-400">{message.role === 'user' ? 'You' : 'Assistant'}</p>
                    {message.role === 'user'
                      ? <p className="whitespace-pre-wrap break-words text-sm leading-7">{message.content}</p>
                      : <div className="markdown text-sm leading-7"><ReactMarkdown>{message.content}</ReactMarkdown></div>}
                  </div>
                </article>
              ))}
              {loading && <div role="status" className="flex items-center gap-1.5 py-3 text-teal-200"><span className="sr-only">Assistant is thinking</span>{[0, 1, 2].map(dot => <span key={dot} className="loading-dot h-1.5 w-1.5 rounded-full bg-current" style={{ animationDelay: `${dot * 160}ms` }} />)}</div>}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="shrink-0 px-5 pb-5 pt-3">
        <div className="mx-auto max-w-[700px]">
          {error && <p role="alert" className="mb-3 rounded-xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-200">{error}</p>}
          <form onSubmit={send} className="flex items-end gap-3 rounded-2xl border border-white/10 bg-[#1c1f21] p-3 focus-within:border-teal-200/40">
            <textarea
              ref={inputRef}
              aria-label="Your message"
              placeholder="Type a message…"
              value={draft}
              onChange={event => setDraft(event.target.value)}
              onKeyDown={event => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) send(event)
              }}
              readOnly={loading}
              rows={1}
              className="max-h-[180px] min-h-11 flex-1 resize-none bg-transparent px-2 py-2.5 text-sm leading-6 text-zinc-100 outline-none placeholder:text-zinc-500"
            />
            <button type="submit" disabled={loading || !draft.trim()} aria-label="Send message" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-teal-200 text-zinc-950 transition hover:bg-teal-100 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-200 disabled:cursor-not-allowed disabled:opacity-30">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 19V5m-6 6 6-6 6 6" /></svg>
            </button>
          </form>
          <p className="mt-3 text-center text-[11px] text-zinc-500">Enter to send · Shift + Enter for a new line</p>
        </div>
      </footer>
    </div>
  )
}

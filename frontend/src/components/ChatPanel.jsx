import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, List, message } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { sendChat } from '../api/client'

export default function ChatPanel({ onUpdate }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '您好！我是学科知识整合助手。您可以询问整合决策的原因，或提出修改建议。' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const listEndRef = useRef(null)

  const scrollToBottom = () => {
    listEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user', content: input }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await sendChat(newMessages)
      setMessages([...newMessages, { role: 'assistant', content: res.reply }])
      if ((res.updated_graph || res.updated_merge) && onUpdate) {
        onUpdate()
      }
    } catch (e) {
      message.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        <List
          dataSource={messages}
          renderItem={(item) => (
            <div
              style={{
                marginBottom: 12,
                textAlign: item.role === 'user' ? 'right' : 'left',
              }}
            >
              <div
                style={{
                  display: 'inline-block',
                  padding: '8px 12px',
                  borderRadius: 8,
                  background: item.role === 'user' ? '#1890ff' : '#f0f0f0',
                  color: item.role === 'user' ? '#fff' : '#333',
                  maxWidth: '90%',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {item.content}
              </div>
            </div>
          )}
        />
        <div ref={listEndRef} />
      </div>

      <div style={{ padding: 12, borderTop: '1px solid #f0f0f0', display: 'flex', gap: 8 }}>
        <Input.TextArea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="输入您的问题或建议..."
        />
        <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={handleSend}>
          发送
        </Button>
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Input, Button, List, Tag, Collapse, message, Spin } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { queryRAG, indexRAG, getRAGStatus } from '../api/client'

export default function RAGPanel() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ indexed_books: 0, total_chunks: 0, is_ready: false })

  useEffect(() => {
    getRAGStatus().then(setStatus).catch(() => {})
  }, [])

  const handleAsk = async () => {
    if (!question.trim()) return
    setLoading(true)
    try {
      const res = await queryRAG(question)
      setAnswer(res)
    } catch (e) {
      message.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleIndex = async () => {
    setLoading(true)
    try {
      await indexRAG()
      message.success('索引建立完成')
      const s = await getRAGStatus()
      setStatus(s)
    } catch (e) {
      message.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 16 }}>
      <div style={{ marginBottom: 12 }}>
        <Tag color={status.is_ready ? 'success' : 'warning'}>
          {status.is_ready ? `已索引 ${status.indexed_books} 本教材` : '索引未建立'}
        </Tag>
        <Button size="small" onClick={handleIndex} style={{ marginLeft: 8 }}>重建索引</Button>
      </div>

      <Input.Search
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onSearch={handleAsk}
        enterButton={<SendOutlined />}
        placeholder="输入问题，基于教材内容回答..."
      />

      <Spin spinning={loading} style={{ marginTop: 16 }}>
        {answer && (
          <div style={{ marginTop: 16 }}>
            <div style={{ background: '#f6ffed', padding: 12, borderRadius: 6, marginBottom: 12 }}>
              <b>回答：</b>
              <div style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{answer.answer}</div>
            </div>

            <Collapse ghost>
              <Collapse.Panel header="引用来源" key="1">
                <List
                  size="small"
                  dataSource={answer.citations || []}
                  renderItem={(item) => (
                    <List.Item>
                      <div>
                        <div>{item.textbook} · {item.chapter} · 第{item.page}页</div>
                        <div style={{ color: '#999', fontSize: 12 }}>相关度: {(item.relevance_score * 100).toFixed(1)}%</div>
                      </div>
                    </List.Item>
                  )}
                />
              </Collapse.Panel>
            </Collapse>
          </div>
        )}
      </Spin>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Input, Button, List, Tag, Collapse, message, Spin, Divider, Card, Drawer, Empty, Space } from 'antd'
import { SendOutlined, ClearOutlined, ReloadOutlined } from '@ant-design/icons'
import { queryRAG, indexRAG, getRAGStatus } from '../api/client'

export default function RAGPanel() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [indexing, setIndexing] = useState(false)
  const [status, setStatus] = useState({ indexed_books: 0, total_chunks: 0, is_ready: false })
  const [selectedChunk, setSelectedChunk] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      const s = await getRAGStatus()
      setStatus(s)
    } catch (e) {
      console.error('Failed to load status:', e)
    }
  }

  const handleAsk = async () => {
    if (!question.trim()) {
      message.warning('请输入问题')
      return
    }
    setLoading(true)
    try {
      const res = await queryRAG(question)
      setAnswer(res)
      // 保存到历史
      setHistory([
        ...history,
        { question: question, answer: res, time: new Date().toLocaleTimeString() }
      ])
      setQuestion('')
    } catch (e) {
      message.error(`查询失败: ${e}`)
    } finally {
      setLoading(false)
    }
  }

  const handleIndex = async () => {
    setIndexing(true)
    try {
      const result = await indexRAG()
      message.success(result.message)
      await loadStatus()
    } catch (e) {
      message.error(`索引建立失败: ${e}`)
    } finally {
      setIndexing(false)
    }
  }

  const handleClear = () => {
    setAnswer(null)
    setQuestion('')
  }

  return (
    <div style={{ padding: 16 }}>
      {/* 状态栏 */}
      <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }}>
        <Space>
          <Tag color={status.is_ready ? 'green' : 'orange'} icon={status.is_ready ? '✓' : '⚠'}>
            {status.is_ready
              ? `已索引：${status.indexed_books} 本教材 · ${status.total_chunks} 个知识块`
              : '索引未建立 - 请先构建索引后才能进行问答'}
          </Tag>
          <Button
            type={status.is_ready ? 'default' : 'primary'}
            size="small"
            loading={indexing}
            onClick={handleIndex}
            icon={<ReloadOutlined />}
          >
            {indexing ? '索引中...' : '重建索引'}
          </Button>
        </Space>
      </Card>

      {/* 问题输入 */}
      <div style={{ marginBottom: 16 }}>
        <Input.TextArea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onPressEnter={(e) => {
            if (e.ctrlKey || e.metaKey) handleAsk()
          }}
          placeholder="输入你的问题（例如：什么是细胞膜？）&#10;提示：Ctrl+Enter 快速发送"
          rows={2}
          style={{ marginBottom: 8 }}
        />
        <Space>
          <Button
            type="primary"
            loading={loading}
            onClick={handleAsk}
            disabled={!status.is_ready}
            icon={<SendOutlined />}
          >
            {loading ? '思考中...' : '提问'}
          </Button>
          <Button onClick={handleClear} icon={<ClearOutlined />}>
            清空
          </Button>
        </Space>
      </div>

      {/* 结果展示 */}
      <Spin spinning={loading} tip="正在检索和生成回答...">
        {answer && (
          <div>
            <Divider />
            
            {/* 回答内容 */}
            <Card
              title="AI 回答"
              size="small"
              style={{ marginBottom: 16, background: '#f6ffed', borderColor: '#b7eb8f' }}
            >
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 14 }}>
                {answer.answer}
              </div>
            </Card>

            {/* 引用来源 */}
            {answer.citations && answer.citations.length > 0 && (
              <Card
                title={`📖 引用来源 (${answer.citations.length})`}
                size="small"
                style={{ marginBottom: 16 }}
              >
                <List
                  dataSource={answer.citations}
                  renderItem={(item, idx) => (
                    <List.Item
                      style={{
                        padding: '8px 0',
                        borderBottom: idx < answer.citations.length - 1 ? '1px solid #f0f0f0' : 'none',
                      }}
                    >
                      <div style={{ width: '100%' }}>
                        <div style={{ marginBottom: 4 }}>
                          <Tag color="blue">{item.textbook}</Tag>
                          <span style={{ marginLeft: 8, color: '#666' }}>
                            {item.chapter} · 第 {item.page} 页
                          </span>
                          <span
                            style={{
                              marginLeft: 12,
                              color: '#ff7a45',
                              fontWeight: 'bold',
                            }}
                          >
                            相关度 {(item.relevance_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 原文内容 */}
            {answer.source_chunks && answer.source_chunks.length > 0 && (
              <Card
                title={`📄 检索到的原文 (${answer.source_chunks.length} 段)`}
                size="small"
                style={{ marginBottom: 16 }}
              >
                <List
                  dataSource={answer.source_chunks}
                  renderItem={(chunk, idx) => (
                    <List.Item
                      style={{
                        padding: '8px 0',
                        borderBottom:
                          idx < answer.source_chunks.length - 1 ? '1px solid #f0f0f0' : 'none',
                      }}
                    >
                      <div
                        style={{
                          width: '100%',
                          padding: 8,
                          background: '#fafafa',
                          borderRadius: 4,
                          cursor: 'pointer',
                        }}
                        onClick={() => setSelectedChunk(chunk)}
                      >
                        <div
                          style={{
                            color: '#666',
                            fontSize: 12,
                            marginBottom: 4,
                          }}
                        >
                          [段落 {idx + 1}] 点击查看完整内容
                        </div>
                        <div
                          style={{
                            color: '#333',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxHeight: 40,
                          }}
                        >
                          {chunk}
                        </div>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 查询历史 */}
            {history.length > 1 && (
              <Card title="📋 查询历史" size="small">
                <List
                  dataSource={history}
                  renderItem={(item, idx) => (
                    <List.Item style={{ padding: '8px 0' }}>
                      <List.Item.Meta
                        title={
                          <span style={{ fontSize: 12, color: '#666' }}>
                            {item.time} - Q{history.length - idx}
                          </span>
                        }
                        description={
                          <div
                            style={{ cursor: 'pointer', color: '#1890ff' }}
                            onClick={() => {
                              setQuestion(item.question)
                              setAnswer(item.answer)
                            }}
                          >
                            {item.question}
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            )}
          </div>
        )}

        {!answer && !loading && status.is_ready && (
          <Empty description="输入问题开始提问" style={{ marginTop: 32 }} />
        )}

        {!status.is_ready && (
          <Empty
            description="请先构建索引"
            style={{ marginTop: 32, color: '#ff7a45' }}
          />
        )}
      </Spin>

      {/* 原文抽屉 */}
      <Drawer
        title="原文内容"
        placement="right"
        onClose={() => setSelectedChunk(null)}
        open={!!selectedChunk}
        width={500}
      >
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
          {selectedChunk}
        </div>
      </Drawer>
    </div>
  )
}

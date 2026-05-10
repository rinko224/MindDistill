import React, { useEffect, useState } from 'react'
import { Upload, Button, List, Tag, message, Spin } from 'antd'
import { UploadOutlined, FileTextOutlined, ReloadOutlined, PartitionOutlined } from '@ant-design/icons'
import { uploadFile, listBooks, parseBook, getParseStatus, buildGraph } from '../api/client'

export default function TextbookPanel({ onSelectBook, onUploadSuccess, refreshFlag }) {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(false)
  const [building, setBuilding] = useState({})

  const fetchBooks = async () => {
    try {
      const data = await listBooks()
      setBooks(data.books || [])
    } catch (e) {
      message.error(e)
    }
  }

  useEffect(() => {
    fetchBooks()
  }, [refreshFlag])

  const handleUpload = async ({ file }) => {
    setLoading(true)
    try {
      const res = await uploadFile(file)
      message.success('上传成功')
      onUploadSuccess()
      if (res.book?.textbook_id) {
        await parseBook(res.book.textbook_id)
        message.info('开始解析...')
      }
    } catch (e) {
      message.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleBuildGraph = async (bookId) => {
    setBuilding(prev => ({ ...prev, [bookId]: true }))
    message.info('开始后台构建知识图谱...')
    try {
      await buildGraph(bookId)
      message.success('图谱构建任务已提交，请稍后在图谱面板刷新查看')
    } catch (e) {
      message.error(e)
    } finally {
      setBuilding(prev => ({ ...prev, [bookId]: false }))
    }
  }

  const statusColor = {
    parsing: 'processing',
    completed: 'success',
    failed: 'error',
  }

  return (
    <div style={{ padding: 16 }}>
      <h3 style={{ marginBottom: 12 }}>教材管理</h3>
      <Upload.Dragger customRequest={handleUpload} showUploadList={false} accept=".pdf,.md,.txt,.docx,.xlsx">
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p className="ant-upload-text">拖拽或点击上传教材</p>
        <p className="ant-upload-hint">支持 PDF / Markdown / TXT / Word / Excel</p>
      </Upload.Dragger>

      <Button icon={<ReloadOutlined />} onClick={fetchBooks} style={{ marginTop: 12, width: '100%' }}>
        刷新列表
      </Button>

      <Spin spinning={loading}>
        <List
          style={{ marginTop: 16 }}
          dataSource={books}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Tag color={statusColor[item.status] || 'default'} key="status">{item.status}</Tag>,
                <Button 
                  key="build"
                  size="small" 
                  type="primary" 
                  icon={<PartitionOutlined />} 
                  loading={building[item.textbook_id]}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleBuildGraph(item.textbook_id)
                  }}
                >
                  {building[item.textbook_id] ? '构建中' : '构建图谱'}
                </Button>
              ]}
              onClick={() => onSelectBook(item.textbook_id)}
              style={{ cursor: 'pointer', background: '#fafafa', marginBottom: 8, padding: 12, borderRadius: 6 }}
            >
              <List.Item.Meta
                avatar={<FileTextOutlined />}
                title={item.title}
                description={`${item.format?.toUpperCase()} · ${(item.total_chars / 10000).toFixed(1)}万字 · ${item.chapters?.length || 0}章`}
              />
            </List.Item>
          )}
        />
      </Spin>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Upload, Button, List, Tag, message, Spin, Popconfirm, Space, Tooltip } from 'antd'
import { UploadOutlined, FileTextOutlined, ReloadOutlined, PartitionOutlined, DeleteOutlined } from '@ant-design/icons'
import { uploadFile, listBooks, parseBook, getParseStatus, buildGraph, deleteBook } from '../api/client'

export default function TextbookPanel({ onSelectBook, onUploadSuccess, refreshFlag }) {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(false)
  const [building, setBuilding] = useState({})
  const [deleting, setDeleting] = useState({})

  const [uploadingFiles, setUploadingFiles] = useState([])

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

  const uploadTimerRef = React.useRef(null)

  // 处理批量上传的核心逻辑
  const processUpload = async (files) => {
    if (files.length === 0) return
    
    setLoading(true)
    try {
      const res = await uploadFile(files)
      message.success(`成功上传 ${res.books?.length || 0} 本教材`)
      
      // 批量触发解析
      const parseTasks = (res.books || []).map(book => {
        if (book.textbook_id) return parseBook(book.textbook_id)
        return Promise.resolve()
      })
      
      await Promise.all(parseTasks)
      message.info('已开始批量解析...')
      
      fetchBooks()
      if (onUploadSuccess) onUploadSuccess()
    } catch (e) {
      message.error(`上传失败: ${e}`)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (info) => {
    const { fileList } = info
    // 过滤出真正需要上传的文件对象
    const rawFiles = fileList
      .map(f => f.originFileObj)
      .filter(f => f instanceof File)

    // 使用定时器防抖，确保在一次拖拽/选择中的所有文件都被收集齐后再发送请求
    if (rawFiles.length > 0) {
      if (uploadTimerRef.current) clearTimeout(uploadTimerRef.current)
      uploadTimerRef.current = setTimeout(() => {
        processUpload(rawFiles)
        // 清理当前上传列表
        info.fileList.splice(0, info.fileList.length)
      }, 300)
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

  const handleDeleteBook = async (bookId, title) => {
    setDeleting(prev => ({ ...prev, [bookId]: true }))
    try {
      await deleteBook(bookId)
      message.success(`已删除教材：${title}`)
      await fetchBooks()
    } catch (e) {
      message.error(`删除失败: ${e}`)
    } finally {
      setDeleting(prev => ({ ...prev, [bookId]: false }))
    }
  }

  const statusColor = {
    parsing: 'processing',
    completed: 'success',
    failed: 'error',
  }

  const statusText = {
    parsing: '解析中',
    completed: '已完成',
    failed: '解析失败',
  }

  return (
    <div style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: 12, whiteSpace: 'nowrap' }}>📚 教材管理</h3>
      <Upload.Dragger
        multiple
        showUploadList={false}
        accept=".pdf,.md,.txt,.docx,.xlsx"
        beforeUpload={() => false}
        onChange={handleChange}
        style={{ marginBottom: 12 }}
      >
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p className="ant-upload-text">拖拽或点击上传</p>
        <p className="ant-upload-hint" style={{ fontSize: 12 }}>支持批量上传 PDF / MD / TXT / Word / Excel</p>
      </Upload.Dragger>

      <Button
        icon={<ReloadOutlined />}
        onClick={fetchBooks}
        style={{ marginBottom: 12, width: '100%' }}
        size="small"
      >
        刷新列表
      </Button>

      <Spin spinning={loading} style={{ flex: 1, overflow: 'auto' }}>
        <List
          dataSource={books}
          renderItem={(item) => (
            <List.Item
              style={{
                cursor: 'pointer',
                background: '#fafafa',
                marginBottom: 8,
                padding: 12,
                borderRadius: 6,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
              }}
              onClick={() => onSelectBook(item.textbook_id)}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 6,
                }}>
                  <FileTextOutlined style={{ fontSize: 16, color: '#1890ff', flexShrink: 0 }} />
                  <Tooltip title={item.title}>
                    <div style={{
                      fontWeight: 500,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1,
                    }}>
                      {item.title}
                    </div>
                  </Tooltip>
                </div>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 6,
                  fontSize: 12,
                  color: '#666',
                }}>
                  <span>{item.format?.toUpperCase()}</span>
                  <span>•</span>
                  <span>{(item.total_chars / 10000).toFixed(1)}万字</span>
                  <span>•</span>
                  <span>{item.chapters?.length || 0}章</span>
                </div>
              </div>

              <div style={{
                display: 'flex',
                gap: 6,
                flexShrink: 0,
                marginLeft: 8,
              }} onClick={(e) => e.stopPropagation()}>
                <Tag color={statusColor[item.status] || 'default'} style={{ marginRight: 0 }}>
                  {statusText[item.status] || item.status}
                </Tag>
                <Button
                  size="small"
                  type={item.graph_status === 'completed' ? 'default' : 'primary'}
                  icon={<PartitionOutlined />}
                  loading={building[item.textbook_id] || item.graph_status === 'building'}
                  disabled={item.status !== 'completed' || item.graph_status === 'completed'}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleBuildGraph(item.textbook_id)
                  }}
                  style={{ fontSize: 12 }}
                >
                  {item.graph_status === 'completed' ? '✓图谱' : '图谱'}
                </Button>
                <Popconfirm
                  title="删除教材"
                  description={`确定要删除《${item.title}》吗？此操作不可恢复。`}
                  onConfirm={(e) => {
                    e.stopPropagation()
                    handleDeleteBook(item.textbook_id, item.title)
                  }}
                  onCancel={(e) => e.stopPropagation()}
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                >
                  <Button
                    size="small"
                    danger
                    type="text"
                    icon={<DeleteOutlined />}
                    loading={deleting[item.textbook_id]}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>
              </div>
            </List.Item>
          )}
          locale={{ emptyText: '暂无教材，上传一个开始吧' }}
        />
      </Spin>
    </div>
  )
}

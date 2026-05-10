import React, { useState } from 'react'
import { Layout, Tabs, Button, Tooltip } from 'antd'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'
import TextbookPanel from './components/TextbookPanel'
import GraphPanel from './components/GraphPanel'
import RAGPanel from './components/RAGPanel'
import ChatPanel from './components/ChatPanel'
import MergePanel from './components/MergePanel'

const { Sider, Content } = Layout

function App() {
  const [selectedBookId, setSelectedBookId] = useState(null)
  const [refreshFlag, setRefreshFlag] = useState(0)
  const [leftSiderCollapsed, setLeftSiderCollapsed] = useState(false)
  const [showMerged, setShowMerged] = useState(false)

  const triggerRefresh = () => setRefreshFlag((v) => v + 1)

  const handleSelectBook = (bookId) => {
    console.log('[App] handleSelectBook', bookId)
    setSelectedBookId(bookId)
    setShowMerged(false)
  }

  console.log('[App] render showMerged=', showMerged, 'selectedBookId=', selectedBookId)

  return (
    <Layout style={{ height: '100vh', display: 'flex' }}>
      {/* 左侧：教材管理 - 可完全折叠 */}
      <Sider
        width={320}
        collapsedWidth={0}
        collapsed={leftSiderCollapsed}
        trigger={null}
        theme="light"
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
          overflow: 'auto',
          transition: 'all 0.3s ease',
          flex: leftSiderCollapsed ? '0 0 0' : '0 0 320px',
        }}
      >
        <TextbookPanel
          onSelectBook={handleSelectBook}
          onUploadSuccess={triggerRefresh}
          refreshFlag={refreshFlag}
        />
      </Sider>

      {/* 中间：知识图谱 */}
      <Content
        style={{
          position: 'relative',
          background: '#fafafa',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* 折叠按钮 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px 12px',
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Tooltip title={leftSiderCollapsed ? '展开教材管理' : '收起教材管理'}>
            <Button
              type="text"
              size="small"
              icon={leftSiderCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setLeftSiderCollapsed(!leftSiderCollapsed)}
            />
          </Tooltip>
        </div>

        {/* 图谱面板 */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          <GraphPanel selectedBookId={selectedBookId} showMerged={showMerged} refreshFlag={refreshFlag} />
        </div>
      </Content>

      {/* 右侧：功能面板 */}
      <Sider
        width={400}
        collapsedWidth={0}
        theme="light"
        style={{
          background: '#fff',
          borderLeft: '1px solid #f0f0f0',
          overflow: 'auto',
          flex: '0 0 400px',
        }}
      >
        <Tabs
          defaultActiveKey="rag"
          items={[
            {
              key: 'rag',
              label: 'RAG问答',
              children: <RAGPanel />,
            },
            {
              key: 'merge',
              label: '整合',
              children: <MergePanel refreshFlag={refreshFlag} onShowMerged={() => setShowMerged(true)} onUpdate={triggerRefresh} />,
            },
            {
              key: 'chat',
              label: '对话',
              children: <ChatPanel onUpdate={triggerRefresh} />,
            },
          ]}
        />
      </Sider>
    </Layout>
  )
}

export default App

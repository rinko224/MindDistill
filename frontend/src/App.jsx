import React, { useState } from 'react'
import { Layout, Tabs, message } from 'antd'
import TextbookPanel from './components/TextbookPanel'
import GraphPanel from './components/GraphPanel'
import RAGPanel from './components/RAGPanel'
import ChatPanel from './components/ChatPanel'
import MergePanel from './components/MergePanel'

const { Sider, Content } = Layout

function App() {
  const [selectedBookId, setSelectedBookId] = useState(null)
  const [refreshFlag, setRefreshFlag] = useState(0)

  const triggerRefresh = () => setRefreshFlag((v) => v + 1)

  return (
    <Layout style={{ height: '100vh' }}>
      {/* 左侧：教材管理 */}
      <Sider width={320} style={{ background: '#fff', borderRight: '1px solid #f0f0f0', overflow: 'auto' }}>
        <TextbookPanel
          onSelectBook={setSelectedBookId}
          onUploadSuccess={triggerRefresh}
          refreshFlag={refreshFlag}
        />
      </Sider>

      {/* 中间：知识图谱 */}
      <Content style={{ position: 'relative', background: '#fafafa' }}>
        <GraphPanel selectedBookId={selectedBookId} refreshFlag={refreshFlag} />
      </Content>

      {/* 右侧：功能面板 */}
      <Sider width={400} style={{ background: '#fff', borderLeft: '1px solid #f0f0f0', overflow: 'auto' }}>
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
              children: <MergePanel refreshFlag={refreshFlag} />,
            },
            {
              key: 'chat',
              label: '对话',
              children: <ChatPanel />,
            },
          ]}
        />
      </Sider>
    </Layout>
  )
}

export default App

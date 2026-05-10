import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { Button, Drawer, message, Tag } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { getGraph, getMergedGraph } from '../api/client'

export default function GraphPanel({ selectedBookId, showMerged, refreshFlag }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [info, setInfo] = useState({ loading: true, nodes: 0, edges: 0, error: null })

  const fetchGraph = async () => {
    console.log('[GraphPanel] fetchGraph called showMerged=', showMerged, 'selectedBookId=', selectedBookId)
    setInfo((prev) => ({ ...prev, loading: true }))
    try {
      let data
      if (showMerged) {
        console.log('[GraphPanel] -> calling getMergedGraph()')
        data = await getMergedGraph()
      } else if (selectedBookId) {
        console.log('[GraphPanel] -> calling getGraph(', selectedBookId, ')')
        data = await getGraph(selectedBookId)
      } else {
        console.log('[GraphPanel] -> no selection')
        data = { error: 'No selection' }
      }

      if (data?.error || !data) {
        setInfo({ loading: false, nodes: 0, edges: 0, error: data?.error || '无数据' })
        if (chartInstance.current) {
          chartInstance.current.setOption({ series: [] }, true)
        }
        return
      }

      const nodeCount = data.nodes?.length || 0
      const edgeCount = data.edges?.length || 0
      setInfo({ loading: false, nodes: nodeCount, edges: edgeCount, error: null })

      if (!nodeCount && !edgeCount) {
        if (chartInstance.current) {
          chartInstance.current.setOption({ series: [] }, true)
        }
        return
      }
      renderGraph(data)
    } catch (e) {
      setInfo({ loading: false, nodes: 0, edges: 0, error: String(e) })
      message.error(`图谱加载失败: ${e}`)
    }
  }

  const renderGraph = (graphData) => {
    if (!chartRef.current) return
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    // echarts graph 的 links source/target 优先匹配 name
    const idToName = {}
    const nodes = (graphData.nodes || []).map((n) => {
      idToName[n.id] = n.name
      return {
        id: n.id,
        name: n.name,
        value: n.category,
        symbolSize: 30 + (n.occurrence || 1) * 5,
        itemStyle: { color: n.textbook_id ? stringToColor(n.textbook_id) : '#5470c6' },
        ...n,
      }
    })

    const edges = (graphData.edges || []).map((e) => ({
      source: idToName[e.source] || e.source,
      target: idToName[e.target] || e.target,
      relation: e.relation_type,
      ...e,
    }))

    const option = {
      tooltip: { formatter: (p) => p.data.name || p.data.relation },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: edges,
          roam: true,
          draggable: true,
          label: { show: true, position: 'right' },
          force: { repulsion: 300, edgeLength: 120 },
          emphasis: { focus: 'adjacency', lineStyle: { width: 4 } },
        },
      ],
    }

    chartInstance.current.resize()
    chartInstance.current.setOption(option, true)
    chartInstance.current.off('click')
    chartInstance.current.on('click', (params) => {
      if (params.dataType === 'node') {
        setSelectedNode(params.data)
        setDrawerOpen(true)
      }
    })
  }

  useEffect(() => {
    console.log('[GraphPanel] useEffect triggered showMerged=', showMerged, 'selectedBookId=', selectedBookId, 'refreshFlag=', refreshFlag)
    fetchGraph()
    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
      chartInstance.current = null
    }
  }, [selectedBookId, showMerged, refreshFlag])

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', padding: '8px 12px', gap: 8, background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
        <b>{showMerged ? '跨教材整合图谱' : '单本教材图谱'}</b>
        {info.loading && <Tag color="processing">加载中</Tag>}
        {info.error && <Tag color="error">错误: {info.error}</Tag>}
        {!info.loading && !info.error && (
          <Tag color="success">节点 {info.nodes} / 边 {info.edges}</Tag>
        )}
        <div style={{ flex: 1 }} />
        <Button
          icon={<ReloadOutlined />}
          size="small"
          onClick={() => {
            fetchGraph()
            message.success('图谱已刷新')
          }}
        >
          刷新图谱
        </Button>
      </div>
      <div ref={chartRef} style={{ flex: 1, minHeight: 400 }} />
      <Drawer
        title={selectedNode?.name || '知识点详情'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={360}
      >
        {selectedNode && (
          <div>
            <p><b>定义：</b>{selectedNode.definition || '暂无'}</p>
            <p><b>类别：</b>{selectedNode.category || '暂无'}</p>
            <p><b>章节：</b>{selectedNode.chapter || '暂无'}</p>
            <p><b>页码：</b>{selectedNode.page || '暂无'}</p>
          </div>
        )}
      </Drawer>
    </div>
  )
}

function stringToColor(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const c = (hash & 0x00ffffff).toString(16).toUpperCase()
  return '#' + '00000'.substring(0, 6 - c.length) + c
}

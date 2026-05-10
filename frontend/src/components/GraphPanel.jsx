import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { Button, Drawer, message } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { getGraph, getMergedGraph } from '../api/client'

export default function GraphPanel({ selectedBookId, refreshFlag }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)

  const fetchGraph = async () => {
    try {
      let data
      if (selectedBookId) {
        data = await getGraph(selectedBookId)
      } else {
        data = await getMergedGraph()
      }
      if (data?.error) {
        return
      }
      renderGraph(data)
    } catch (e) {
    }
  }

  const renderGraph = (graphData) => {
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const nodes = (graphData.nodes || []).map((n) => ({
      id: n.id,
      name: n.name,
      value: n.category,
      symbolSize: 30 + (n.occurrence || 1) * 5,
      itemStyle: { color: n.textbook_id ? stringToColor(n.textbook_id) : '#5470c6' },
      ...n,
    }))

    const edges = (graphData.edges || []).map((e) => ({
      source: e.source,
      target: e.target,
      relation: e.relation_type,
      ...e,
    }))

    const option = {
      title: { text: selectedBookId ? '单本教材图谱' : '跨教材整合图谱', left: 'center' },
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
    fetchGraph()
    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [selectedBookId, refreshFlag])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Button 
        icon={<ReloadOutlined />} 
        onClick={() => {
          fetchGraph()
          message.success('图谱已刷新')
        }}
        style={{ position: 'absolute', top: 16, right: 16, zIndex: 10 }}
      >
        刷新图谱
      </Button>
      <div ref={chartRef} style={{ width: '100%', height: '100%' }} />
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

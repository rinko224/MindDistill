import React, { useEffect, useRef, useState } from 'react'
import { Button, List, Tag, Statistic, message, Spin } from 'antd'
import { runMerge, resetMerge, getMergeDecisions, getMergeResult } from '../api/client'

export default function MergePanel({ refreshFlag, onShowMerged, onUpdate }) {
  const [result, setResult] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [loading, setLoading] = useState(false)
  const [merging, setMerging] = useState(false)
  const pollRef = useRef(null)

  const fetchData = async () => {
    try {
      const r = await getMergeResult()
      if (!r.error) {
        setResult(r)
        const d = await getMergeDecisions()
        if (d.decisions) setDecisions(d.decisions)
        return true
      }
    } catch (e) {
      // ignore
    }
    return false
  }

  useEffect(() => {
    fetchData()
  }, [refreshFlag])

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    setMerging(true)
    let attempts = 0
    pollRef.current = setInterval(async () => {
      attempts += 1
      const ok = await fetchData()
      if (ok) {
        clearInterval(pollRef.current)
        pollRef.current = null
        setMerging(false)
        message.success('整合完成')
        onUpdate?.()
      } else if (attempts > 30) {
        clearInterval(pollRef.current)
        pollRef.current = null
        setMerging(false)
        message.warning('整合超时，请手动刷新')
      }
    }, 2000)
  }

  const handleMerge = async () => {
    setLoading(true)
    try {
      await runMerge()
      message.success('整合已开始')
      startPolling()
    } catch (e) {
      message.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    setLoading(true)
    try {
      await resetMerge()
      setResult(null)
      setDecisions([])
      message.success('整合已撤销')
      onUpdate?.()
    } catch (e) {
      message.error(e)
    } finally {
      setLoading(false)
    }
  }

  const actionColor = {
    merge: 'blue',
    keep: 'green',
    remove: 'red',
  }

  return (
    <div style={{ padding: 16 }}>
      <Button type="primary" block onClick={handleMerge} loading={loading || merging} style={{ marginBottom: 8 }}>
        {merging ? '整合中，请稍候...' : result ? '重新整合' : '执行跨教材整合'}
      </Button>
      <Button block onClick={() => { console.log('[MergePanel] 查看整合图谱 clicked'); onShowMerged(); message.success('已切换至整合图谱'); }} style={{ marginBottom: 8 }}>
        查看整合图谱
      </Button>
      <Button danger block onClick={handleReset} loading={loading} style={{ marginBottom: 16 }}>
        撤销整合
      </Button>

      {result && (
        <div style={{ marginBottom: 16 }}>
          <Statistic title="原始总字数" value={result.original_chars} />
          <Statistic title="整合后字数" value={result.merged_chars} />
          <Statistic title="压缩比" value={(result.ratio * 100).toFixed(1)} suffix="%" />
          <Statistic title="原始节点数" value={result.original_nodes} />
          <Statistic title="整合后节点数" value={result.merged_nodes} />
        </div>
      )}

      <Spin spinning={loading || merging}>
        <List
          size="small"
          header={<b>整合决策列表</b>}
          dataSource={decisions}
          renderItem={(item) => (
            <List.Item>
              <div>
                <Tag color={actionColor[item.action]}>{item.action}</Tag>
                <span style={{ marginLeft: 8 }}>{item.reason}</span>
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                  置信度: {(item.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </List.Item>
          )}
        />
      </Spin>
    </div>
  )
}

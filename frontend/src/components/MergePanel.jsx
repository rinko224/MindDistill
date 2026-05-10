import React, { useEffect, useState } from 'react'
import { Button, List, Tag, Statistic, message, Spin } from 'antd'
import { runMerge, getMergeDecisions, getMergeResult } from '../api/client'

export default function MergePanel({ refreshFlag }) {
  const [result, setResult] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {
    try {
      const r = await getMergeResult()
      if (!r.error) setResult(r)
      const d = await getMergeDecisions()
      if (d.decisions) setDecisions(d.decisions)
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => {
    fetchData()
  }, [refreshFlag])

  const handleMerge = async () => {
    setLoading(true)
    try {
      await runMerge()
      message.success('整合已开始，请稍后刷新')
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
      <Button type="primary" block onClick={handleMerge} loading={loading} style={{ marginBottom: 16 }}>
        执行跨教材整合
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

      <Spin spinning={loading}>
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

import React, { useEffect, useRef, useState } from 'react'
import { Button, List, Tag, Statistic, message, Spin, Modal } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import { runMerge, resetMerge, getMergeDecisions, getMergeResult, generateReport } from '../api/client'

export default function MergePanel({ refreshFlag, onShowMerged, onUpdate }) {
  const [result, setResult] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [loading, setLoading] = useState(false)
  const [merging, setMerging] = useState(false)
  const [reportOpen, setReportOpen] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
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

  const handleGenerateReport = async () => {
    setReportLoading(true)
    try {
      const res = await generateReport()
      if (res.report) {
        setReportData(res.report)
        setReportOpen(true)
      } else {
        message.warning('暂无报告数据')
      }
    } catch (e) {
      message.error(`生成报告失败: ${e}`)
    } finally {
      setReportLoading(false)
    }
  }

  const actionColor = {
    merge: 'blue',
    keep: 'green',
    remove: 'red',
  }

  const ov = reportData?.overview || {}
  const ds = reportData?.decisions_summary || {}
  const gs = reportData?.graph_stats || {}

  return (
    <div style={{ padding: 16 }}>
      <Button type="primary" block onClick={handleMerge} loading={loading || merging} style={{ marginBottom: 8 }}>
        {merging ? '整合中，请稍候...' : result ? '重新整合' : '执行跨教材整合'}
      </Button>
      <Button block onClick={() => { onShowMerged(); message.success('已切换至整合图谱'); }} style={{ marginBottom: 8 }}>
        查看整合图谱
      </Button>
      <Button block icon={<FileTextOutlined />} onClick={handleGenerateReport} loading={reportLoading} style={{ marginBottom: 8 }}>
        生成整合报告
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

      <Modal
        title="整合报告"
        open={reportOpen}
        onCancel={() => setReportOpen(false)}
        footer={[
          <Button key="close" onClick={() => setReportOpen(false)}>关闭</Button>
        ]}
        width={600}
      >
        {reportData && (
          <div style={{ maxHeight: 500, overflow: 'auto' }}>
            <h3>1. 整合概览</h3>
            <ul>
              <li>原始教材数量：{ov.book_count || 0} 本</li>
              <li>原始总字数：{(ov.total_chars || 0).toLocaleString()} 字</li>
              <li>整合后估算字数：{(ov.merged_chars || 0).toLocaleString()} 字</li>
              <li>最终压缩比：{ov.ratio || '0%'}</li>
            </ul>

            <h3>2. 整合决策摘要</h3>
            <p>系统共执行了 <b>{ds.total || 0}</b> 项整合决策：</p>
            <ul>
              <li>合并 (Merge)：{ds.merge || 0} 项</li>
              <li>保留 (Keep)：{ds.keep || 0} 项</li>
              <li>删除 (Remove)：{ds.remove || 0} 项</li>
            </ul>

            <h3>3. 知识图谱统计</h3>
            <ul>
              <li>整合前总节点数：{gs.original_nodes || 0}</li>
              <li>整合后总节点数：{gs.merged_nodes || 0}</li>
              <li>整合后总关系数：{gs.merged_edges || 0}</li>
            </ul>

            <h3>4. 重点整合案例</h3>
            {(reportData.cases || []).map((c, i) => (
              <div key={i} style={{ marginBottom: 12, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                <b>案例 {i + 1}: {c.result}</b>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>整合理由：{c.reason}</div>
              </div>
            ))}

            <h3>5. 教学完整性说明</h3>
            <p>{reportData.completeness}</p>
          </div>
        )}
      </Modal>
    </div>
  )
}

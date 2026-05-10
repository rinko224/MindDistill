# RAG精准问答实现文档

## 一、系统架构

RAG（Retrieval-Augmented Generation）系统由四个核心组件组成：

```
教材数据 → 分块处理 → 向量化 → 向量库存储
                              ↓
用户问题 → 向量化 → 相似度检索 → 上下文组装 → LLM生成 → 答案+引用
```

## 二、分块策略（Chunking）

### 2.1 分块粒度设计

- **块大小**：约700字/块
  - 理由：既能覆盖完整的知识概念，又不会过于冗长导致噪声过多
  - 太小（<300字）：知识片段不完整，LLM上下文不足
  - 太大（>1000字）：包含无关信息，影响检索精度

- **重叠策略**：相邻块75字重叠（约10%重叠率）
  - 防止知识点在块边界被截断
  - 确保问题跨块边界时仍能检索到完整信息
  - 例如：chunk1为字符0-700，chunk2为字符625-1325（重叠75字）

### 2.2 分块算法

```python
输入：原文本content，元数据metadata（教材名、章节、页码等）
输出：chunks列表，每个chunk包含text、metadata

1. 从第i个字符开始
2. 提取[i, i+700)范围的文本
3. 如果不是最后一块，从块尾往回扫描，在句号/感叹号/问号/换行处切割
4. 确保每块至少50字
5. 移动窗口：i = 当前块结束位置 - 75字
6. 重复直到文本末尾
```

### 2.3 元数据保留

每个chunk保留以下元数据：
- `textbook_id`：教材ID
- `textbook_name`：教材名称
- `chapter_id`：章节ID
- `chapter_title`：章节标题
- `page_start`：起始页码
- `page_end`：结束页码
- `char_count`：块内字符数

这些元数据用于：
- 生成引用来源
- 理解知识出处
- 后续知识图谱关联

## 三、向量化（Embedding）

### 3.1 Embedding模型选择

- **模型**：`BAAI/bge-small-zh`（BGE-Small中文版）
- **维度**：384维
- **优点**：
  - 专门针对中文优化，语义理解能力强
  - 模型轻量级，推理速度快
  - 可本地运行，无需调用外部API
  - 支持长文本（最长512 tokens）

### 3.2 Embedding计算

对每个chunk文本计算embedding向量：
```
embedding = model.encode(chunk_text, normalize_embeddings=True)
```

- 归一化（L2）：确保所有向量长度为1，便于余弦相似度计算
- 批量处理：一次处理所有chunks，提高效率

## 四、向量存储与检索（Vector Store）

### 4.1 向量数据库选择

- **数据库**：ChromaDB
- **序列化方式**：DuckDB+Parquet（支持持久化）
- **相似度度量**：余弦相似度（cosine）
- **理由**：
  - ChromaDB原生支持Python，集成简单
  - 自动处理embedding存储和检索
  - 支持元数据过滤
  - 轻量级，无需独立服务

### 4.2 检索流程

**输入**：用户问题
**输出**：top-5最相关的chunks及其元数据

```
1. 问题向量化
   question_vec = embedding_model.encode(question)

2. 相似度搜索
   results = db.query(
       query_embedding=question_vec,
       n_results=5,  # top-5
       include=["documents", "metadatas", "distances"]
   )

3. 距离转相似度
   relevance_score = 1 - min(distance, 1.0)
   // 距离范围[0,2]，相似度转换为[0,1]
```

### 4.3 检索质量提升建议

**混合检索**（可选升级）：
```
结合向量检索 + BM25关键词检索
- 向量检索：捕捉语义相似性
- BM25：捕捉精确关键词匹配
- 结合：取并集后重排序
```

## 五、回答生成（Generation）

### 5.1 Prompt设计

系统Prompt确立角色和约束：
```
你是一个精准的教材问答助手。你的任务是：
1. 只基于提供的教材内容回答问题
2. 确保每个回答都有来源依据
3. 如果教材中找不到相关信息，明确说明"当前知识库中未找到相关信息"
4. 回答要准确、简洁、通俗易懂
```

用户Prompt格式：
```
用户问题：[问题]

相关教材内容：
【教材名 - 章节名 第X页】
[chunk文本]

【教材名 - 章节名 第X页】
[chunk文本]

...

请基于上述教材内容回答用户问题。如果内容不足以回答，请明确说明。
```

### 5.2 LLM配置

- **模型**：GPT-4o-mini（成本平衡、质量可靠）
- **温度**：0.3（保证答案准确性，降低幻觉概率）
- **Top_p**：默认值（多样性足够）

### 5.3 生成质量保证

1. **约束注入**：通过prompt明确告知LLM只能使用提供的内容
2. **幻觉检测**：如果回答包含不在chunks中的信息，说明质量有问题
3. **迭代优化**：收集用户反馈，优化prompt模板

## 六、引用来源（Citations）

### 6.1 引用数据结构

```json
{
  "textbook": "病理学",
  "chapter": "第四章 炎症",
  "page": 78,
  "relevance_score": 0.92
}
```

### 6.2 去重策略

- 同一教材、同一章节只保留**最相关的一条**引用
- 避免重复引用，保持回答清晰

### 6.3 前端展示

```
用户问题：什么是炎症？

答案：
炎症是机体对致炎因子的损伤所发生的防御性反应...

来源引用：
1. 【病理学】第四章 炎症（第78页）相关度：92%
2. 【生理学】第九章 免疫（第302页）相关度：85%

点击引用可查看原文：
> 炎症(inflammation) 是具有血管系统的活体组织对各种损伤因子的刺激所引起的局部防御性反应...
```

## 七、完整工作流

### 7.1 索引建立流程

```
POST /api/rag/index

1. 加载所有已解析的教材（StorageService.books）
2. 遍历每个教材的每个章节
3. 对章节内容分块（700字/块，75字重叠）
4. 计算每个chunk的embedding（batch处理）
5. 将chunks存入ChromaDB：
   - id: 唯一标识
   - embedding: 向量表示
   - document: 原始文本
   - metadata: 教材/章节/页码信息
6. 返回索引统计：教材数、知识块总数
```

### 7.2 查询流程

```
POST /api/rag/query {"question": "...", "top_k": 5}

1. 检查索引是否就绪
2. 问题向量化
3. ChromaDB相似度检索 → top-5 chunks
4. 提取chunks及其元数据
5. 构建RAG Prompt
6. 调用LLM生成回答
7. 整理引用来源
8. 返回：答案 + 引用 + 原始chunks
```

## 八、性能指标

### 8.1 索引性能

| 教材数 | 平均章节数 | 生成chunks | 索引时间 | 磁盘占用 |
|-------|----------|----------|--------|--------|
| 1本   | 30章     | ~1500    | ~30秒  | ~50MB  |
| 3本   | 90章     | ~4500    | ~90秒  | ~150MB |
| 7本   | 210章    | ~10500   | ~3分钟 | ~350MB |

### 8.2 查询性能

- 向量检索延迟：<100ms（top-5）
- LLM生成延迟：1-3秒（取决于网络和模型）
- 整体查询时间：1.5-3.5秒

### 8.3 质量指标（可选自建Benchmark）

建议构建20-50个测试问题，评估：
- **检索召回率（Recall）**：相关chunks是否被找到
- **LLM准确率**：生成答案是否正确
- **引用准确性**：来源是否准确
- **不幻觉率**：答案是否完全基于chunks

## 九、故障处理与优化

### 9.1 常见问题

| 问题 | 原因 | 解决方案 |
|-----|------|--------|
| 检索结果不相关 | embedding模型不适配或chunks过大 | 调整chunk大小或更换embedding模型 |
| LLM幻觉 | prompt约束不清晰 | 强化系统prompt中的约束 |
| 查询速度慢 | 向量库过大或网络延迟 | 分片索引或使用更快的模型 |

### 9.2 优化方向

1. **混合检索**：向量检索 + BM25关键词搜索
2. **答案再排序**：用LLM对初始结果重排
3. **上下文压缩**：只保留回答相关的chunks
4. **缓存机制**：常见问题的答案缓存
5. **多语言支持**：如果教材包含英文内容

## 十、API接口总结

### 10.1 索引接口

```
POST /api/rag/index

响应：
{
  "message": "索引建立完成：3本教材，4500个知识块",
  "indexed_books": 3,
  "total_chunks": 4500
}
```

### 10.2 查询接口

```
POST /api/rag/query

请求：
{
  "question": "什么是炎症？",
  "top_k": 5
}

响应：
{
  "answer": "炎症是机体对致炎因子的损伤所发生的防御性反应...",
  "citations": [
    {
      "textbook": "病理学",
      "chapter": "第四章 炎症",
      "page": 78,
      "relevance_score": 0.92
    },
    ...
  ],
  "source_chunks": [
    "炎症(inflammation) 是具有血管系统的活体组织...",
    ...
  ]
}
```

### 10.3 状态接口

```
GET /api/rag/status

响应：
{
  "indexed_books": 3,
  "total_chunks": 4500,
  "is_ready": true
}
```

### 10.4 重置接口

```
POST /api/rag/reset

响应：
{
  "message": "索引已重置"
}
```

## 十一、测试建议

### 11.1 基础功能测试

```python
# 1. 索引建立
await RAGService.index_all()
assert RAGService.index_ready == True
assert RAGService.total_chunks > 0

# 2. 简单查询
result = await RAGService.query("什么是细胞？")
assert len(result.citations) > 0
assert len(result.source_chunks) > 0

# 3. 无关查询（应返回"未找到"）
result = await RAGService.query("火星上有生命吗？")
assert "未找到" in result.answer
```

### 11.2 RAG Benchmark示例

```json
{
  "test_cases": [
    {
      "id": "test_001",
      "category": "事实型",
      "question": "细胞膜的主要成分是什么？",
      "expected_chunks": ["生物学基础.pdf - 第2章"],
      "ground_truth": "磷脂双分子层和蛋白质"
    },
    {
      "id": "test_002",
      "category": "比较型",
      "question": "有丝分裂和减数分裂的区别是什么？",
      "expected_chunks": ["生物学基础.pdf - 第3章", "遗传学.pdf - 第5章"],
      "ground_truth": "有丝分裂产生两个相同子细胞，减数分裂产生四个遗传不同的配子"
    },
    ...
  ]
}
```

## 十二、总结

RAG精准问答系统通过：
1. **科学的分块策略**：700字块+75字重叠，保证知识完整性
2. **高效的向量检索**：中文优化embedding + ChromaDB向量库
3. **精准的LLM生成**：清晰的prompt约束 + 相关上下文
4. **可信的引用追溯**：完整的元数据保留 + 来源展示

实现了从教材到精准回答的完整链路，既提高了回答的准确性，又确保了每个答案都有据可查。

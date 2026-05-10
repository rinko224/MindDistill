# RAG精准问答系统 - 快速开始指南

## 📋 概述

RAG精准问答系统是学科知识整合智能体的核心功能之一，提供基于教材内容的精准问答能力。系统通过向量检索+LLM生成的组合，确保每个答案都有据可查。

## 🚀 快速开始

### 第一步：上传和解析教材

```bash
# 1. 在前端上传教材文件（PDF、Markdown、TXT等）
# 2. 等待文件解析完成
# 3. 可以通过以下API检查解析状态

GET /api/upload/
# 响应示例：
# {
#   "books": [
#     {
#       "textbook_id": "book_01",
#       "title": "生理学",
#       "total_pages": 520,
#       "status": "completed",
#       "chapters": [...]
#     }
#   ]
# }
```

### 第二步：建立索引

```bash
POST /api/rag/index

# 响应：
# {
#   "message": "索引建立完成：3本教材，4500个知识块",
#   "indexed_books": 3,
#   "total_chunks": 4500
# }
```

这一步会：
1. 遍历所有已解析的教材
2. 对每个章节进行分块（约700字/块，75字重叠）
3. 计算embedding向量
4. 存入ChromaDB向量数据库

⏱️ 预计耗时：
- 1本教材：~30秒
- 3本教材：~90秒
- 7本教材：~3分钟

### 第三步：执行查询

```bash
POST /api/rag/query

请求体：
{
  "question": "什么是细胞膜？",
  "top_k": 5
}

# 响应示例：
# {
#   "answer": "细胞膜是指围绕细胞质并限制细胞范围的半透膜...",
#   "citations": [
#     {
#       "textbook": "生物学基础",
#       "chapter": "第二章 细胞的基本结构",
#       "page": 45,
#       "relevance_score": 0.92
#     },
#     {
#       "textbook": "细胞生物学",
#       "chapter": "第一章 细胞膜",
#       "page": 12,
#       "relevance_score": 0.87
#     }
#   ],
#   "source_chunks": [
#     "细胞膜(cell membrane/plasma membrane) 是围绕细胞质...",
#     "细胞膜由磷脂分子和蛋白质分子组成..."
#   ]
# }
```

## 📊 查看索引状态

```bash
GET /api/rag/status

# 响应：
# {
#   "indexed_books": 3,
#   "total_chunks": 4500,
#   "is_ready": true
# }
```

## 🧪 运行基准测试

```bash
POST /api/rag/benchmark

# 执行标准测试用例集，评估系统质量
# 响应包含：
# - 总体通过率
# - 关键词覆盖率
# - 引用准确性
# - 详细的测试报告
```

## 🔄 重置索引

如果需要重新构建索引（例如上传了新教材）：

```bash
POST /api/rag/reset

# 响应：
# {
#   "message": "索引已重置"
# }
```

## 💻 使用示例

### Python示例

```python
import asyncio
from app.services.rag import RAGService

async def main():
    # 1. 建立索引
    result = await RAGService.index_all()
    print(f"索引建立: {result['message']}")
    
    # 2. 执行查询
    response = await RAGService.query("细胞膜的结构是什么？", top_k=5)
    
    print("=== RAG问答结果 ===")
    print(f"问题: 细胞膜的结构是什么？")
    print(f"\n答案:\n{response.answer}")
    print(f"\n引用来源:")
    for citation in response.citations:
        print(f"  - {citation.textbook} 《{citation.chapter}》第{citation.page}页 (相关度: {citation.relevance_score:.1%})")

asyncio.run(main())
```

### JavaScript/React示例

```javascript
// 在RAGPanel.jsx中已实现
import { indexRAG, queryRAG, getRAGStatus } from '../api/client'

// 建立索引
const result = await indexRAG()
console.log(result.message)

// 查询
const response = await queryRAG("什么是细胞膜？", 5)
console.log(response.answer)
console.log(response.citations)

// 查询状态
const status = await getRAGStatus()
console.log(`已索引: ${status.total_chunks} 个知识块`)
```

## 🎯 问题类型示例

### 事实型问题

```
Q: 细胞膜的主要成分是什么？
A: 细胞膜的主要成分是磷脂和蛋白质。具体来说，细胞膜由磷脂分子形成的双分子层和蛋白质分子组成。其中磷脂分子排列成双分子层，蛋白质分子部分镶嵌在或贴附在双分子层表面。

来源：
- 《生物学基础》第二章 细胞的基本结构 第45页 相关度97%
- 《细胞生物学》第一章 细胞膜 第12页 相关度91%
```

### 比较型问题

```
Q: 有丝分裂和减数分裂的主要区别是什么？
A: 有丝分裂和减数分裂是两种不同的细胞分裂方式，主要区别包括：
1. 分裂次数：有丝分裂进行一次分裂，减数分裂进行两次分裂
2. 产生的细胞数：有丝分裂产生两个子细胞，减数分裂产生四个子细胞
3. 遗传学差异：有丝分裂产生的子细胞与母细胞遗传物质完全相同，减数分裂产生的子细胞遗传物质只有母细胞的一半

来源：
- 《遗传学》第三章 减数分裂 第78页 相关度94%
- 《生物学基础》第六章 细胞分裂 第112页 相关度88%
```

### 推理型问题

```
Q: 为什么绿色植物主要分布在温暖湿润的地区？
A: 这是因为绿色植物进行光合作用需要特定的环境条件：
1. 光照：需要充足的太阳光
2. 水分：光合作用需要水作为原料，湿润环境提供充足水分
3. 温度：酶活性与温度相关，适当的温度能提高代谢效率
4. 二氧化碳：虽然空气中普遍存在，但局部环境也会影响

温暖湿润的地区同时满足这些条件，因此绿色植物在该地区生长最旺盛。

来源：
- 《植物生理学》第五章 光合作用 第156页 相关度92%
- 《生态学》第二章 植物分布 第89页 相关度85%
```

## 🔍 高级用法

### 调整检索参数

```python
# 增加检索块数以获得更全面的信息
response = await RAGService.query("复杂问题", top_k=10)

# 减少检索块数以加快响应速度
response = await RAGService.query("简单问题", top_k=3)
```

### 自定义embedding模型

编辑 `.env` 文件：

```
EMBEDDING_MODEL=BAAI/bge-small-zh  # 中文优化
# 或
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2  # 多语言
```

### 调整chunk大小

在 `backend/app/services/rag.py` 中：

```python
class RAGService:
    CHUNK_SIZE = 700      # 调整为500-1000字
    OVERLAP_SIZE = 75     # 调整为50-150字
```

## ⚙️ 性能优化建议

### 1. 混合检索（可选升级）

结合向量检索和BM25关键词检索，提高召回率：

```python
# 在query方法中，先执行向量检索
results_vector = collection.query(query_embedding, n_results=10)

# 再执行关键词检索
results_keyword = search_bm25(question, top_k=10)

# 取并集后重排序
combined_results = merge_and_rerank(results_vector, results_keyword)
```

### 2. 答案再排序

使用LLM对检索结果进行相关性排序。

### 3. 缓存热门问题

```python
cache = {}
if question in cache:
    return cache[question]
# ... 执行查询
cache[question] = response
```

### 4. 批量索引优化

```python
# 使用批量API而不是逐个添加
collection.add(
    ids=batch_ids,
    embeddings=batch_embeddings,
    documents=batch_documents,
    metadatas=batch_metadatas
)
```

## 🐛 常见问题

### Q: 查询结果总是返回"未找到"

**A:** 检查以下几点：
1. 是否执行了 `POST /api/rag/index`？
2. 是否成功上传和解析了教材？
3. 尝试增加 `top_k` 参数值
4. 检查embedding模型是否正确加载

### Q: 回答中包含教材中没有的信息（幻觉）

**A:** 这是LLM的常见问题。解决方法：
1. 在系统prompt中强化"只基于提供的内容"的约束
2. 使用温度较低的LLM参数（已设为0.3）
3. 考虑使用更小的、更精准的模型
4. 验证检索到的chunks是否相关

### Q: 某些问题的答案引用来自错误的教材

**A:** 可能的原因：
1. 多本教材内容重复，相似度高
2. embedding模型的语义理解不准确
3. 问题表述模糊

解决方法：
1. 检查教材是否有重复内容
2. 考虑使用更好的embedding模型
3. 提高用户提问的明确性

### Q: 索引建立很慢

**A:** 正常现象。优化方法：
1. 使用更快的embedding模型（如MiniLM）
2. 批量处理chunks
3. 使用GPU加速（如果可用）

## 📚 相关文档

- [RAG精准问答实现文档](./RAG精准问答实现.md) - 详细的技术实现说明
- [系统设计文档](./系统设计.md) - 整体系统架构
- [API参考](#) - 完整的API文档

## 🎓 自建Benchmark

建议自己收集20-50个问题，构建测试集：

```json
{
  "test_cases": [
    {
      "id": "test_001",
      "category": "事实型",
      "question": "细胞膜的主要成分是什么？",
      "expected_keywords": ["磷脂", "蛋白质"],
      "expected_textbooks": ["生物学基础"]
    }
  ]
}
```

然后调用 `POST /api/rag/benchmark` 来评估系统质量。

## 📞 技术支持

如有问题，请：
1. 查看本文档和实现文档
2. 检查日志文件（`data/logs/`）
3. 运行基准测试获取诊断信息
4. 检查模型/API配置

---

**祝你使用愉快！🎉**

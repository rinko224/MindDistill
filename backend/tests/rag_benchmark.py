"""
RAG精准问答系统 - 集成测试与Benchmark
=====================================

这个模块提供RAG系统的测试用例和Benchmark评估
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Tuple


class RAGTestCase:
    """RAG测试用例"""
    
    def __init__(self, id: str, category: str, question: str, 
                 expected_keywords: List[str], expected_textbooks: List[str] = None):
        """
        Args:
            id: 用例ID
            category: 问题类型（事实型/比较型/推理型/跨教材）
            question: 问题文本
            expected_keywords: 预期答案应该包含的关键词
            expected_textbooks: 预期涉及的教材列表
        """
        self.id = id
        self.category = category
        self.question = question
        self.expected_keywords = expected_keywords
        self.expected_textbooks = expected_textbooks or []
        self.result = None
        self.passed = False
        
    def evaluate(self, answer: str, citations: List[Dict]) -> Tuple[bool, Dict]:
        """
        评估RAG答案质量
        
        Returns:
            (是否通过, 评估报告)
        """
        report = {
            "test_id": self.id,
            "category": self.category,
            "question": self.question,
            "metrics": {}
        }
        
        # 1. 检查关键词覆盖度
        found_keywords = sum(1 for kw in self.expected_keywords if kw in answer)
        keyword_coverage = found_keywords / len(self.expected_keywords) if self.expected_keywords else 1.0
        report["metrics"]["keyword_coverage"] = {
            "found": found_keywords,
            "total": len(self.expected_keywords),
            "coverage": keyword_coverage
        }
        
        # 2. 检查引用覆盖度
        cited_textbooks = [c["textbook"] for c in citations]
        if self.expected_textbooks:
            expected_cited = sum(1 for tb in self.expected_textbooks if tb in cited_textbooks)
            citation_coverage = expected_cited / len(self.expected_textbooks)
        else:
            citation_coverage = 1.0 if len(citations) > 0 else 0.5
        report["metrics"]["citation_coverage"] = {
            "cited": cited_textbooks,
            "expected": self.expected_textbooks,
            "coverage": citation_coverage
        }
        
        # 3. 检查幻觉（答案中是否包含明显错误信息）
        # 简单检查：答案长度是否在合理范围内
        hallucination_score = 1.0
        if len(answer) < 20:
            hallucination_score = 0.3  # 答案太短，可能没有真正回答
        elif len(answer) > 5000:
            hallucination_score = 0.5  # 答案太长，可能包含过多无关信息
        report["metrics"]["hallucination_score"] = hallucination_score
        
        # 4. 总体评分
        # 权重：关键词(40%) + 引用(40%) + 反幻觉(20%)
        total_score = (
            keyword_coverage * 0.4 +
            citation_coverage * 0.4 +
            hallucination_score * 0.2
        )
        report["metrics"]["total_score"] = round(total_score, 3)
        
        # 5. 通过判定
        passed = (
            keyword_coverage >= 0.5 and
            citation_coverage >= 0.5 and
            hallucination_score >= 0.5 and
            len(citations) > 0
        )
        report["passed"] = passed
        self.result = report
        self.passed = passed
        return passed, report


# 标准测试集
STANDARD_TEST_CASES = [
    # 事实型问题
    RAGTestCase(
        id="test_001",
        category="事实型",
        question="细胞膜的主要成分是什么？",
        expected_keywords=["磷脂", "蛋白质", "双分子层"],
    ),
    RAGTestCase(
        id="test_002",
        category="事实型",
        question="光合作用的产物有哪些？",
        expected_keywords=["葡萄糖", "氧气", "水", "光能"],
    ),
    RAGTestCase(
        id="test_003",
        category="事实型",
        question="DNA的全称是什么？其作用是什么？",
        expected_keywords=["脱氧核糖核酸", "遗传", "信息"],
    ),
    
    # 比较型问题
    RAGTestCase(
        id="test_004",
        category="比较型",
        question="有丝分裂和减数分裂的主要区别是什么？",
        expected_keywords=["有丝分裂", "减数分裂", "配子", "相同", "不同"],
    ),
    RAGTestCase(
        id="test_005",
        category="比较型",
        question="原核生物和真核生物的区别是什么？",
        expected_keywords=["原核", "真核", "细胞核", "膜"],
    ),
    
    # 推理型问题
    RAGTestCase(
        id="test_006",
        category="推理型",
        question="为什么绿色植物主要分布在温暖湿润的地区？",
        expected_keywords=["光合作用", "水", "温度", "光"],
    ),
    RAGTestCase(
        id="test_007",
        category="推理型",
        question="为什么细胞需要进行代谢？",
        expected_keywords=["能量", "生长", "维持", "生命活动"],
    ),
]


class RAGBenchmark:
    """RAG性能评估"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.test_results = []
        self.metrics_summary = {}
        
    async def run_all_tests(self) -> Dict:
        """
        运行所有测试用例
        
        Returns:
            完整的测试报告
        """
        print("=" * 60)
        print("RAG精准问答 - 集成测试开始")
        print("=" * 60)
        
        if not self.rag_service.index_ready:
            print("❌ 错误：索引未建立，请先执行 POST /api/rag/index")
            return {"error": "Index not ready"}
        
        for i, test_case in enumerate(STANDARD_TEST_CASES, 1):
            print(f"\n[{i}/{len(STANDARD_TEST_CASES)}] 执行测试: {test_case.id}")
            print(f"问题类型: {test_case.category}")
            print(f"问题: {test_case.question}")
            
            try:
                # 执行RAG查询
                response = await self.rag_service.query(test_case.question, top_k=5)
                
                # 评估结果
                passed, report = test_case.evaluate(
                    response.answer,
                    [c.model_dump() for c in response.citations]
                )
                
                self.test_results.append(report)
                
                # 打印结果
                status = "✓ 通过" if passed else "✗ 失败"
                score = report["metrics"]["total_score"]
                print(f"结果: {status} (评分: {score})")
                
                if passed:
                    print(f"✓ 关键词覆盖: {report['metrics']['keyword_coverage']['found']}/{report['metrics']['keyword_coverage']['total']}")
                    print(f"✓ 引用数: {len(response.citations)}")
                
            except Exception as e:
                print(f"✗ 执行失败: {e}")
                self.test_results.append({
                    "test_id": test_case.id,
                    "passed": False,
                    "error": str(e)
                })
        
        # 生成总结报告
        self._generate_summary()
        return self._format_report()
    
    def _generate_summary(self):
        """生成测试总结"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        
        self.metrics_summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": round(passed_tests / total_tests * 100, 1) if total_tests > 0 else 0,
            "avg_score": round(
                sum(r.get("metrics", {}).get("total_score", 0) for r in self.test_results) / total_tests, 3
            ) if total_tests > 0 else 0,
            "avg_keyword_coverage": round(
                sum(r.get("metrics", {}).get("keyword_coverage", {}).get("coverage", 0) for r in self.test_results) / total_tests, 3
            ) if total_tests > 0 else 0,
            "avg_citation_coverage": round(
                sum(r.get("metrics", {}).get("citation_coverage", {}).get("coverage", 0) for r in self.test_results) / total_tests, 3
            ) if total_tests > 0 else 0,
        }
    
    def _format_report(self) -> Dict:
        """格式化报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self.metrics_summary,
            "test_results": self.test_results,
            "recommendations": self._get_recommendations()
        }
    
    def _get_recommendations(self) -> List[str]:
        """根据测试结果提出优化建议"""
        recommendations = []
        
        if self.metrics_summary.get("pass_rate", 0) < 60:
            recommendations.append("❌ 通过率过低(<60%)，建议：")
            recommendations.append("  1. 检查embedding模型是否正确加载")
            recommendations.append("  2. 检查chunk大小设置是否合理")
            recommendations.append("  3. 检查LLM prompt约束是否清晰")
        
        if self.metrics_summary.get("avg_keyword_coverage", 0) < 0.6:
            recommendations.append("❌ 关键词覆盖度低，建议：")
            recommendations.append("  1. 增加检索chunk数量（top_k参数）")
            recommendations.append("  2. 调整chunk大小，确保覆盖更多信息")
            recommendations.append("  3. 优化LLM生成时的prompt")
        
        if self.metrics_summary.get("avg_citation_coverage", 0) < 0.5:
            recommendations.append("❌ 引用覆盖度不足，建议：")
            recommendations.append("  1. 增加向量检索的top_k参数")
            recommendations.append("  2. 检查元数据是否正确保存")
            recommendations.append("  3. 考虑使用混合检索（向量+关键词）")
        
        if not recommendations:
            recommendations.append("✓ 系统性能良好！")
            if self.metrics_summary.get("pass_rate", 0) >= 80:
                recommendations.append("✓ 通过率优秀，可以考虑以下优化：")
                recommendations.append("  1. 实现混合检索提升精度")
                recommendations.append("  2. 添加答案再排序机制")
                recommendations.append("  3. 收集用户反馈迭代改进")
        
        return recommendations
    
    def save_report(self, filepath: str):
        """保存测试报告"""
        report = self._format_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📊 测试报告已保存: {filepath}")
        return report


# 使用示例
async def run_rag_benchmark():
    """
    运行完整的RAG基准测试
    
    使用方式：
    1. 确保已经上传教材并解析
    2. 执行 POST /api/rag/index 建立索引
    3. 调用此函数进行测试
    """
    from app.services.rag import RAGService
    
    benchmark = RAGBenchmark(RAGService)
    report = await benchmark.run_all_tests()
    
    # 保存报告
    benchmark.save_report("data/rag_benchmark_report.json")
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    summary = report["summary"]
    print(f"总测试数: {summary['total_tests']}")
    print(f"通过: {summary['passed_tests']}")
    print(f"通过率: {summary['pass_rate']}%")
    print(f"平均评分: {summary['avg_score']}")
    print(f"关键词覆盖: {summary['avg_keyword_coverage']:.1%}")
    print(f"引用覆盖: {summary['avg_citation_coverage']:.1%}")
    
    print("\n" + "=" * 60)
    print("优化建议")
    print("=" * 60)
    for rec in report["recommendations"]:
        print(rec)
    
    return report


if __name__ == "__main__":
    # 可以直接运行此脚本进行测试
    # python -m backend.tests.rag_benchmark
    print("请在FastAPI应用中调用 run_rag_benchmark() 函数")

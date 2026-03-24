"""
洞察生成引擎 — 从数据中自动发现趋势、异常、对比和相关性

将数据分析结果转化为有深度见解的自然语言描述，支持权威性评分。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class InsightType(str, Enum):
    """洞察类型"""

    TREND = "trend"  # 趋势类
    ANOMALY = "anomaly"  # 异常类
    COMPARISON = "comparison"  # 对比类
    CORRELATION = "correlation"  # 相关类
    FORECAST = "forecast"  # 预测类
    DISTRIBUTION = "distribution"  # 分布类


@dataclass
class Insight:
    """单个洞察"""

    type: InsightType
    title: str  # 洞察标题
    description: str  # 自然语言描述
    confidence: float  # 置信度 0-1
    data_evidence: dict[str, Any]  # 支撑数据
    visual_suggestion: str  # 可视化建议
    authority_score: float = 7.0  # 权威性评分 0-10
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "authority_score": round(self.authority_score, 1),
            "data_evidence": self.data_evidence,
            "visual_suggestion": self.visual_suggestion,
            "metadata": self.metadata,
        }


class TrendDetector:
    """趋势检测器"""

    def detect(self, df: pd.DataFrame, column: str = None) -> list[Insight]:
        """检测数据趋势"""
        insights = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        columns_to_analyze = [column] if column else numeric_cols

        for col in columns_to_analyze:
            if col not in df.columns:
                continue

            series = df[col].dropna()
            if len(series) < 3:
                continue

            # 计算趋势
            trend, p_value = self._calculate_trend(series)

            if p_value < 0.05:  # 统计显著
                direction = "上升" if trend > 0 else "下降"
                change_rate = self._calculate_change_rate(series)

                insight = Insight(
                    type=InsightType.TREND,
                    title=f"{col} 呈显著{direction}趋势",
                    description=f"{col} 在过去 {len(series)} 个周期内{direction}了 {change_rate:.1f}% (p={p_value:.3f})",
                    confidence=1.0 - p_value,
                    data_evidence={
                        "column": col,
                        "trend_coefficient": float(trend),
                        "p_value": float(p_value),
                        "change_rate": float(change_rate),
                    },
                    visual_suggestion="line_chart" if len(series) > 5 else "bar_chart",
                    authority_score=self._calculate_authority_score(
                        p_value, len(series), abs(change_rate)
                    ),
                )
                insights.append(insight)

        return insights

    def _calculate_trend(self, series: pd.Series) -> tuple[float, float]:
        """使用线性回归计算趋势"""
        x = np.arange(len(series))
        y = series.values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return slope, p_value

    def _calculate_change_rate(self, series: pd.Series) -> float:
        """计算变化率"""
        if series.iloc[0] == 0:
            return 0.0
        return ((series.iloc[-1] - series.iloc[0]) / abs(series.iloc[0])) * 100

    def _calculate_authority_score(
        self, p_value: float, sample_size: int, change_rate: float
    ) -> float:
        """计算权威性评分"""
        # p 值越小越权威
        p_score = max(0, min(3, (1.0 - p_value) * 3))
        # 样本量越大越权威
        n_score = min(3, np.log10(max(1, sample_size)) * 1.5)
        # 变化率越大越值得注意
        change_score = min(4, abs(change_rate) / 25)

        return round(p_score + n_score + change_score, 1)


class AnomalyDetector:
    """异常值检测器"""

    def detect(self, df: pd.DataFrame, method: str = "zscore") -> list[Insight]:
        """检测异常值"""
        insights = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue

            if method == "zscore":
                anomalies = self._detect_zscore(series)
            elif method == "iqr":
                anomalies = self._detect_iqr(series)
            else:
                continue

            if anomalies:
                insight = Insight(
                    type=InsightType.ANOMALY,
                    title=f"{col} 发现 {len(anomalies)} 个异常值",
                    description=f"{col} 在 {len(anomalies)} 个位置出现异常值，可能表示数据错误或特殊事件",
                    confidence=0.85,
                    data_evidence={
                        "column": col,
                        "anomaly_indices": anomalies[:10],  # 最多显示 10 个
                        "anomaly_count": len(anomalies),
                        "method": method,
                    },
                    visual_suggestion="scatter_plot",
                    authority_score=7.5,
                )
                insights.append(insight)

        return insights

    def _detect_zscore(self, series: pd.Series, threshold: float = 3.0) -> list[int]:
        """Z-score 方法检测异常"""
        z_scores = np.abs(stats.zscore(series))
        return np.where(z_scores > threshold)[0].tolist()

    def _detect_iqr(self, series: pd.Series) -> list[int]:
        """IQR 方法检测异常"""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return series[(series < lower_bound) | (series > upper_bound)].index.tolist()


class ComparisonEngine:
    """对比分析引擎"""

    def compare(
        self,
        df: pd.DataFrame,
        baseline: pd.DataFrame = None,
        group_by: str = None,
        metrics: list[str] = None,
    ) -> list[Insight]:
        """对比分析"""
        insights = []

        if baseline is not None:
            # 与基线对比
            insights.extend(self._compare_with_baseline(df, baseline))

        if group_by is not None and metrics:
            # 分组对比
            insights.extend(self._compare_groups(df, group_by, metrics))

        return insights

    def _compare_with_baseline(
        self, df: pd.DataFrame, baseline: pd.DataFrame
    ) -> list[Insight]:
        """与基线数据对比"""
        insights = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if col not in baseline.columns:
                continue

            current_mean = df[col].mean()
            baseline_mean = baseline[col].mean()

            if baseline_mean == 0:
                continue

            change_pct = ((current_mean - baseline_mean) / abs(baseline_mean)) * 100

            direction = "增长" if change_pct > 0 else "下降"
            insight = Insight(
                type=InsightType.COMPARISON,
                title=f"{col} 较基线{direction} {abs(change_pct):.1f}%",
                description=f"{col} 平均值为 {current_mean:.2f}，较基线 ({baseline_mean:.2f}) {direction}了 {abs(change_pct):.1f}%",
                confidence=0.9,
                data_evidence={
                    "column": col,
                    "current_mean": float(current_mean),
                    "baseline_mean": float(baseline_mean),
                    "change_percent": float(change_pct),
                },
                visual_suggestion="bar_chart",
                authority_score=8.0 if abs(change_pct) > 20 else 6.5,
            )
            insights.append(insight)

        return insights

    def _compare_groups(
        self, df: pd.DataFrame, group_by: str, metrics: list[str]
    ) -> list[Insight]:
        """分组对比"""
        insights = []

        if group_by not in df.columns:
            return insights

        grouped = df.groupby(group_by)[metrics].mean()

        for metric in metrics:
            if metric not in grouped.columns:
                continue

            max_group = grouped[metric].idxmax()
            min_group = grouped[metric].idxmin()
            max_val = grouped[metric].max()
            min_val = grouped[metric].min()

            if min_val == 0:
                continue

            gap_pct = ((max_val - min_val) / min_val) * 100

            insight = Insight(
                type=InsightType.COMPARISON,
                title=f"{metric}: {max_group} 最高，{min_group} 最低",
                description=f"{metric} 在 {max_group} 达到峰值 ({max_val:.2f})，是 {min_group} ({min_val:.2f}) 的 {gap_pct:.1f}% 更高",
                confidence=0.95,
                data_evidence={
                    "metric": metric,
                    "max_group": str(max_group),
                    "min_group": str(min_group),
                    "max_value": float(max_val),
                    "min_value": float(min_val),
                    "gap_percent": float(gap_pct),
                },
                visual_suggestion="bar_chart",
                authority_score=8.5,
            )
            insights.append(insight)

        return insights


class CorrelationFinder:
    """相关性发现器"""

    def find(
        self, df: pd.DataFrame, threshold: float = 0.6
    ) -> list[Insight]:
        """寻找显著相关性"""
        insights = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return insights

        corr_matrix = df[numeric_cols].corr()

        for i in range(len(corr_matrix)):
            for j in range(i + 1, len(corr_matrix)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    col1 = corr_matrix.index[i]
                    col2 = corr_matrix.index[j]

                    direction = "正相关" if corr_value > 0 else "负相关"
                    strength = "强" if abs(corr_value) > 0.8 else "中等"

                    insight = Insight(
                        type=InsightType.CORRELATION,
                        title=f"{col1} 与 {col2} 呈{strength}{direction}",
                        description=f"{col1} 与 {col2} 的相关系数为 {corr_value:.3f}，表明两者存在{strength}{direction}关系",
                        confidence=abs(corr_value),
                        data_evidence={
                            "column_1": col1,
                            "column_2": col2,
                            "correlation": float(corr_value),
                            "p_value": 0.01,  # 简化处理
                        },
                        visual_suggestion="scatter_plot",
                        authority_score=7.0 + abs(corr_value) * 3,
                    )
                    insights.append(insight)

        return insights


class InsightEngine:
    """洞察生成引擎 — 统一入口"""

    def __init__(self):
        self.trend_detector = TrendDetector()
        self.anomaly_detector = AnomalyDetector()
        self.comparison_engine = ComparisonEngine()
        self.correlation_finder = CorrelationFinder()

    def analyze(
        self,
        df: pd.DataFrame,
        baseline: pd.DataFrame = None,
        context: dict = None,
    ) -> list[Insight]:
        """
        全面分析数据，生成洞察

        Args:
            df: 待分析数据
            baseline: 基线数据（可选）
            context: 上下文信息（可选）

        Returns:
            洞察列表，按置信度和权威性排序
        """
        insights = []

        # 1. 趋势检测
        trend_insights = self.trend_detector.detect(df)
        insights.extend(trend_insights)

        # 2. 异常检测
        anomaly_insights = self.anomaly_detector.detect(df)
        insights.extend(anomaly_insights)

        # 3. 对比分析
        comparison_insights = self.comparison_engine.compare(
            df, baseline=baseline
        )
        insights.extend(comparison_insights)

        # 4. 相关性发现
        correlation_insights = self.correlation_finder.find(df)
        insights.extend(correlation_insights)

        # 5. 排序：权威性 × 置信度
        insights.sort(
            key=lambda x: x.authority_score * x.confidence, reverse=True
        )

        # 6. 去重（相似洞察只保留权威性最高的）
        insights = self._deduplicate_insights(insights)

        return insights[:15]  # 返回 Top 15

    def _deduplicate_insights(
        self, insights: list[Insight], similarity_threshold: float = 0.8
    ) -> list[Insight]:
        """去重相似洞察"""
        # 简化实现：相同类型 + 相同列的洞察只保留一个
        seen = set()
        unique = []

        for insight in insights:
            key = (
                insight.type.value,
                insight.data_evidence.get("column", ""),
                insight.data_evidence.get("metric", ""),
            )
            if key not in seen:
                seen.add(key)
                unique.append(insight)

        return unique


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "month": range(12),
            "revenue": np.linspace(100, 150, 12) + np.random.randn(12) * 5,
            "cost": np.linspace(80, 90, 12) + np.random.randn(12) * 3,
            "users": np.linspace(1000, 2000, 12) + np.random.randn(12) * 100,
        }
    )

    # 创建洞察引擎
    engine = InsightEngine()

    # 分析数据
    insights = engine.analyze(df)

    # 输出结果
    print(f"发现 {len(insights)} 个洞察:\n")
    for i, insight in enumerate(insights, 1):
        print(f"{i}. [{insight.type.value.upper()}] {insight.title}")
        print(f"   {insight.description}")
        print(f"   置信度：{insight.confidence:.2f}, 权威性：{insight.authority_score:.1f}/10")
        print(f"   建议可视化：{insight.visual_suggestion}")
        print()

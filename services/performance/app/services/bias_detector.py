"""
Bias detection for performance reviews — delegates to shared.bias_analyzer.
No duplicate logic here.
"""
from shared.bias_analyzer import BiasAnalyzer, BiasAnalysisResult

__all__ = ["BiasAnalyzer", "BiasAnalysisResult"]

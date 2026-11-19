"""
MoE-SHD 项目包
混合专家大模型蜜罐统一优化部署
"""

# 导入核心模块
try:
    from .core.module_a_scb import SCBFilter, SCBScore
    print("[OK] 核心模块: 成功导入 SCBFilter")
except ImportError as e:
    print("[ERROR] 核心模块导入失败:", e)

try:
    from .core.module_b_ose import OSEOptimizer
    print("[OK] 核心模块: 成功导入 OSEOptimizer")
except ImportError as e:
    print("[ERROR] 导入 OSEOptimizer 失败:", e)

try:
    from .core.module_c_steiner import SteinerTreeBuilder
    print("[OK] 核心模块: 成功导入 SteinerTreeBuilder")
except ImportError as e:
    print("[ERROR] 核心模块导入失败:", e)

try:
    from .core.module_d_ga import GeneticAlgorithmSolver
    print("[OK] 核心模块: 成功导入 GeneticAlgorithmSolver")
except ImportError as e:
    print("[ERROR] 核心模块导入失败:", e)

# 导入配置模块
try:
    from .data_structures.profiles import ConfigManager, EnhancedConfigManager
    print("[OK] 配置模块导入成功")
except ImportError as e:
    print("[ERROR] 配置模块导入失败:", e)

# 导入评估模块
try:
    from .evaluation.evaluator import Evaluator
    from .evaluation.benchmark import BenchmarkRunner, Benchmark
    from .evaluation.pareto import ParetoAnalyzer
    print("[OK] 评估模块导入成功")
except ImportError as e:
    print("[ERROR] 评估模块导入失败:", e)

# 导入对比算法模块
try:
    from .comparison.random_k import RandomKAlgorithm
    print("[OK] 对比算法模块导入成功")
except ImportError as e:
    print("[ERROR] 对比算法模块导入失败:", e)

try:
    from .comparison.k_medoids import KMedoidsAlgorithm
    print("[OK] 对比算法模块导入成功")
except ImportError as e:
    print("[ERROR] 对比算法模块导入失败:", e)

# 导入实验模块
try:
    from .experiments.test_data_generator import TestDataGenerator
    print("[OK] 实验模块: 成功导入 TestDataGenerator")
except ImportError as e:
    print("[ERROR] 实验模块导入失败:", e)

try:
    from .experiments.batch_runner import BatchRunner
    print("[OK] 实验模块: 成功导入 BatchRunner")
except ImportError as e:
    print("[ERROR] 实验模块导入失败:", e)

try:
    from .experiments.moe_shd_wrapper import MoESHDWrapper
    print("[OK] 实验模块: 成功导入 MoESHDWrapper")
    print("[OK] MoE-SHD 实验模块初始化完成")
except ImportError as e:
    print("[ERROR] 导入MoE-SHD核心模块失败:", e)

# 导入工具模块
try:
    from .utils.constraints import ConstraintChecker
    from .utils.normalization import Normalizer
    from .utils.visualization import GraphVisualizer, ResultVisualizer
    print("[OK] 工具模块导入成功")
except ImportError as e:
    print("[ERROR] 工具模块导入失败:", e)

print("[OK] MoE-SHD 项目包初始化完成")

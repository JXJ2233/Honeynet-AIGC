"""
工具模块 - 包含约束检查、归一化、可视化等工具
基于斯坦纳树的混合专家大模型蜜罐统一优化部署系统 - 工具模块
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入工具模块的各个组件
try:
    from .constraints import ConstraintChecker
    print("[OK] 工具模块: 成功导入 ConstraintChecker")
except ImportError as e:
    print(f"[WARNING]  工具模块: 导入 ConstraintChecker 失败: {e}")
    ConstraintChecker = None

try:
    from .normalization import Normalizer, normalize, NormalizationMethod, NormalizationSystem
    print("[OK] 工具模块: 成功导入 Normalizer")
except ImportError as e:
    print(f"[WARNING]  工具模块: 导入 Normalizer 失败: {e}")
    Normalizer = None
    normalize = None
    NormalizationMethod = None

try:
    from .visualization import GraphVisualizer, ResultVisualizer
    print("[OK] 工具模块: 成功导入 可视化工具")
except ImportError as e:
    print(f"[WARNING]  工具模块: 导入 可视化工具 失败: {e}")
    GraphVisualizer = None
    ResultVisualizer = None

# 定义公开的API
__all__ = [
    'ConstraintChecker',
    'Normalizer',
    'normalize',
    'NormalizationMethod',
    'NormalizationSystem',
    'GraphVisualizer',
    'ResultVisualizer'
]

print("[OK] MoE-SHD 工具模块初始化完成")

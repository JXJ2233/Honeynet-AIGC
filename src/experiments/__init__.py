# src/experiments/__init__.py
"""
实验模块 - 包含测试数据生成、批量测试和MoE-SHD包装器
基于斯坦纳树的混合专家大模型蜜罐统一优化部署系统 - 实验模块
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入实验模块的各个组件
try:
    from .test_data_generator import TestDataGenerator
    print("[OK] 实验模块: 成功导入 TestDataGenerator")
except ImportError as e:
    print(f"[WARNING]  实验模块: 导入 TestDataGenerator 失败: {e}")
    TestDataGenerator = None

try:
    from .batch_runner import BatchRunner
    print("[OK] 实验模块: 成功导入 BatchRunner")
except ImportError as e:
    print(f"[WARNING]  实验模块: 导入 BatchRunner 失败: {e}")
    BatchRunner = None

try:
    from .moe_shd_wrapper import MoESHDWrapper
    print("[OK] 实验模块: 成功导入 MoESHDWrapper")
except ImportError as e:
    print(f"[WARNING]  实验模块: 导入 MoESHDWrapper 失败: {e}")
    MoESHDWrapper = None

# 定义公开的API
__all__ = ['TestDataGenerator', 'BatchRunner', 'MoESHDWrapper']

print("[OK] MoE-SHD 实验模块初始化完成")
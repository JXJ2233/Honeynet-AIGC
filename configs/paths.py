"""
MoE-SHD 项目路径配置
"""
from pathlib import Path
import sys

# 获取项目根目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    PROJECT_ROOT = Path(sys.executable).parent
else:
    # 如果是源代码运行
    PROJECT_ROOT = Path(__file__).parent.parent.parent

# 定义项目路径
PATHS = {
    "PROJECT_ROOT": PROJECT_ROOT,
    "CONFIGS": PROJECT_ROOT / "configs",
    "RESULTS": PROJECT_ROOT / "results",
    "DATA": PROJECT_ROOT / "data",
    "SRC": PROJECT_ROOT / "src",
    "TESTS": PROJECT_ROOT / "tests",
    "DOCS": PROJECT_ROOT / "docs",
    "VISUALIZATIONS": PROJECT_ROOT / "results" / "visualizations",
    "LOGS": PROJECT_ROOT / "results" / "logs",
}

# 默认配置文件路径
DEFAULT_CONFIG = PATHS["CONFIGS"] / "default_config.yaml"
SAMPLE_CONFIG = PATHS["CONFIGS"] / "sample_config.yaml"

# 创建目录结构
def create_project_structure():
    """创建项目目录结构"""
    for name, path in PATHS.items():
        if name not in ["PROJECT_ROOT", "SRC"]:  # 不创建项目根目录和src目录
            path.mkdir(parents=True, exist_ok=True)
            print(f" 创建目录: {path}")
    
    # 创建特殊子目录
    (PATHS["RESULTS"] / "runs").mkdir(exist_ok=True)
    (PATHS["RESULTS"] / "benchmarks").mkdir(exist_ok=True)
    (PATHS["DATA"] / "raw").mkdir(exist_ok=True)
    (PATHS["DATA"] / "processed").mkdir(exist_ok=True)
    
    return True

def check_project_structure():
    """检查项目目录结构"""
    missing = []
    for name, path in PATHS.items():
        if not path.exists():
            missing.append((name, path))
    
    if missing:
        print("  缺少以下目录:")
        for name, path in missing:
            print(f"  - {name}: {path}")
        return False
    return True

def get_config_path(config_name: str = None) -> Path:
    """获取配置文件路径"""
    if config_name is None:
        return DEFAULT_CONFIG
    
    config_path = Path(config_name)
    if not config_path.is_absolute():
        # 如果是相对路径，则尝试在多个位置查找
        possible_paths = [
            config_path,  # 当前工作目录
            PATHS["CONFIGS"] / config_path,  # configs目录
            PROJECT_ROOT / config_path,  # 项目根目录
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
    
    # 如果都没找到，返回默认路径
    return DEFAULT_CONFIG

if __name__ == "__main__":
    create_project_structure()
    print(" 项目目录结构创建完成！")
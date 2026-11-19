"""
配置管理模块 - 配置文件管理增强版本
支持多场景、配置档案、实验配置等功能
"""

from typing import Dict, Any, List, Optional, Union
import yaml
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import copy


@dataclass
class ConfigProfile:
    """配置档案类"""
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def save(self, filepath: Union[str, Path]) -> None:
        """保存配置到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'ConfigProfile':
        """从文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data['name'],
            description=data['description'],
            parameters=data['parameters'],
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置参数，支持嵌套键访问"""
        keys = key.split('.')
        value = self.parameters
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置参数"""
        keys = key.split('.')
        params = self.parameters
        
        for k in keys[:-1]:
            if k not in params:
                params[k] = {}
            params = params[k]
        
        params[keys[-1]] = value
        self.updated_at = datetime.now().isoformat()


@dataclass
class ExperimentProfile:
    """实验配置类"""
    experiment_id: str
    name: str
    scenario: str = "default"
    config_profile: Optional[ConfigProfile] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """后初始化处理"""
        if self.config_profile is None:
            self.config_profile = ConfigProfile(
                name=f"profile_{self.experiment_id}",
                description=f"Experiment {self.experiment_id} profile"
            )
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取实验参数"""
        # 首先检查实验特定参数
        if key in self.parameters:
            return self.parameters[key]
        
        # 然后检查配置档案参数
        if self.config_profile:
            return self.config_profile.get(key, default)
        
        return default
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.config_profile:
            data['config_profile'] = self.config_profile.to_dict()
        return data


class EnhancedConfigManager:
    """
    增强配置管理器
    支持多场景、配置档案管理、嵌套键访问等功能
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如为None则使用默认配置
        """
        self.config_data: Dict[str, Any] = {}
        self.profiles: Dict[str, ConfigProfile] = {}
        self.experiments: Dict[str, ExperimentProfile] = {}
        self.current_scenario: Optional[str] = None
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        
        if config_file:
            self.load_config(config_file)
        else:
            self._init_default_config()
        
        # 加载内置场景
        self._load_scenarios()
    
    def _init_default_config(self) -> None:
        """初始化默认配置"""
        self.config_data = {
            'algorithm': {
                'scb_filter': {
                    'alpha': 0.4,
                    'beta': 0.3,
                    'gamma': 0.3,
                    'keep_ratio': 0.4,
                    'security_weight': 0.5,
                    'cost_weight': 0.3,
                    'balance_weight': 0.2
                },
                'ga_solver': {
                    'population_size': 100,
                    'generations': 50,
                    'crossover_rate': 0.8,
                    'mutation_rate': 0.1,
                    'elite_count': 5
                }
            },
            'scenarios': {
                'default': {
                    'weights': {
                        'economic': 0.33,
                        'performance': 0.33,
                        'security': 0.34
                    }
                },
                'high_security': {
                    'weights': {
                        'economic': 0.2,
                        'performance': 0.1,
                        'security': 0.7
                    }
                },
                'low_cost': {
                    'weights': {
                        'economic': 0.5,
                        'performance': 0.2,
                        'security': 0.3
                    }
                },
                'real_time': {
                    'weights': {
                        'economic': 0.2,
                        'performance': 0.5,
                        'security': 0.3
                    }
                }
            },
            'constraints': {
                'budget': 100000.0,
                'max_latency_core_aggregation': 20.0,
                'min_security_coverage': 0.7,
                'resource_limits': {
                    'cpu': 0.3,
                    'memory': 0.2,
                    'bandwidth': 0.4
                }
            },
            'visualization': {
                'enable': True,
                'output_dir': 'results/visualizations',
                'dpi': 300,
                'save_format': 'png'
            }
        }
    
    def _load_scenarios(self) -> None:
        """加载场景配置"""
        scenarios = self.get('scenarios', {})
        for scenario_name, config in scenarios.items():
            self.scenarios[scenario_name] = config
    
    def load_config(self, config_file: Union[str, Path]) -> None:
        """加载配置文件"""
        filepath = Path(config_file)
        
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.suffix in ['.yaml', '.yml']:
                    self.config_data = yaml.safe_load(f)
                elif filepath.suffix == '.json':
                    self.config_data = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {filepath.suffix}")
            
            print(f" 配置已加载: {config_file}")
            
            # 重新加载场景
            self._load_scenarios()
            
        except Exception as e:
            print(f" 错误: 加载配置文件失败: {e}")
            raise
    
    def save_config(self, filepath: Union[str, Path]) -> None:
        """保存配置到文件"""
        path = Path(filepath)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    yaml.dump(self.config_data, f, default_flow_style=False)
                elif path.suffix == '.json':
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {path.suffix}")
            
            print(f" 配置已保存: {filepath}")
            
        except Exception as e:
            print(f" 错误: 保存配置文件失败: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置参数，支持嵌套键
        
        Args:
            key: 参数键，支持点号分隔的嵌套键，如 'algorithm.scb_filter.alpha'
            default: 默认值（如果键不存在）
            
        Returns:
            参数值或默认值
        """
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            print(f" 警告: 获取参数 {key} 失败: {e}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置参数，支持嵌套键
        
        Args:
            key: 参数键，支持点号分隔的嵌套键
            value: 参数值
        """
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def set_scenario(self, scenario_name: str) -> bool:
        """
        设置当前场景
        
        Args:
            scenario_name: 场景名称
            
        Returns:
            是否成功设置
        """
        if scenario_name in self.scenarios:
            self.current_scenario = scenario_name
            print(f" 已切换到场景: {scenario_name}")
            return True
        else:
            print(f" 警告: 场景 '{scenario_name}' 不存在")
            return False
    
    def get_scenario_weights(self, scenario_name: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        获取场景权重
        
        Args:
            scenario_name: 场景名称，如果为None则使用当前场景
            
        Returns:
            权重字典或None
        """
        scenario = scenario_name or self.current_scenario
        if scenario in self.scenarios:
            return self.scenarios[scenario].get('weights', {})
        return None
    
    def create_profile(self, name: str, description: str = "") -> ConfigProfile:
        """
        创建配置档案
        
        Args:
            name: 档案名称
            description: 档案描述
            
        Returns:
            配置档案对象
        """
        profile = ConfigProfile(
            name=name,
            description=description,
            parameters=copy.deepcopy(self.config_data)
        )
        
        self.profiles[name] = profile
        return profile
    
    def load_profile(self, profile_name: str) -> bool:
        """
        加载配置档案
        
        Args:
            profile_name: 档案名称
            
        Returns:
            是否成功加载
        """
        if profile_name in self.profiles:
            self.config_data = copy.deepcopy(self.profiles[profile_name].parameters)
            print(f" 配置档案已加载: {profile_name}")
            return True
        else:
            print(f" 警告: 配置档案 '{profile_name}' 不存在")
            return False
    
    def create_experiment_profile(self, 
                                  experiment_id: str,
                                  name: str,
                                  scenario: str = "default",
                                  config_profile: Optional[ConfigProfile] = None) -> ExperimentProfile:
        """
        创建实验配置档案
        
        Args:
            experiment_id: 实验ID
            name: 实验名称
            scenario: 场景名称
            config_profile: 配置档案
            
        Returns:
            实验配置档案对象
        """
        profile = ExperimentProfile(
            experiment_id=experiment_id,
            name=name,
            scenario=scenario,
            config_profile=config_profile
        )
        
        self.experiments[experiment_id] = profile
        return profile
    
    def print_summary(self) -> None:
        """打印配置摘要"""
        print("=" * 60)
        print("配置管理器摘要")
        print("=" * 60)
        
        print(f"当前场景: {self.current_scenario or '默认'}")
        
        # 打印可用场景
        print(f"\n可用场景 ({len(self.scenarios)}个):")
        for scenario in self.scenarios.keys():
            weights = self.scenarios[scenario].get('weights', {})
            print(f"  - {scenario}: {weights}")
        
        # 打印主要算法参数
        print(f"\n算法参数:")
        algorithm_config = self.get('algorithm', {})
        for algo_name, params in algorithm_config.items():
            print(f"  [{algo_name.upper()}]")
            for key, value in params.items():
                if not isinstance(value, dict):
                    print(f"    {key}: {value}")
        
        # 打印配置档案
        print(f"\n配置档案 ({len(self.profiles)}个):")
        for profile_name in self.profiles.keys():
            print(f"  - {profile_name}")
        
        # 打印实验配置
        print(f"\n实验配置 ({len(self.experiments)}个):")
        for exp_id, exp_profile in self.experiments.items():
            print(f"  - {exp_id}: {exp_profile.name} ({exp_profile.scenario})")
        
        print("=" * 60)
    
    def export_to_json(self) -> str:
        """导出配置为JSON字符串"""
        return json.dumps(self.config_data, indent=2, ensure_ascii=False)
    
    def get_all_scenarios(self) -> List[str]:
        """获取所有可用场景"""
        return list(self.scenarios.keys())


# 默认配置管理器实例
default_config_manager = EnhancedConfigManager()
# 添加在profiles.py文件末尾

# ================ 兼容性适配器 ================
class ConfigManager(EnhancedConfigManager):
    """ConfigManager 兼容类，用于向后兼容"""
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        super().__init__(config_file=config_path)
    
    def load_config(self, config_file: Union[str, Path]) -> None:
        """兼容原有接口"""
        return super().load_config(config_file)
    
    def save_config(self, filepath: Union[str, Path]) -> None:
        """兼容原有接口"""
        return super().save_config(filepath)
    
    def get(self, key: str, default: Any = None) -> Any:
        """兼容原有接口"""
        return super().get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """兼容原有接口"""
        return super().set(key, value)

# 提供向后兼容的默认实例
default_config_manager = ConfigManager()

# 添加__all__导出
__all__ = [
    'ConfigProfile',
    'ExperimentProfile', 
    'EnhancedConfigManager',
    'ConfigManager',  # 新增
    'default_config_manager'
]
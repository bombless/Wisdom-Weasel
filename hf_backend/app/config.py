"""配置管理模块"""
import json
from pathlib import Path
from typing import Any, Optional
import torch


class Config:
    """从JSON文件加载配置"""
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
    DEFAULT_CONFIG = {
        "model_id": "your-model-name",
        "torch_dtype": "bfloat16",
        "device_map": "auto",
        "generation": {
            "max_new_tokens_no_constraint": 4,
            "num_beams": 10,
            "num_return_sequences": 5,
            "num_beam_groups": 5,
            "diversity_penalty_no_constraint": 100.0,
            "diversity_penalty_with_constraint": 0.5
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件，不存在则使用默认配置"""
        merged = self.DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    merged.update(json.load(f))
                print(f"配置已从 {self.config_path} 加载")
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
        else:
            print(f"配置文件不存在: {self.config_path}，使用默认配置")
        return merged
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def get_model_id(self) -> str:
        return self.get("model_id")
    
    def get_torch_dtype(self) -> torch.dtype:
        return getattr(torch, self.get("torch_dtype"))
    
    def get_device_map(self) -> str:
        return self.get("device_map")
    
    def get_generation_config(self) -> dict:
        return self.get("generation", {})
    
    def get_max_new_tokens_no_constraint(self) -> int:
        return self.get("generation", {}).get("max_new_tokens_no_constraint", 4)
    
    def get_num_beams(self) -> int:
        return self.get("generation", {}).get("num_beams", 10)
    
    def get_num_return_sequences(self) -> int:
        return self.get("generation", {}).get("num_return_sequences", 5)
    
    def get_num_beam_groups(self) -> int:
        return self.get("generation", {}).get("num_beam_groups", 5)
    
    def get_diversity_penalty_no_constraint(self) -> float:
        return self.get("generation", {}).get("diversity_penalty_no_constraint", 100.0)
    
    def get_diversity_penalty_with_constraint(self) -> float:
        return self.get("generation", {}).get("diversity_penalty_with_constraint", 0.5)
    
    def to_dict(self) -> dict:
        return self.config.copy()


_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance

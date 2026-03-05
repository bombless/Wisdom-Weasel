"""
模型管理器：负责加载和管理LLM模型和tokenizer
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Optional
import os


from app.pinyin_constraint import mapping_pinyin_to_ids


class ModelManager:
    """模型管理器，负责加载和初始化模型"""
    
    def __init__(
        self,
        model_id: str,
        torch_dtype: torch.dtype = torch.bfloat16,
        device_map: str = "auto",
        trust_remote_code: bool = False
    ):
        """
        初始化模型管理器
        
        Args:
            model_id: HuggingFace模型ID或本地路径
            torch_dtype: 模型数据类型
            device_map: 设备映射策略
            trust_remote_code: 是否信任远程代码
        """
        self.model_id = model_id
        self.torch_dtype = torch_dtype
        self.device_map = device_map
        self.trust_remote_code = trust_remote_code
        
        self.model = None
        self.tokenizer = None
        self.device = None
        self.pinyin_mapping = None
        
    def load_model(self):
        """加载模型和tokenizer"""
        print(f"正在加载模型: {self.model_id}")
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=self.trust_remote_code
        )
        
        # 如果tokenizer没有pad_token，设置为eos_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype,
            device_map=self.device_map,
            trust_remote_code=self.trust_remote_code
        )
        
        # 获取模型设备
        if isinstance(self.device_map, str) and self.device_map == "auto":
            # 尝试从模型参数获取设备
            first_param = next(self.model.parameters())
            self.device = first_param.device
        else:
            self.device = torch.device(self.device_map if isinstance(self.device_map, str) else "cuda")
        print("正在构建拼音映射...")
        self.pinyin_mapping = mapping_pinyin_to_ids(self.tokenizer, self.model_id)
        print(f"模型加载完成，设备: {self.device}")


        
    def get_model(self):
        """获取模型实例"""
        if self.model is None:
            raise RuntimeError("模型尚未加载，请先调用load_model()")
        return self.model
    
    def get_tokenizer(self):
        """获取tokenizer实例"""
        if self.tokenizer is None:
            raise RuntimeError("Tokenizer尚未加载，请先调用load_model()")
        return self.tokenizer
    
    def get_device(self):
        """获取模型设备"""
        return self.device

    def get_pinyins_mapping(self):
        """获取拼音到ID的映射"""
        return self.pinyin_mapping

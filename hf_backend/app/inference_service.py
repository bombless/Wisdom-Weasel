"""
推理服务
"""
import torch
from typing import List, Dict, Any, Optional

from transformers import LogitsProcessorList

if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from pinyin_constraint import PinyinConstraintLogitsProcessor, mapping_pinyin_to_ids
    from model_manager import ModelManager
else:
    from .pinyin_constraint import PinyinConstraintLogitsProcessor, mapping_pinyin_to_ids
    from .model_manager import ModelManager
    from .config import get_config
import os


class InferenceService:
    """LLM 推理服务"""

    def __init__(
        self,
        model_manager: ModelManager,
        use_chat_template: bool = True,
    ):
        self.model_manager = model_manager
        self.use_chat_template = use_chat_template
        self.config = get_config()

    def _prepare_inputs(
        self,
        messages: List[Dict[str, str]],
        add_generation_prompt: bool = True,
    ) -> Dict[str, torch.Tensor]:
        
        tokenizer = self.model_manager.get_tokenizer()
        device = self.model_manager.get_device()

        if self.use_chat_template and messages:
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=add_generation_prompt,
                enable_thinking=False,
                return_tensors="pt",
                return_dict=True,
            )
        else:
            text = messages[0]["content"] if messages else ""
            inputs = tokenizer(text, return_tensors="pt", return_dict=True)

        return {k: v.to(device) for k, v in inputs.items()}


    def base_model_generate(
        self,
        prompt: str,
        pinyin_constraints: List[str] = [],
    ):
        """使用基础模型进行生成，支持拼音约束"""
        model = self.model_manager.get_model()
        tokenizer = self.model_manager.get_tokenizer()
        device = self.model_manager.get_device()

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        input_len = inputs["input_ids"].shape[1]

        # 生成参数
        gen_kwargs = {
            "max_new_tokens": self.config.get_max_new_tokens_no_constraint() if len(pinyin_constraints) == 0 else len(pinyin_constraints),
            "num_beams": self.config.get_num_beams(),              
            "num_return_sequences": self.config.get_num_return_sequences(),    
            "num_beam_groups": self.config.get_num_beam_groups(),         
            "diversity_penalty": self.config.get_diversity_penalty_no_constraint() if len(pinyin_constraints) == 0 else self.config.get_diversity_penalty_with_constraint(),     
            "do_sample": False,           
            "pad_token_id": tokenizer.pad_token_id,
            "custom_generate": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "beam_search")),
        }
        
        

        if len(pinyin_constraints)>0:
            pinyin_mapping = self.model_manager.get_pinyins_mapping()
            pinyin_processor = PinyinConstraintLogitsProcessor(
                prompt_length=input_len,
                pinyin_constraints=pinyin_constraints,
                mapping=pinyin_mapping
            )
            gen_kwargs["logits_processor"] = LogitsProcessorList([pinyin_processor])
        
        with torch.no_grad():
            outputs = model.generate(inputs["input_ids"], trust_remote_code=True, **gen_kwargs)
        
        input_token_len = inputs["input_ids"].shape[1]
        results = set()
        for i in outputs:
            generated_tokens = i[input_token_len:]
            generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True,errors='ignore').replace('�', '')
            results.add(generated_text)  
            

        return results

if __name__ == "__main__":
    model_name = r"C:\Users\Ken\Downloads\Qwen3_4B"
    model_manager = ModelManager(model_name)
    model_manager.load_model()

    inferServer=InferenceService(model_manager)
    res=inferServer.base_model_generate("计算机视觉是", pinyin_constraints=['ji','su'])
    for r in res:
        print(r)
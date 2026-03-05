

from pypinyin import Style, pinyin
import torch
from transformers import LogitsProcessor
import os
import json


class PinyinConstraintLogitsProcessor(LogitsProcessor):
    def __init__(self, prompt_length, pinyin_constraints, mapping):
        """
        prompt_length: 输入 prompt 的 token 长度 (用于计算当前生成的是第几个 token)
        pinyin_constraints: 拼音列表，例如 ['t', 'q']
        mapping: 预计算好的 map_initial_to_ids
        """
        self.prompt_len = prompt_length
        self.constraints = pinyin_constraints
        self.mapping = mapping

    def __call__(self, input_ids, scores):
        # input_ids shape: (batch_size, sequence_length)
        # scores shape: (batch_size, vocab_size)
        
        # 计算当前正在生成第几个 token (index 从 0 开始)
        current_step = input_ids.shape[1] - self.prompt_len
        
        # 如果当前步数还在约束列表范围内
        if 0 <= current_step < len(self.constraints):
            target_initial = self.constraints[current_step]
            
            # 获取允许的 token IDs
            allowed_ids = self.mapping.get(target_initial, [])
            
            if not allowed_ids:
                print(f"Warning: No tokens found for initial '{target_initial}', skipping constraint.")
                return scores

            # 创建一个全是 -inf 的 mask
            mask = torch.full_like(scores, float('-inf'))
            
            # 只保留允许的 token 的分数
            mask[:, allowed_ids] = scores[:, allowed_ids]
            
            return mask
        
        # 如果超出了约束范围，不做限制，直接返回原分数
        return scores
    
def get_initial(text):
    # 使用 pypinyin 获取声母 (Style.INITIALS)
    # 过滤掉非中文字符，避免干扰
    if not text or not '\u4e00' <= text[0] <= '\u9fff':
        return None
    res = pinyin(text, style=Style.NORMAL, heteronym=True, strict=False)
    if not res: 
        return None
    # 取第一个字的声母，如果为空（如'a'无声母），则取首字母
    initial = res[0] 
    if not initial and text: # 处理 'a', 'e' 等无声母的情况
        initial = text[0]
    return initial

def mapping_pinyin_to_ids(tokenizer,model_id, cache_path: str = None, force_recompute: bool = False):
    """
    返回 map_initial_to_ids 的映射字典，并可将其持久化到磁盘。

    参数:
      tokenizer: 分词器实例
      cache_path: 可选的缓存文件路径（JSON）。默认放在本文件同目录下的 map_initial_to_ids.json
      force_recompute: 如果为 True，将忽略现有缓存并强制重新计算
    """
    if cache_path is None:
        cache_path = os.path.join(os.path.dirname(__file__), "map_initial_to_ids.json")

    if os.path.exists(cache_path) and not force_recompute:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                if isinstance(cached_data, dict) and cached_data.get("model_id") == model_id:
                    return cached_data["map_initial_to_ids"]
                else:
                    print(f"Warning: model_id mismatch or invalid cache format, recomputing.")
        except Exception as e:
            print(f"Warning: failed to load cache {cache_path}: {e}. Recomputing.")

    map_initial_to_ids = {}

    vocab = tokenizer.get_vocab()
    for token, token_id in vocab.items():
        # 解码 token 为文本
        token_text = tokenizer.decode([token_id], skip_special_tokens=True).strip()
        if not token_text:
            continue

        initials = get_initial(token_text)
        if not initials:
            continue

        # initials 可能是字符串或列表，统一处理为可迭代
        if isinstance(initials, str):
            initials_iter = [initials]
        else:
            initials_iter = list(initials)

        for initial in initials_iter:
            if not initial:
                continue
            for i in range(1, len(initial) + 1):
                prefix = initial[:i]
                map_initial_to_ids.setdefault(prefix, []).append(token_id)

    # 去重并排序以保持稳定性
    for k, v in list(map_initial_to_ids.items()):
        map_initial_to_ids[k] = sorted(set(v))

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"model_id": model_id, "map_initial_to_ids": map_initial_to_ids}, f, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: failed to save cache {cache_path}: {e}")

    return map_initial_to_ids



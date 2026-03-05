# LLM 推理后端

轻量级 HTTP 服务，依赖 Hugging Face `transformers` 提供模型推理。当前版本具有以下特点：

* 对中文句子支持拼音声母约束
* 简单 JSON 配置管理


---

## 要求

* Python 3.10 或更高
* CUDA 可选但建议用于 GPU 运行


## 安装

```bash

cd HF_backend
python -m venv .venv          
.\venv\Scripts\activate       
pip install -U pip
pip install -r requirements.txt
```

更新依赖时请同步调整 `requirements.txt`。

## 配置

选项通过根目录的 `config.json` 提供，示例：

```json
{
  "model_id": "Qwen/Qwen3-4B-Base",
  "torch_dtype": "bfloat16",
  "device_map": "auto",
  "generation": {
    "max_new_tokens_no_constraint": 4,
    "num_beams": 10,
    "num_return_sequences": 5,
    "num_beam_groups": 5,
    "diversity_penalty_no_constraint": 100.0
  }
}
```

支持字段：

* `model_id` – HuggingFace 模型名或本地路径
* `torch_dtype` – PyTorch dtype，如 `bfloat16`、`float16`
* `device_map` – 传给 `from_pretrained(..., device_map=...)` 的值
* `generation` – 生成相关参数的子对象，示例可参见下方；其中
  * `max_new_tokens_no_constraint` – 无声母约束时的最大生成长度
  * `num_beams`, `num_return_sequences`, `num_beam_groups` – beam search 参数：搜索候选数量（需要是分组数的倍数），返回候选数量，搜索分组数
  * `diversity_penalty_no_constraint` 多样性惩罚值, 越大候选词差异越大



## 启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```


## API

所有端点返回 `application/json`。

### `GET /health`

简单的就绪检查：

```json
{"status":"ok"}
```

### `POST /v1/generate/completions`

基础文本生成接口，支持可选的拼音声母约束。

请求体：

```json
{
  "prompt": "计算机视觉是",
  "pinyin_constraints": ["y","men","yan","j"]
}
```

* `prompt` – 上下文文本
* `pinyin_constraints` – 与预期生成字符一一对应的声母列表；
  传空数组或省略字段表示不使用约束。

### 生成参数

新增一组用于调整生成行为的配置项，可以在 `config.json` 的 `generation`
字段内定义，例如：

```json

```

这些值会影响 /v1/generate/completions 接口的内部推理参数。

成功返回：

```json
{"responses":"... 多条候选结果以空格分隔 ..."}
```











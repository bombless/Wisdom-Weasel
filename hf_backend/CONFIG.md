# 配置说明

## 概述
后端参数配置已从环境变量改为配置文件方式。配置文件位于项目根目录的 `config.json`。

## 配置文件位置
```
HF_backend/
├── config.json          # 配置文件（在这里修改参数）
├── requirements.txt
├── README.md
└── app/
    ├── config.py       # 配置加载模块
    ├── main.py
    ├── model_manager.py
    ├── inference_service.py
    └── ...
```

## 配置参数说明

### config.json

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `model_id` | string | "your-model-name" | HuggingFace 模型 ID 或本地模型路径 |
| `torch_dtype` | string | "bfloat16" | PyTorch 数据类型，可选值：`float32`, `float16`, `bfloat16` |
| `device_map` | string | "auto" | 设备映射策略，可选值：`auto`, `cpu`, `cuda`, `cuda:0` 等 |
| `trust_remote_code` | boolean | false | 是否信任远程代码（加载自定义代码时需设为 `true`） |
| `cache_type` | string | "dynamic" | KV 缓存类型 |
| `max_cache_len` | integer | 4096 | 最大缓存长度（字符数） |

## 使用示例

### 修改配置
编辑 `config.json` 文件，修改所需的参数：

```json
{
  "comment": "后端推理服务配置文件",
  "model_id": "meta-llama/Llama-2-7b-chat",
  "torch_dtype": "bfloat16",
  "device_map": "auto",
  "trust_remote_code": false,
  "cache_type": "dynamic",
  "max_cache_len": 4096
}
```

### 启动应用
配置完成后，直接启动应用：
```bash
python -m uvicorn app.main:app --reload
```

应用启动时会自动加载 `config.json` 中的配置参数。

## 配置加载机制

### 加载顺序
1. 首先检查 `config.json` 文件是否存在
2. 如果存在，读取文件内容并解析 JSON
3. 如果不存在或解析失败，使用默认配置
4. 将加载的配置与默认配置合并（已加载的配置优先）

### 迁移从环境变量
如果之前使用环境变量配置，现在需要改为在 `config.json` 中配置：

**环境变量方式（已弃用）：**
```bash
export MODEL_ID="your-model-name"
export TORCH_DTYPE="bfloat16"
export CACHE_TYPE="dynamic"
export MAX_CACHE_LEN="4096"

```

**配置文件方式（新方式）：**
在 `config.json` 中设置相应参数。

## API 调用

### 在代码中获取配置
```python
from app.config import get_config

config = get_config()
model_id = config.get_model_id()
torch_dtype = config.get_torch_dtype()
device_map = config.get_device_map()
trust_remote_code = config.get_trust_remote_code()
cache_type = config.get_cache_type()
max_cache_len = config.get_max_cache_len()

# 或者获取全部配置
all_config = config.to_dict()
```

## 故障排除

### 配置文件不存在
- 应用会打印警告信息并使用默认配置
- 建议在项目根目录创建 `config.json` 文件

### JSON 格式错误
- 应用会打印错误信息并使用默认配置
- 检查 JSON 文件是否有语法错误

### 自定义配置路径
如果需要在非默认位置加载配置文件，可以在代码中指定：
```python
from app.config import Config

config = Config(config_path="/path/to/custom/config.json")
```

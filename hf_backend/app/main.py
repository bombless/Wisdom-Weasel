"""
LLM 推理后端 FastAPI 入口
支持带 KV Cache 的迭代生成与预填充缓存
"""
from contextlib import asynccontextmanager
from typing import List, Optional

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .model_manager import ModelManager
from .inference_service import InferenceService
from .config import get_config
import time


# ---------- 配置 ----------
config = get_config()
MODEL_ID = config.get_model_id()
TORCH_DTYPE = config.get_torch_dtype()


# 全局服务（启动时加载）
model_manager: Optional[ModelManager] = None
inference_service: Optional[InferenceService] = None


# ---------- Pydantic 请求体 ----------
class PinYinConstraintGenerateRequest(BaseModel):
    prompt: str = Field(..., description="用户输入的文本prompt")
    pinyin_constraints: List[str] = Field(..., description="与输入文本对应的拼音约束列表")


# ---------- 生命周期 ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_manager, inference_service
    model_manager = ModelManager(
        model_id=MODEL_ID,
        torch_dtype=TORCH_DTYPE,
        device_map=config.get_device_map(),
        trust_remote_code=False,
    )
    model_manager.load_model()
    inference_service = InferenceService(
        model_manager=model_manager,
        use_chat_template=True,
    )
    yield
    model_manager = None
    inference_service = None


app = FastAPI(
    title="LLM Inference Backend",
    description="基于 transformers 的 LLM 推理后端，支持 KV Cache 迭代生成与预填充",
    version="0.1.0",
    lifespan=lifespan,
)


def get_inference():
    if inference_service is None:
        raise HTTPException(status_code=503, detail="服务未就绪")
    return inference_service


# ---------- 接口 ----------
@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/v1/generate/completions")
def generate_completions(req: PinYinConstraintGenerateRequest):
    """使用Base模型进行生成补全"""
    print("Received request:", req.prompt)
    start_time = time.time()
    svc = get_inference()
    output = svc.base_model_generate(
        prompt=req.prompt,
        pinyin_constraints=req.pinyin_constraints,
    )
    elapsed = time.time() - start_time
    print(f"generate_completions耗时: {elapsed:.3f}s")
    responses = " ".join(output)
    return {"responses": responses}
    
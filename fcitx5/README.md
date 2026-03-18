# Wisdom-Weasel 的 fcitx5 适配说明（Linux）

这个目录提供的是一个“可运行适配层”，不是把 Weasel 的 Windows TSF/IME 代码直接移植到 Linux。

适配思路：

- Linux 输入法前端使用 `fcitx5-rime`
- Rime 侧通过 `lua_translator` 增加 LLM 候选
- LLM 请求发送到仓库里的 `hf_backend`（HTTP API）

## 前置条件

- 已安装：`fcitx5`、`fcitx5-rime`、`librime-lua`、`curl`
- 已有一个可用的 Rime 方案（例如 `luna_pinyin_simp`）
- 能启动并访问 `hf_backend` 的接口：
  - 默认地址：`http://127.0.0.1:8000/v1/generate/completions`

在 Arch Linux 上可参考：

```bash
sudo pacman -S fcitx5 fcitx5-rime librime-lua curl
```

## 一键安装适配层

在仓库根目录执行：

```bash
chmod +x ./fcitx5/install_fcitx5_adapter.sh
./fcitx5/install_fcitx5_adapter.sh \
  --schema luna_pinyin_simp \
  --endpoint http://127.0.0.1:8000/v1/generate/completions
```

脚本会做这些事情：

- 向 `~/.local/share/fcitx5/rime/rime.lua` 写入（或追加）`wisdom_predictor` 译码函数
- 修改 `~/.local/share/fcitx5/rime/<schema>.custom.yaml`，把 `lua_translator@wisdom_predictor` 挂到 translators
- 调用 `rime_deployer --build` 重新编译部署
- 自动备份被修改文件（后缀 `.bak.<timestamp>`）

## 启动 hf_backend（示例）

```bash
cd hf_backend
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 验证

1. 输入法切到对应 schema（例如 `luna_pinyin_simp`）。
2. 连续输入拼音（长度达到 `min_input_length`，默认 2）。
3. 候选栏里会出现标注 `〔LLM〕` 的候选项。

## 常见问题

- 无 `〔LLM〕` 候选：
  - 检查 `hf_backend` 是否运行；
  - `curl http://127.0.0.1:8000/health` 是否返回 `{"status":"ok"}`；
  - 执行 `fcitx5-remote -r` 后重试。
- 想降低卡顿：
  - 调小 `timeout_ms`（例如 300~600）；
  - 提高 `min_input_length`（例如 3）。
- 误改配置：
  - 用脚本生成的 `.bak.<timestamp>` 文件恢复。

# Agent 运行与排障

## 本地运行

```bash
python -m autodev --help
python -m autodev -P <path-to-plan.md> --dry-run
```

## 常见问题

1. `ModuleNotFoundError`
- 先确认激活 `.venv` 或已执行 `pip install -e .`。

2. `autodev: command not found`
- 使用 `python -m autodev` 直接运行，或修正 PATH 到当前虚拟环境。

3. `codex` 不可用
- 检查 `--codex-bin` 配置，确保对应可执行文件存在。

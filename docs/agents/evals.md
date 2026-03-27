# Agent 评测与门禁

## 最低门禁

1. 代码应可通过基础导入/语法检查（例如 `python -m compileall autodev`）。
2. CLI 变更需至少验证一条关键路径（例如 `--help` 或 `--dry-run`）。
3. 文档变更需检查链接与路径是否存在。
4. 测试门禁必须通过：
   - 总覆盖率 `>= 80%`。
   - 有逻辑的代码文件（默认 `autodev/` 下且语句数 `>= 5`，排除 `__init__.py/__main__.py/constants.py`）不得为 `0` 覆盖。

门禁命令：

```bash
.venv/bin/python scripts/check_test_gates.py
```

## 结果记录

- 在交付说明中记录实际执行命令与关键输出。
- 若环境缺依赖导致无法运行，需说明缺失项与影响范围。

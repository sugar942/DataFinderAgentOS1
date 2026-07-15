"""
controllers 包 —— 控制器层（Tornado RequestHandler 实现）
约定：
- 一个业务模块对应一个 .py 文件（auth、home、admin...）
- Handler 职责：接收请求 → 校验参数 → 调用 Model → 渲染 View
"""
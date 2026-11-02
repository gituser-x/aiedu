# 核心代码导读

| 文件 | 来源与公开处理 | 运行范围 |
| --- | --- | --- |
| question-schema/generated_question_schema.py | 从私有项目同名模块原样摘取，纯函数，无配置与凭据 | 独立可运行 |
| task-workflow/conversation_submission.py | 从 compose/conversations.py 选取导入和任务提交视图，去掉其他方法 | 缺少私有模型与任务，不可独立运行 |
| tests/test_question_schema.py | 针对公开模块编写的独立单元测试 | Python 标准库即可运行 |

推荐先读规范化函数，再读边界测试，最后看任务提交中的所有权过滤、锁、请求去重和派发失败处理。公开片段并不覆盖完整应用，不包含提示词体系、检索排序实现、模型配置或数据。

# 系统架构与主链路

![架构](../assets/diagrams/architecture.svg)

```mermaid
flowchart LR
  U[浏览器] --> C[Caddy :80]
  C --> W[Django / Gunicorn]
  W --> D[(PostgreSQL / pgvector)]
  W --> R[(Redis)]
  R --> T[Celery Worker]
  T --> D
  T --> M[硅基流动文本 / 向量接口]
  W --> S[(RustFS / S3)]
  T --> S
```

浏览器通过 Django Session 认证；对话按用户查询。任务提交后先持久化，再派发至 Worker，前端查询持久化状态和结果，避免长生成请求持续占用 Web 连接。数据库、Redis 与对象存储服务部署于容器网络内。

## 找题与组卷

```mermaid
sequenceDiagram
  participant B as 浏览器
  participant W as Django
  participant D as 数据库
  participant Q as Celery Worker
  participant L as 文本模型
  B->>W: 创建对话 / 提交 request_id
  W->>D: 校验所有权、锁定对话、保存任务
  W->>Q: 派发任务
  W-->>B: 202 与当前对话状态
  Q->>D: 检索候选题、更新阶段进度
  opt 允许 AI 补题
    Q->>L: 批量请求补齐题目
    L-->>Q: 结构化内容
    Q->>Q: 规范化、校验、局部修复
  end
  Q->>D: 保存结果或错误
  B->>W: 轮询对话
  W-->>B: 进度 / 题目 / 错误
  B->>W: 保存已选题目
  W->>D: 校验并保存试卷与所有者
```

## 取舍与待完善点

单机 Compose 适合当前低并发展示，部署成本低；它不提供多机高可用。当前公网入口为 HTTP，后续可绑定域名并启用 HTTPS。

数据库事务与队列派发之间仍有故障窗口；当前派发异常会标记任务失败，进一步增强可采用事务发件箱与补偿任务。备用模型和有限重试可以缓解瞬时故障，不能消除供应商不可用。

结构校验解决格式与必要字段问题，无法独立证明知识正确性。答案与解析一致性、数学复算、内容审核是后续重点。

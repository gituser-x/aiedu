# 代表性接口设计

接口来自实际 Django 路由和视图，使用 Session 认证。以下为选取的契约说明，不是完整 API SDK。POST 等修改请求需要 CSRF 令牌；HttpOnly Cookie 不通过 JavaScript 读取，页面隐藏字段供前端设置 X-CSRFToken。

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| GET | `/api/compose/conversations/` | 当前用户对话列表 |
| POST | `/api/compose/conversations/` | 新建当前用户对话，201 |
| GET | `/api/compose/conversations/{id}/` | 当前用户对话与任务状态，200 |
| POST | `/api/compose/conversations/{id}/` | 提交异步任务，202 |
| DELETE | `/api/compose/conversations/{id}/` | 无运行任务时删除对话；忙时 409 |
| GET | `/api/compose/knowledge-tree/` | 组卷知识树 |
| POST | `/api/compose/preview/` | 组卷预览 |
| POST | `/api/compose/save-draft/` | 保存试卷草稿 |

## 提交异步任务

```json
{
  "request_id": "1ef9cd28-f146-453c-b791-72e22cd65f99",
  "payload": {
    "message": "语文2道选择题",
    "request": {"subject": "语文", "grade": "高三", "question_count": 2}
  }
}
```

request_id 为客户端生成的 UUID，在同一对话内用于请求去重。上述 request 为字段示意，完整业务选项由站内表单构建。前端携带当前会话与合法 CSRF 令牌，不包含模型密钥。

响应外层为 `{ "ok": true, "conversation": { "id": "...", "title": "...", "turns": [] } }`；turn 包括 id、message、status、result、error、progress 和 elapsed_seconds。状态包含 queued、running、completed、failed，实际完成后从 result 读取题目。

## 错误与隔离

- 400：JSON、UUID 或字段格式不合法。
- 404：对话不存在，或不属于当前用户。
- 409：当前对话有任务运行，暂不能继续提交或删除。
- 503：任务派发服务暂不可用。
- 身份认证和 CSRF 失败由视图及 Django 中间件处理，前端分别提示。

## 保存结果

`/api/compose/save-draft/` 接受包含 questions 的 result 与 request，可附带 import_ai_to_bank 选项。站内生成流程会附带相应校验数据；此仓库不提供绕过校验的自造请求。保存成功响应含 ok、redirect_url，浏览器据此打开试卷。

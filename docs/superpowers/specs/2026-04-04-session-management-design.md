# 会话管理功能设计

## 概述

为 TonyChat 添加多会话管理功能，支持用户创建、切换、删除对话会话。

## 数据模型

### 新增 sessions 表

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,           -- UUID
    title TEXT,                     -- AI 生成的会话标题
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 现有 messages 表

已有 `session_id` 字段，只需确保索引：
```sql
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
```

## API 设计

### GET /sessions

获取会话列表。

**响应：**
```json
{
    "sessions": [
        {
            "id": "uuid-xxx",
            "title": "如何学习 Python",
            "created_at": "2026-04-04T10:00:00",
            "updated_at": "2026-04-04T10:30:00"
        }
    ]
}
```

### POST /sessions

创建新会话。

**响应：**
```json
{
    "session": {
        "id": "uuid-xxx",
        "title": "新会话",
        "created_at": "2026-04-04T10:00:00",
        "updated_at": "2026-04-04T10:00:00"
    }
}
```

### DELETE /sessions/<id>

删除会话及其所有消息。

**响应：**
```json
{
    "success": true
}
```

### POST /chat

现有接口，新增 `session_id` 参数处理：

- 若 `session_id` 为空，使用或创建默认会话
- 若 `session_id` 对应会话不存在，返回 404

## 前端设计

### 侧边栏布局

```
┌─────────────────────────┐
│ 会话管理           [▼]  │  ← 可折叠区域
│   ├ 新建会话           │
│   └ [会话列表]          │
├─────────────────────────┤
│ 📄 点击或拖拽上传       │
├─────────────────────────┤
│ 已上传文件              │
└─────────────────────────┘
```

### 会话列表项

- 显示 AI 生成的标题
- 当前选中会话高亮显示
- 悬停显示删除按钮
- 点击切换当前会话

### 会话标题生成

首次对话完成后自动生成：

1. 取用户第 1-2 条消息和对应 AI 回复
2. 调用 LLM 生成一句话标题（中文，最多 20 字符）
3. 更新 sessions 表 title 字段
4. 刷新会话列表显示新标题

## 实现步骤

### 后端
1. 创建 sessions 表
2. 实现 `/sessions` API
3. 实现 `/sessions/<id>` DELETE API
4. 修改 `/chat` 接口处理 session_id
5. 添加会话标题生成逻辑

### 前端
1. 添加会话管理折叠 UI
2. 实现会话列表展示
3. 实现新建会话功能
4. 实现切换会话功能
5. 实现删除会话功能
6. 发送聊天请求时携带 session_id
7. 存储当前会话 ID 到 localStorage

## 存储结构

### localStorage

```json
{
    "current_session_id": "uuid-xxx"
}
```

## 错误处理

- 删除会话时级联删除所有消息
- 切换会话时清空当前聊天区域，显示新会话历史
- 无会话时创建默认会话

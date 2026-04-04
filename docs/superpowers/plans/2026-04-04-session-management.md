# Session Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 TonyChat 添加多会话管理功能，支持创建、切换、删除对话会话

**Architecture:** 后端新增 sessions 表和 API，前端添加会话管理 UI，使用 UUID 作为会话标识符，会话标题由 AI 自动生成

**Tech Stack:** Flask, SQLAlchemy, SQLite, JavaScript

---

## 文件结构

```
TonyChat/
├── infrastructure/persistence/database.py   # 新增 Session 模型和会话管理方法
├── api/routes.py                             # 新增 /sessions API 端点
├── application/services/chat_service.py      # 修改：处理 session_id 和标题生成
├── templates/index.html                       # 新增：会话管理 UI
└── chat.db                                   # SQLite 数据库（自动创建）
```

---

## Task 1: 数据库层 - 新增 Session 模型

**Files:**
- Modify: `infrastructure/persistence/database.py:1-102`

- [ ] **Step 1: 添加 Session 模型和数据库方法**

在 `database.py` 中添加：

```python
class Session(Base):
    __tablename__ = 'sessions'

    id = Column(String(36), primary_key=True)  # UUID
    title = Column(String(200), nullable=False, default='新会话')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

在 `Database` 类中添加方法：
- `create_session() -> Session` - 创建新会话
- `get_session(session_id: str) -> Optional[Session]` - 获取指定会话
- `get_all_sessions() -> List[Session]` - 获取所有会话（按 updated_at 倒序）
- `update_session_title(session_id: str, title: str)` - 更新会话标题
- `delete_session(session_id: str)` - 删除会话（同时删除关联消息）
- `touch_session(session_id: str)` - 更新 updated_at 时间戳

- [ ] **Step 2: 测试数据库层**

```python
# 在 python shell 中测试
from infrastructure.persistence.database import get_database
db = get_database()
# 测试创建会话
s = db.create_session()
print(s.id, s.title)
# 测试获取所有会话
sessions = db.get_all_sessions()
print(len(sessions))
# 测试删除
db.delete_session(s.id)
```

---

## Task 2: API 层 - 新增 /sessions 端点

**Files:**
- Modify: `api/routes.py:1-148`

- [ ] **Step 1: 添加 session API 路由**

在 `api/routes.py` 中添加：

```python
@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """获取会话列表"""
    db = get_database()
    sessions = db.get_all_sessions()
    return jsonify({
        'sessions': [
            {
                'id': s.id,
                'title': s.title,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat()
            }
            for s in sessions
        ]
    })


@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    db = get_database()
    session = db.create_session()
    return jsonify({
        'session': {
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        }
    }), 201


@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    db = get_database()
    try:
        db.delete_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404
```

---

## Task 3: Chat Service - 处理 session_id 和标题生成

**Files:**
- Modify: `application/services/chat_service.py:1-155`

- [ ] **Step 1: 修改 chat_sync 方法**

在 `chat_sync` 方法中：
1. 如果 session_id 不存在，自动创建新会话
2. 对话完成后，调用 `generate_session_title` 生成标题

添加新方法：

```python
def generate_session_title(self, session_id: str) -> str:
    """使用 LLM 生成会话标题"""
    db = get_database()
    messages = db.get_conversation_history(session_id, limit=4)

    if len(messages) < 2:
        return "新会话"

    # 取前两条消息
    context_parts = []
    for msg in messages[:2]:
        if msg.role == 'user':
            context_parts.append(f"用户问题: {msg.content[:100]}")
        elif msg.role == 'assistant':
            context_parts.append(f"助手回答: {msg.content[:100]}")

    context_text = "\n".join(context_parts)

    title_prompt = f"""根据以下对话生成一个简短的中文会话标题（最多20字）：

{context_text}

标题："""

    try:
        title = self.llm_adapter.invoke_simple(title_prompt)
        title = title.strip()[:20]
        if not title:
            title = "新会话"
        db.update_session_title(session_id, title)
        return title
    except Exception as e:
        print(f"生成标题失败: {e}")
        return "新会话"
```

修改 `chat_sync` 方法，在对话完成后调用标题生成。

- [ ] **Step 2: 测试 chat_sync with session_id**

启动服务器后测试：
```bash
curl -X POST http://localhost:5001/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好","session_id":"test-session-123"}'
```

---

## Task 4: 前端 - 会话管理 UI

**Files:**
- Modify: `templates/index.html:1-619`

- [ ] **Step 1: 添加会话管理 HTML 结构**

在 `<div class="sidebar">` 中添加：

```html
<div class="session-section">
    <div class="section-header" id="sessionHeader">
        <span>会话管理</span>
        <span class="collapse-icon">▼</span>
    </div>
    <div class="section-content" id="sessionContent">
        <button class="new-session-btn" id="newSessionBtn">+ 新建会话</button>
        <div class="session-list" id="sessionList"></div>
    </div>
</div>
```

- [ ] **Step 2: 添加 CSS 样式**

```css
.session-section {
    margin-bottom: 16px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: #1a1a1a;
}

.section-header:hover {
    color: #666;
}

.collapse-icon {
    transition: transform 0.2s;
    font-size: 10px;
}

.section-header.collapsed .collapse-icon {
    transform: rotate(-90deg);
}

.section-content {
    overflow: hidden;
    transition: max-height 0.2s;
}

.section-content.collapsed {
    max-height: 0 !important;
}

.new-session-btn {
    width: 100%;
    padding: 8px 12px;
    background: #f7f7f8;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    text-align: left;
    margin-bottom: 8px;
}

.new-session-btn:hover {
    background: #e5e5e5;
}

.session-list {
    max-height: 200px;
    overflow-y: auto;
}

.session-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #f7f7f8;
    border-radius: 6px;
    margin-bottom: 4px;
    cursor: pointer;
    font-size: 13px;
}

.session-item:hover {
    background: #e5e5e5;
}

.session-item.active {
    background: #1a1a1a;
    color: #fff;
}

.session-item .session-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.session-item .session-delete {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    padding: 4px;
    font-size: 14px;
    opacity: 0;
}

.session-item:hover .session-delete {
    opacity: 1;
}

.session-item .session-delete:hover {
    color: #ff4444;
}
```

- [ ] **Step 3: 添加 JavaScript 逻辑**

添加全局变量和函数：

```javascript
let currentSessionId = localStorage.getItem('current_session_id');
let sessions = [];

// 加载会话列表
async function loadSessions() {
    try {
        const response = await fetch('/sessions');
        const result = await response.json();
        sessions = result.sessions;
        renderSessions();
    } catch (error) {
        console.error('加载会话列表失败:', error);
    }
}

// 渲染会话列表
function renderSessions() {
    const sessionList = document.getElementById('sessionList');
    if (sessions.length === 0) {
        sessionList.innerHTML = '<div style="color: #999; font-size: 12px;">暂无会话</div>';
        return;
    }
    sessionList.innerHTML = sessions.map(s => `
        <div class="session-item ${s.id === currentSessionId ? 'active' : ''}"
             onclick="switchSession('${s.id}')">
            <span class="session-title">${s.title}</span>
            <button class="session-delete" onclick="event.stopPropagation(); deleteSession('${s.id}')">&times;</button>
        </div>
    `).join('');
}

// 创建新会话
async function createSession() {
    try {
        const response = await fetch('/sessions', { method: 'POST' });
        const result = await response.json();
        currentSessionId = result.session.id;
        localStorage.setItem('current_session_id', currentSessionId);
        await loadSessions();
        clearMessages();
    } catch (error) {
        console.error('创建会话失败:', error);
    }
}

// 切换会话
async function switchSession(sessionId) {
    if (sessionId === currentSessionId) return;
    currentSessionId = sessionId;
    localStorage.setItem('current_session_id', sessionId);
    renderSessions();
    await loadMessagesForSession(sessionId);
}

// 删除会话
async function deleteSession(sessionId) {
    if (!confirm('确定删除该会话吗？')) return;
    try {
        await fetch(`/sessions/${sessionId}`, { method: 'DELETE' });
        if (currentSessionId === sessionId) {
            currentSessionId = null;
            localStorage.removeItem('current_session_id');
            clearMessages();
        }
        await loadSessions();
    } catch (error) {
        console.error('删除会话失败:', error);
    }
}

// 加载指定会话的消息
async function loadMessagesForSession(sessionId) {
    // TODO: 需要后端新增 API 或从现有聊天响应中获取
    clearMessages();
}

// 清空消息显示
function clearMessages() {
    const messages = document.getElementById('messages');
    messages.innerHTML = `
        <div class="empty-state" id="emptyState">
            <div class="empty-state-icon">💬</div>
            <div class="empty-state-text">上传文档后开始提问</div>
        </div>
    `;
}

// 折叠功能
document.getElementById('sessionHeader').addEventListener('click', () => {
    const header = document.getElementById('sessionHeader');
    const content = document.getElementById('sessionContent');
    header.classList.toggle('collapsed');
    content.classList.toggle('collapsed');
});
```

- [ ] **Step 4: 修改 sendMessage 函数携带 session_id**

修改 `sendMessage` 函数中的 fetch 请求：

```javascript
// 确保有当前会话
if (!currentSessionId) {
    await createSession();
}

const response = await fetch('/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: message,
        model: currentModel,
        session_id: currentSessionId
    })
});
```

- [ ] **Step 5: 初始化时加载会话**

在 `loadFiles()` 后添加：

```javascript
// Initialize
loadFiles();
loadSessions();  // 新增
```

- [ ] **Step 6: 测试完整流程**

1. 刷新页面，检查会话列表是否显示
2. 点击"新建会话"
3. 发送消息，检查 session_id 是否正确传递
4. 检查后端数据库中 messages 表的 session_id

---

## Task 5: 标题生成触发

**Files:**
- Modify: `application/services/chat_service.py`

- [ ] **Step 1: 在 chat_sync 完成后触发标题生成**

修改 `chat_sync` 方法末尾：

```python
# 保存到历史
self._add_to_history(session_id, "user", question)
self._add_to_history(session_id, "assistant", response)

# 检查是否需要生成标题（只有首条消息后才生成）
db = get_database()
session = db.get_session(session_id)
if session and session.title == '新会话':
    self.generate_session_title(session_id)

return response
```

---

## 验证清单

- [ ] 数据库 sessions 表正确创建
- [ ] GET /sessions 返回会话列表
- [ ] POST /sessions 创建新会话
- [ ] DELETE /sessions/<id> 删除会话
- [ ] POST /chat 正确使用 session_id
- [ ] 前端显示会话列表
- [ ] 前端创建/切换/删除会话功能正常
- [ ] 对话完成后 AI 生成会话标题
- [ ] 刷新页面后会话保持

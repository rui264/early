# 项目文件结构说明

## 核心文件

### 1. **langgraph_multi_agent.py** - 主要系统文件
- ✅ **保留** - 真正的多代理协作系统
- 功能：多Agent并行处理、协作、智能结果整合
- 支持：文件上传、数学计算、搜索、知识库问答

### 2. **core_api.py** - 接口文件
- ✅ **保留** - 已修改为调用新系统
- 功能：为FastAPI等外部接口提供统一入口
- 接口：`multi_agent_ask()`, `upload_knowledge_file()`, `get_chat_history()`

### 3. **agents/** - Agent工具目录
- ✅ **保留** - 各个专业Agent的工具函数
- `agent_math.py` - 数学计算工具
- `agent_search.py` - 搜索工具
- `agent_knowledge.py` - 知识库工具
- `agent_fileqa.py` - 文件问答工具

### 4. **其他支持文件**
- ✅ **保留** - `llm_factory.py`, `memory_manager.py` 等

## 已删除的旧文件

### ❌ **muti_agent_main.py** - 已删除
- 原因：功能已被 `langgraph_multi_agent.py` 替代
- 新系统更强大，支持真正的多Agent协作

### ❌ **agent_executor.py** - 已删除
- 原因：功能已集成到 `langgraph_multi_agent.py` 中
- 新系统使用LangGraph框架，更现代化

## 使用方法

### 1. 直接使用新系统
```bash
python langgraph_multi_agent.py
```

### 2. 通过API接口使用
```python
from core_api import multi_agent_ask, upload_knowledge_file

# 问答
result = multi_agent_ask("session_123", "什么是人工智能？")

# 文件上传
upload_result = upload_knowledge_file("session_123", "test.pdf")
```

### 3. 文件上传和问答
```
upload test_document.txt
test_document.txt|这个文件的主要内容是什么？
```

## 系统特点

### 新系统优势：
1. **真正的多Agent协作** - 多个Agent并行处理
2. **智能路由** - 根据问题类型自动选择Agent
3. **结果整合** - 智能整合多个Agent的结果
4. **文件支持** - 完整的文件上传和问答功能
5. **现代化架构** - 基于LangGraph框架

### 兼容性：
- ✅ 保持API接口不变
- ✅ 支持所有原有功能
- ✅ 增强的文件处理能力
- ✅ 更好的错误处理和调试信息

## 迁移说明

从旧系统迁移到新系统：
1. **功能完全兼容** - 所有原有功能都保留
2. **性能提升** - 多Agent协作提供更好的结果
3. **扩展性增强** - 更容易添加新的Agent类型
4. **维护性改善** - 代码结构更清晰

## 测试建议

1. **基础功能测试**：
   ```bash
   python langgraph_multi_agent.py
   ```

2. **文件功能测试**：
   ```
   upload test_document.txt
   test_document.txt|文件内容是什么？
   ```

3. **多Agent协作测试**：
   ```
   计算100元能买几束花，并搜索当前花的价格
   ``` 
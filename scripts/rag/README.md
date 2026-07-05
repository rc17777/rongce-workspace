# RAG 知识库脚本

用途：本地知识库索引重建、查询、Web 服务和配置。

常见脚本：

- `rag_config.py`：RAG 路径/配置。
- `rag_rebuild.py` / `rag_build_index.py`：重建索引。
- `rag_query.py`：命令行查询。
- `rag_server.py` / `rag_web.py`：本地 Web 服务。
- `rag_watcher.py`：文件变更监控。

注意：不要删除 `.rag_index/` 前先确认重建脚本可用。索引文件很大，但属于可重建资产。

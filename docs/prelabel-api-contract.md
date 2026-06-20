# Prelabel API Contract (MVP)

本文档用于固定主站与 prelabel-service 的接口边界，方便后续替换 mock pipeline 为真实 pipeline。

## 1. 主站 API（对前端）

### 1.1 创建任务

- Method: `POST`
- Path: `/api/prelabel/create`
- Request JSON:

```json
{
  "day_id": "YYYYMMDD",
  "force": false
}
```

- Response JSON:

```json
{
  "job_id": 123,
  "status": "pending",
  "reused": false,
  "created_at": 1711111111,
  "started_at": null,
  "finished_at": null
}
```

约束:
- 同一天同一用户仅允许一个 active job (`pending`/`running`)。
- 该天已有 `done` 任务时默认不重复运行（除非 `force=true`）。

### 1.2 查询任务状态

- Method: `GET`
- Path: `/api/prelabel/status/{job_id}`

- Response JSON:

```json
{
  "id": 123,
  "day_id": "20260320",
  "status": "running",
  "created_at": 1711111111,
  "started_at": 1711111120,
  "finished_at": null,
  "error_log": null,
  "pipeline_version": "mvp-mock-v1"
}
```

### 1.3 获取结果

- Method: `GET`
- Path: `/api/prelabel/results?day_id=YYYYMMDD[&job_id=123]`

- Response JSON:

```json
{
  "job": {
    "id": 123,
    "day_id": "20260320",
    "status": "done",
    "created_at": 1711111111,
    "started_at": 1711111120,
    "finished_at": 1711111220,
    "error_log": null,
    "pipeline_version": "mvp-mock-v1"
  },
  "results": [
    {
      "id": 1,
      "job_id": 123,
      "audio_id": 456,
      "minute_ts": 1711110000,
      "task_type": "asr",
      "content": {"text": "..."},
      "created_at": 1711111200
    }
  ]
}
```

### 1.4 失败分钟重跑

- Method: `POST`
- Path: `/api/prelabel/rerun-failed`
- Request JSON:

```json
{
  "day_id": "YYYYMMDD"
}
```

- Response JSON:

```json
{
  "job_id": 124,
  "status": "pending",
  "reused": false,
  "mode": "failed_only",
  "created_at": 1711112111,
  "started_at": null,
  "finished_at": null
}
```

约束:
- 仅重跑该日 `audio_data.pre_label_status=failed` 的片段。
- 若无失败片段，返回 409。

## 2. prelabel-service API（主站调用）

### 2.1 触发异步任务

- Method: `POST`
- Path: `/prelabel/run`
- Request JSON:

```json
{
  "job_id": 123,
  "day_id": "20260320",
  "user_id": "nuna_user"
}
```

- Response JSON:

```json
{
  "accepted": true,
  "job_id": 123,
  "status": "pending",
  "reused": false
}
```

说明:
- 服务内必须异步执行，HTTP 请求不能阻塞整个 pipeline。
- mock 阶段可使用线程/队列，正式阶段可替换为 worker。

### 2.2 查询状态（调试）

- Method: `GET`
- Path: `/prelabel/status/{job_id}`

### 2.3 重跑失败分钟

- Method: `POST`
- Path: `/prelabel/rerun_failed`
- Request JSON:

```json
{
  "job_id": 124,
  "day_id": "20260320",
  "user_id": "nuna_user"
}
```

- Response JSON:

```json
{
  "accepted": true,
  "job_id": 124,
  "status": "pending",
  "reused": false
}
```

## 3. 数据表约定

### 3.1 `prelabel_jobs`

最小字段:
- `id`, `userId`, `day_id`, `status`
- `created_at`, `started_at`, `finished_at`
- `error_log`, `pipeline_version`

### 3.2 `prelabel_results`

最小字段:
- `id`, `job_id`, `userId`, `day_id`
- `audio_id`, `minute_ts`
- `task_type`, `content_json`, `created_at`

说明:
- `content_json` 用于兼容多任务输出结构，后续不破坏 schema 即可扩展。
- 正式标注表与预标注表严格隔离。

## 4. 后续接真实 pipeline 的建议

1. 保留 `task_type + content_json`，仅迭代 JSON schema。
2. 通过 `pipeline_version` 做结果可追溯。
3. 在主站增加“强制重跑”开关（调用 `force=true`）。
4. 引入任务队列后，保持 `/prelabel/run` 入参和返回不变，避免前端与主站改动。

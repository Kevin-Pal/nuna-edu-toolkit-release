【项目背景与硬约束】
- 用户音频来自 Nuna 服务器，同步到本地后已按 1 分钟切片：每个文件=一个 segment。
- segment 是标注的最小单位：
  - Block（块标注）=连续多个 segment 的区间（整数个，必须连续）。
  - Point（点标注）=Block 内连续 segment 区间，最小 1 个 segment。
- 不做 VAD；块/点选定的 segment 区间天然定义范围。
- 不使用 remote_key；前端不呈现任何 remote_key 概念。
- 同步由后端在用户进入 /tasks 时触发，前端只展示同步状态（running/failed/success）和上次同步时间。
- 标注字段必须结构化输入，不能只让用户填一个自由文本：
  - Block：scene_adj, scene_noun, scene_note(optional), be_adv, be_verb, be_note(optional), emo_valence(low/mid/high), emo_arousal(low/mid/high/very_high)
  - Point：pe_type(env_fluctuation/personal_action)；若 env_fluctuation 则 env_subject+env_predicate 必填；若 personal_action 则 act_adv+act_verb 必填；pe_note(optional)；emo_valence/emo_arousal 同上
- 删除策略采用“策略A（推荐）”：若用户选择删除的 segment 被任何 block/point 覆盖，则前端必须阻止提交并提示用户先删除/调整对应标注。

【技术实现偏好】
- 前端尽量简单：优先模板渲染 + 少量 JS（或轻量框架也可，但必须易维护）。
- UI 框架可选 Bootstrap 或 Tailwind（二选一），请给出清晰一致的样式规范。
- 音频播放使用原生 <audio>，支持播放/暂停/拖动进度条（seek）。
- 页面要支持在 2C2G 服务器上流畅使用：避免一次性渲染过多 DOM（需要分页/折叠/虚拟列表策略其一）。

【必须交付的内容】
1) 信息架构（IA）与页面清单：至少包含
   - /auth/login
   - /auth/register
   - /auth/reset
   - /tasks（按天总览 + 同步状态）
   - /tasks/{date}（当天 segment 列表 + 创建 block）
   - /blocks/{block_id}（block 详情 + 创建/管理 point）
2) 每个页面的 UI 版式描述（布局区域、信息层级、关键组件）。
3) 关键交互的状态机/流程图式文字描述（必须覆盖）：
   - segment 列表的连续区间选择（start/end 锚点 + shift 选择 + 取消选择 + 折叠分组下的连续性定义）
   - 创建 Block 的流程（选择区间 -> 打开表单 -> 校验 -> 提交 -> 刷新 UI）
   - 在 block 内创建 Point（最少 1 个 segment）流程
   - 删除 segment 的流程：选择 -> 预校验是否被标注覆盖 -> 弹二次确认 -> 成功/失败反馈
   - 同步状态展示：进入 /tasks 时展示“同步中”与轮询/刷新策略（不要求 websocket）
4) 组件划分与复用建议：
   - SegmentList（支持分组折叠、范围选择、多选、分页）
   - AudioPlayerRow（单条 segment 的播放器 + ASR 展示）
   - BlockCreateModal（block 表单）
   - PointCreateModal（point 表单，含 pe_type 切换与字段互斥校验）
   - BlockSummaryList（当日 block 列表）
   - Toast/Alert（成功/错误提示）
5) 表单校验规则（逐字段）：必填、互斥、枚举值、长度上限、错误提示文案（中文）。
6) 接口调用约定（前端如何与后端交互），至少列出：
   - GET /tasks
   - GET /tasks/{date}
   - POST /blocks
   - GET /blocks/{block_id}
   - POST /points
   - POST /audio/delete
   - GET /audio/{audio_id}/stream（audio src 用法）
   说明每个接口需要的参数、前端何时调用、成功失败如何反馈。
7) 可用性与错误处理：
   - 空状态（无数据/同步中/同步失败）
   - ASR 仍在 queued/running 时的显示
   - 网络错误与重试按钮
8) 简洁的视觉规范：
   - 字体层级、间距、按钮样式、表格/列表行高
   - 标注状态颜色/标签（unlabeled/partially_labeled/labeled）建议（不用精确颜色值，但要有一致的语义）

【输出格式要求】
- 用 Markdown 输出。
- 先给“整体设计摘要”（不超过 15 行），再按页面逐一展开。
- 交互描述要足够精确，让工程师可以直接照着实现。
- 只输出前端设计与前端交互/接口约定，不要输出后端代码。
你是一个资深全栈前端工程师兼产品设计师。请为项目 Audio_Collection_Nuna 产出“前端实现与UI设计方案”，并给出可直接落地的页面结构、组件划分、状态管理、交互细节与接口调用约定。

【项目背景与硬约束】
- 用户音频来自 Nuna 服务器，同步到本地后已按 1 分钟切片：每个文件=一个 segment。
- segment 是标注的最小单位：
  - Block（块标注）=连续多个 segment 的区间（整数个，必须连续）。
  - Point（点标注）=Block 内连续 segment 区间，最小 1 个 segment。
- 不做 VAD；块/点选定的 segment 区间天然定义范围。
- 不使用 remote_key；前端不呈现任何 remote_key 概念。
- 同步由后端在用户进入 /tasks 时触发，前端只展示同步状态（running/failed/success）和上次同步时间。
- 标注字段必须结构化输入，不能只让用户填一个自由文本：
  - Block：scene_adj, scene_noun, scene_note(optional), be_adv, be_verb, be_note(optional), emo_valence(low/mid/high), emo_arousal(low/mid/high/very_high)
  - Point：pe_type(env_fluctuation/personal_action)；若 env_fluctuation 则 env_subject+env_predicate 必填；若 personal_action 则 act_adv+act_verb 必填；pe_note(optional)；emo_valence/emo_arousal 同上
- 删除策略采用“策略A（推荐）”：若用户选择删除的 segment 被任何 block/point 覆盖，则前端必须阻止提交并提示用户先删除/调整对应标注。

【技术实现偏好】
- 前端尽量简单：优先模板渲染 + 少量 JS（或轻量框架也可，但必须易维护）。
- UI 框架可选 Bootstrap 或 Tailwind（二选一），请给出清晰一致的样式规范。
- 音频播放使用原生 <audio>，支持播放/暂停/拖动进度条（seek）。
- 页面要支持在 2C2G 服务器上流畅使用：避免一次性渲染过多 DOM（需要分页/折叠/虚拟列表策略其一）。

【必须交付的内容】
1) 信息架构（IA）与页面清单：至少包含
   - /auth/login
   - /auth/register
   - /auth/reset
   - /tasks（按天总览 + 同步状态）
   - /tasks/{date}（当天 segment 列表 + 创建 block）
   - /blocks/{block_id}（block 详情 + 创建/管理 point）
2) 每个页面的 UI 版式描述（布局区域、信息层级、关键组件）。
3) 关键交互的状态机/流程图式文字描述（必须覆盖）：
   - segment 列表的连续区间选择（start/end 锚点 + shift 选择 + 取消选择 + 折叠分组下的连续性定义）
   - 创建 Block 的流程（选择区间 -> 打开表单 -> 校验 -> 提交 -> 刷新 UI）
   - 在 block 内创建 Point（最少 1 个 segment）流程
   - 删除 segment 的流程：选择 -> 预校验是否被标注覆盖 -> 弹二次确认 -> 成功/失败反馈
   - 同步状态展示：进入 /tasks 时展示“同步中”与轮询/刷新策略（不要求 websocket）
4) 组件划分与复用建议：
   - SegmentList（支持分组折叠、范围选择、多选、分页）
   - AudioPlayerRow（单条 segment 的播放器 + ASR 展示）
   - BlockCreateModal（block 表单）
   - PointCreateModal（point 表单，含 pe_type 切换与字段互斥校验）
   - BlockSummaryList（当日 block 列表）
   - Toast/Alert（成功/错误提示）
5) 表单校验规则（逐字段）：必填、互斥、枚举值、长度上限、错误提示文案（中文）。
6) 接口调用约定（前端如何与后端交互），至少列出：
   - GET /tasks
   - GET /tasks/{date}
   - POST /blocks
   - GET /blocks/{block_id}
   - POST /points
   - POST /audio/delete
   - GET /audio/{audio_id}/stream（audio src 用法）
   说明每个接口需要的参数、前端何时调用、成功失败如何反馈。
7) 可用性与错误处理：
   - 空状态（无数据/同步中/同步失败）
   - ASR 仍在 queued/running 时的显示
   - 网络错误与重试按钮
8) 简洁的视觉规范：
   - 字体层级、间距、按钮样式、表格/列表行高
   - 标注状态颜色/标签（unlabeled/partially_labeled/labeled）建议（不用精确颜色值，但要有一致的语义）
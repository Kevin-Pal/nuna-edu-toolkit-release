import json
from typing import Any

from fastapi import Request
from starlette.responses import Response


DEFAULT_LANG = "zh-CN"
SUPPORTED_LANGS = {"zh-CN", "en"}


MESSAGES = {
    "brand": {"zh-CN": "Nuna Audio Lab", "en": "Nuna Audio Lab"},
    "nav.tasks": {"zh-CN": "任务列表", "en": "Tasks"},
    "nav.login": {"zh-CN": "登录", "en": "Login"},
    "nav.register": {"zh-CN": "注册", "en": "Register"},
    "nav.logout": {"zh-CN": "退出登录", "en": "Log Out"},
    "lang.label": {"zh-CN": "Language", "en": "Language"},
    "lang.zh": {"zh-CN": "简体中文", "en": "简体中文"},
    "lang.en": {"zh-CN": "English", "en": "English"},
    "auth.login.title": {"zh-CN": "登录", "en": "Login"},
    "auth.login.user": {"zh-CN": "账号 (UserId)", "en": "Account (UserId)"},
    "auth.login.password": {"zh-CN": "密码", "en": "Password"},
    "auth.login.submit": {"zh-CN": "登录", "en": "Login"},
    "auth.login.no_account": {"zh-CN": "没有账号？", "en": "No account?"},
    "auth.login.register_now": {"zh-CN": "立即注册", "en": "Register now"},
    "auth.register.title": {"zh-CN": "注册", "en": "Register"},
    "auth.register.user": {"zh-CN": "账号 (UserId)", "en": "Account (UserId)"},
    "auth.register.user_hint": {
        "zh-CN": "请使用与手机端app一致的UserId",
        "en": "Use the same UserId as in your mobile app",
    },
    "auth.register.email": {"zh-CN": "电子邮箱", "en": "Email"},
    "auth.register.password": {"zh-CN": "密码", "en": "Password"},
    "auth.register.confirm_password": {"zh-CN": "确认密码", "en": "Confirm password"},
    "auth.register.submit": {"zh-CN": "注册", "en": "Register"},
    "auth.register.have_account": {"zh-CN": "已有账号？", "en": "Already have an account?"},
    "auth.register.direct_login": {"zh-CN": "直接登录", "en": "Log in"},
    "tasks.title": {"zh-CN": "任务列表", "en": "Tasks"},
    "tasks.last_sync": {"zh-CN": "上次接收音频", "en": "Last audio receive"},
    "tasks.never": {"zh-CN": "从未", "en": "Never"},
    "tasks.sync_failed": {"zh-CN": "接收失败", "en": "Receive failed"},
    "tasks.sync_ok": {"zh-CN": "接收正常", "en": "Receive normal"},
    "tasks.server_hint": {
        "zh-CN": "请在 Nuna 手机 App 的 Configure Audio Server 中配置开发者提供的 Customer Server 地址。",
        "en": "Please configure the Customer Server in Nuna mobile app Configure Audio Server.",
    },
    "tasks.timezone_note": {
        "zh-CN": "接收音频按 UTC 日期目录存放；页面时间按浏览器时区显示。",
        "en": "Received audio is stored by UTC date folders; page time uses browser timezone.",
    },
    "tasks.total_segments": {"zh-CN": "共 {count} 个片段 ({minutes} 分钟)", "en": "{count} segments total ({minutes} min)"},
    "tasks.labeled": {"zh-CN": "已标注", "en": "Labeled"},
    "tasks.coverage": {"zh-CN": "覆盖率", "en": "Coverage"},
    "tasks.prelabel_status": {"zh-CN": "预标注状态", "en": "Prelabel status"},
    "status.done": {"zh-CN": "已完成", "en": "Done"},
    "status.running": {"zh-CN": "运行中", "en": "Running"},
    "status.pending": {"zh-CN": "排队中", "en": "Pending"},
    "status.failed": {"zh-CN": "失败", "en": "Failed"},
    "status.not_run": {"zh-CN": "未运行", "en": "Not run"},
    "tasks.enter_workspace": {"zh-CN": "进入工作台", "en": "Open workspace"},
    "tasks.no_data": {"zh-CN": "暂无数据", "en": "No data"},
    "tasks.no_data_hint": {
        "zh-CN": "请先在手机端完成音频上传，服务器收到后会自动出现在这里",
        "en": "Please upload audio in the mobile app first. It will appear here automatically after server receive.",
    },
    "prelabel.title": {"zh-CN": "预标注结果", "en": "Prelabel Results"},
    "prelabel.back_workspace": {"zh-CN": "返回工作台", "en": "Back to Workspace"},
    "prelabel.console": {"zh-CN": "预标注控制台", "en": "Prelabel Console"},
    "prelabel.intro": {
        "zh-CN": "日期 {day_id} · 开发测试阶段支持重复预标注，并可查看历史任务结果进行比对",
        "en": "Date {day_id} · During development, repeated prelabel runs are supported and historical jobs can be compared.",
    },
    "prelabel.status": {"zh-CN": "状态", "en": "Status"},
    "prelabel.start_time": {"zh-CN": "开始时间", "en": "Start Time"},
    "prelabel.finish_time": {"zh-CN": "结束时间", "en": "Finish Time"},
    "prelabel.run_beta": {"zh-CN": "预标注（Beta）", "en": "Prelabel (Beta)"},
    "prelabel.rerun_failed": {"zh-CN": "重跑失败分钟", "en": "Rerun Failed Minutes"},
    "prelabel.refresh": {"zh-CN": "刷新状态", "en": "Refresh Status"},
    "prelabel.allow_repeat": {"zh-CN": "允许重复预标注", "en": "Repeat prelabel is allowed"},
    "prelabel.deny_repeat": {"zh-CN": "禁止重复预标注", "en": "Repeat prelabel is disabled"},
    "prelabel.switch_latest": {"zh-CN": "切换到最新任务 #{id}", "en": "Switch to latest job #{id}"},
    "prelabel.history": {"zh-CN": "历史预标注任务", "en": "Prelabel Job History"},
    "prelabel.history_hint": {"zh-CN": "点击 Job 可切换查看历史结果", "en": "Click Job to view historical results"},
    "prelabel.created_time": {"zh-CN": "创建时间", "en": "Created Time"},
    "prelabel.finished_time": {"zh-CN": "完成时间", "en": "Finished Time"},
    "prelabel.action": {"zh-CN": "操作", "en": "Action"},
    "prelabel.view": {"zh-CN": "查看", "en": "View"},
    "prelabel.no_history": {"zh-CN": "暂无历史任务。", "en": "No historical jobs."},
    "prelabel.asr_tab": {"zh-CN": "ASR 结果", "en": "ASR Results"},
    "prelabel.sed_tab": {"zh-CN": "ASC/SED/HAR（预留接口）", "en": "ASC/SED/HAR (Reserved)"},
    "prelabel.select_all": {"zh-CN": "全选", "en": "Select All"},
    "prelabel.select_none": {"zh-CN": "全不选", "en": "Select None"},
    "prelabel.export_selected": {"zh-CN": "导出选中音频 + CSV", "en": "Export Selected Audio + CSV"},
    "prelabel.selected": {"zh-CN": "已选择", "en": "Selected"},
    "prelabel.low_speech_thres": {"zh-CN": "低语音自动折叠阈值", "en": "Low-speech auto-fold threshold"},
    "prelabel.low_speech_folded": {"zh-CN": "已折叠 {count} 条", "en": "{count} folded"},
    "prelabel.expand_all_low": {"zh-CN": "展开所有低语音结果", "en": "Expand all low-speech results"},
    "prelabel.collapse_all_low": {"zh-CN": "折叠所有低语音结果", "en": "Collapse all low-speech results"},
    "prelabel.segment": {"zh-CN": "片段", "en": "Segment"},
    "prelabel.audio_time": {"zh-CN": "音频时间", "en": "Audio Time"},
    "prelabel.duration": {"zh-CN": "时长", "en": "Duration"},
    "prelabel.low_speech_item": {"zh-CN": "低语音内容（{units}/{thres} {unit}），默认折叠。", "en": "Low-speech content ({units}/{thres} {unit}), collapsed by default."},
    "prelabel.unit_word": {"zh-CN": "词", "en": "words"},
    "prelabel.unit_char": {"zh-CN": "字", "en": "chars"},
    "prelabel.expand_one": {"zh-CN": "展开本条", "en": "Expand this item"},
    "prelabel.no_asr": {"zh-CN": "暂无 ASR 预标注结果。", "en": "No ASR prelabel results."},
    "prelabel.time": {"zh-CN": "时间", "en": "Time"},
    "prelabel.sed_not_enabled": {"zh-CN": "当前尚未启用 ASC/SED/HAR 实际产出，但接口与展示位已预留。", "en": "ASC/SED/HAR output is not enabled yet, while API and UI placeholders are reserved."},
    "prelabel.query_failed": {"zh-CN": "状态查询失败", "en": "Failed to query status"},
    "prelabel.triggering": {"zh-CN": "触发中", "en": "Triggering"},
    "prelabel.trigger_failed": {"zh-CN": "预标注任务触发失败", "en": "Failed to trigger prelabel job"},
    "prelabel.rerun_trigger_failed": {"zh-CN": "失败分钟重跑触发失败", "en": "Failed to trigger rerun for failed minutes"},
    "prelabel.refresh_failed": {"zh-CN": "状态刷新失败", "en": "Failed to refresh status"},
    "prelabel.choose_audio": {"zh-CN": "请先选择要导出的音频", "en": "Please select audio to export first"},
    "prelabel.exporting": {"zh-CN": "导出中", "en": "Exporting"},
    "prelabel.export_failed": {"zh-CN": "导出失败", "en": "Export failed"},
    "flash.manual_sync_disabled": {
        "zh-CN": "S3 手动同步已下线。请在 Nuna 手机 App 的 Configure Audio Server 中配置 Customer Server：{url}",
        "en": "S3 manual sync is deprecated. Please configure Customer Server in Nuna mobile app Configure Audio Server: {url}",
    },
    "detail.back": {"zh-CN": "返回", "en": "Back"},
    "detail.segment": {"zh-CN": "片段", "en": "segments"},
    "detail.all": {"zh-CN": "全部", "en": "All"},
    "detail.unlabeled_only": {"zh-CN": "仅未标", "en": "Unlabeled only"},
    "detail.expand_all": {"zh-CN": "全部展开", "en": "Expand all"},
    "detail.collapse_all": {"zh-CN": "全部折叠", "en": "Collapse all"},
    "detail.tip": {
        "zh-CN": "提示：点击已标注的 Block 可进入块详情页，进一步进行点状（Point）标注。",
        "en": "Tip: Click labeled Block to enter block detail and create Point annotations.",
    },
    "detail.minutes": {"zh-CN": "分钟", "en": "min"},
    "detail.select_hour": {"zh-CN": "全选本小时", "en": "Select this hour"},
    "detail.select_quarter": {"zh-CN": "全选本 15 分钟", "en": "Select this 15 min"},
    "detail.expand_asr": {"zh-CN": "展开 ASR 文本", "en": "Expand ASR text"},
    "detail.collapse_asr": {"zh-CN": "收起 ASR 文本", "en": "Collapse ASR text"},
    "detail.no_asr": {"zh-CN": "暂无预标注 ASR 结果", "en": "No prelabel ASR result"},
    "detail.selected_count": {"zh-CN": "个片段被选中", "en": "segments selected"},
    "detail.cancel": {"zh-CN": "取消", "en": "Cancel"},
    "detail.create_block": {"zh-CN": "创建 Block", "en": "Create Block"},
    "detail.delete_audio": {"zh-CN": "删除选中音频", "en": "Delete selected audio"},
    "detail.prelabel_beta": {"zh-CN": "预标注（Beta）", "en": "Prelabel (Beta)"},
    "detail.choose_audio_first": {"zh-CN": "请先选择要删除的音频", "en": "Please select audio to delete first"},
    "detail.next_day": {"zh-CN": "次日", "en": "Next day"},
    "detail.prev_day": {"zh-CN": "前日", "en": "Previous day"},
    "block.back_day": {"zh-CN": "返回当天", "en": "Back to day"},
    "block.range": {"zh-CN": "范围", "en": "Range"},
    "block.scene": {"zh-CN": "场景", "en": "Scene"},
    "block.event": {"zh-CN": "块事件", "en": "Block event"},
    "block.no_note": {"zh-CN": "无备注", "en": "No notes"},
    "block.points_created": {"zh-CN": "已创建的点状标注", "en": "Created point annotations"},
    "block.table.range": {"zh-CN": "范围 (片段ID)", "en": "Range (segment IDs)"},
    "block.table.type": {"zh-CN": "类型", "en": "Type"},
    "block.table.content": {"zh-CN": "内容", "en": "Content"},
    "block.table.emotion": {"zh-CN": "情绪", "en": "Emotion"},
    "block.type.env": {"zh-CN": "环境波动", "en": "Environment fluctuation"},
    "block.type.action": {"zh-CN": "个人行动", "en": "Personal action"},
    "block.no_point": {"zh-CN": "暂无点标注，选择片段创建一个吧。", "en": "No point annotations yet. Select segments to create one."},
    "block.create_point": {"zh-CN": "创建点标注", "en": "Create Point"},
    "modal.block.title": {"zh-CN": "创建块标注 (Block)", "en": "Create Block Annotation"},
    "modal.block.selected_zero": {"zh-CN": "已选择 0 分钟片段", "en": "Selected 0 min segments"},
    "modal.cancel": {"zh-CN": "取消", "en": "Cancel"},
    "modal.create": {"zh-CN": "创建标注", "en": "Create annotation"},
    "flash.login_failed": {"zh-CN": "账号或密码错误", "en": "Invalid account or password"},
    "flash.password_len": {"zh-CN": "密码长度需 8-72 个字符", "en": "Password length must be 8-72 characters"},
    "flash.password_mismatch": {"zh-CN": "两次密码输入不一致", "en": "Passwords do not match"},
    "flash.user_exists": {"zh-CN": "该账号已被注册", "en": "This account is already registered"},
    "flash.no_audio": {
        "zh-CN": "当前服务器未检测到该用户上传的有效音频数据。请先在 Nuna 手机 App - 我的 - Configure Audio Server 中将 Customer Server 设置为：{url}",
        "en": "No valid uploaded audio was found for this user on current server. Set Customer Server in Nuna app Configure Audio Server to: {url}",
    },
    "flash.register_success": {"zh-CN": "注册成功，请登录", "en": "Registration successful, please log in"},
    "flash.emotion_invalid": {"zh-CN": "情绪选择错误", "en": "Invalid emotion selection"},
    "flash.start_gt_end": {"zh-CN": "起始ID不能大于结束ID", "en": "Start ID cannot be greater than end ID"},
    "flash.segment_not_continuous": {"zh-CN": "选择的片段不连续或部分丢失", "en": "Selected segments are not continuous or missing"},
    "flash.segment_labeled": {"zh-CN": "片段 {id} 已经被标注，无法创建 Block", "en": "Segment {id} is already labeled. Cannot create Block"},
    "flash.block_created": {"zh-CN": "Block 创建成功，继续在该 Block 内添加点标注", "en": "Block created successfully. Continue creating Point annotations inside this Block"},
    "flash.block_not_found": {"zh-CN": "Block 不存在或无权限", "en": "Block not found or no permission"},
    "flash.point_range": {"zh-CN": "点标注范围必须落在已选 Block 内", "en": "Point range must be inside selected Block"},
    "flash.select_point_type": {"zh-CN": "请选择点状事件类型", "en": "Please select point event type"},
    "flash.env_need_subject_predicate": {"zh-CN": "环境波动需填写主语和谓语", "en": "Environment fluctuation requires subject and predicate"},
    "flash.act_need_adv_verb": {"zh-CN": "个人行动需填写副词和动词", "en": "Personal action requires adverb and verb"},
    "flash.point_created": {"zh-CN": "点标注创建成功", "en": "Point annotation created successfully"},
    "flash.no_segment_selected": {"zh-CN": "未选择片段", "en": "No segments selected"},
    "flash.segment_id_invalid": {"zh-CN": "片段ID格式错误", "en": "Invalid segment ID format"},
    "flash.invalid_or_no_permission_segment": {"zh-CN": "存在无效片段或无权限的片段", "en": "Invalid segments found or no permission"},
    "flash.segment_in_block": {"zh-CN": "片段 {seg_id} 已在 Block #{block_id} 中，无法删除，请先调整/删除该 Block", "en": "Segment {seg_id} is in Block #{block_id}. Delete or adjust the Block first"},
    "flash.segment_in_point": {"zh-CN": "片段 {seg_id} 已在 Point #{point_id} 中，无法删除，请先调整/删除相关标注", "en": "Segment {seg_id} is in Point #{point_id}. Delete or adjust related annotation first"},
    "flash.file_delete_failed": {"zh-CN": "删除文件失败：{reason}", "en": "Failed to delete file: {reason}"},
    "flash.delete_success": {"zh-CN": "删除成功", "en": "Deleted successfully"},
    "flash.invalid_day_id": {"zh-CN": "day_id 必须是 YYYYMMDD", "en": "day_id must be YYYYMMDD"},
    "flash.no_audio_for_day": {"zh-CN": "该日期没有音频数据", "en": "No audio data for this day"},
    "flash.prelabel_already_done": {"zh-CN": "该日期已完成预标注，默认不重复运行", "en": "Prelabel is already done for this day and rerun is disabled by default"},
    "flash.no_failed_segments": {"zh-CN": "该日期没有失败片段可重跑", "en": "No failed segments to rerun for this day"},
    "flash.job_not_found": {"zh-CN": "任务不存在", "en": "Job not found"},
    "flash.audio_path_illegal": {"zh-CN": "音频路径非法", "en": "Illegal audio path"},
    "flash.prelabel_service_unavailable": {"zh-CN": "预标注服务不可用，请稍后重试", "en": "Prelabel service unavailable, please retry later"},
    "flash.choose_one_audio": {"zh-CN": "请至少选择一个音频片段", "en": "Please select at least one audio segment"},
    "flash.audio_ids_invalid": {"zh-CN": "audio_ids 格式错误", "en": "Invalid audio_ids format"},
    "flash.job_id_invalid": {"zh-CN": "job_id 格式错误", "en": "Invalid job_id format"},
    "flash.export_job_not_found": {"zh-CN": "未找到可导出的预标注任务", "en": "No exportable prelabel job found"},
    "flash.invalid_audio_or_permission": {"zh-CN": "存在无效音频片段或无权限访问", "en": "Invalid audio segment exists or no permission"},
    "flash.audio_file_not_found": {"zh-CN": "音频文件不存在: audio_id={audio_id}", "en": "Audio file does not exist: audio_id={audio_id}"},
    "js.create_block": {"zh-CN": "创建 Block", "en": "Create Block"},
    "js.non_contiguous": {"zh-CN": "选择不连续 (无法创建)", "en": "Non-contiguous (cannot create)"},
    "js.selected_contiguous": {"zh-CN": "已选 {count} 个连续片段 ({time} 开始)", "en": "Selected {count} continuous segments (start at {time})"},
    "js.must_contiguous": {"zh-CN": "错误：选择的片段必须连续", "en": "Error: selected segments must be continuous"},
    "js.choose_point_segments": {"zh-CN": "请选择连续片段后创建点标注", "en": "Select continuous segments before creating point annotation"},
    "js.start_end_time": {"zh-CN": "起止时间", "en": "Time range"},
}


def normalize_lang(lang: str | None) -> str | None:
    raw = (lang or "").strip().lower()
    if not raw:
        return None
    if raw in {"en", "en-us", "en-gb"}:
        return "en"
    if raw in {"zh", "zh-cn", "zh-hans", "zh-hans-cn"}:
        return "zh-CN"
    return None


def resolve_lang(request: Request) -> str:
    q_raw = request.query_params.get("lang")
    q = normalize_lang(q_raw)
    if q:
        return q

    c = normalize_lang(request.cookies.get("lang"))
    if c:
        return c

    accept = request.headers.get("accept-language", "")
    for item in accept.split(","):
        lang = normalize_lang(item.split(";")[0])
        if lang:
            return lang

    return DEFAULT_LANG


def t(request: Request, key: str, **kwargs: Any) -> str:
    lang = resolve_lang(request)
    entry = MESSAGES.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def catalog_for(request: Request) -> str:
    lang = resolve_lang(request)
    data = {k: (v.get(lang) or v.get(DEFAULT_LANG) or k) for k, v in MESSAGES.items()}
    return json.dumps(data, ensure_ascii=False)


def set_lang_cookie(response: Response, lang: str) -> None:
    value = normalize_lang(lang)
    if not value:
        value = DEFAULT_LANG
    response.set_cookie("lang", value, max_age=31536000, path="/")

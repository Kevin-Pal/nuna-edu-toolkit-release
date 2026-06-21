from fastapi import FastAPI, File, UploadFile, HTTPException
import json
import os
from datetime import datetime
import uvicorn

app = FastAPI()

# === Server Config (可通过环境变量覆盖) ===
# 保存目录：默认写入到 /runtime（符合项目运行时数据规范）
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
# 监听地址与端口（仅用于 __main__ 运行；容器/进程管理另行指定亦可）
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "9000"))

os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/thingx/api/file/upload/audio")
async def upload_audio(
    file: UploadFile = File(...),
    metadata: UploadFile = File(...)  # ← 关键：改为 UploadFile！
):
    try:
        # 读取 metadata 文件内容（它是 text/plain 的 JSON 字符串）
        metadata_content = await metadata.read()
        metadata_str = metadata_content.decode('utf-8')
        meta = json.loads(metadata_str)

        # 验证字段
        required = ["userId", "name", "startTime", "endTime", "mac", "size"]
        for field in required:
            if field not in meta:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")

        # 保存音频文件
        save_path = os.path.join(UPLOAD_DIR, meta["name"])
        with open(save_path, "wb") as f:
            audio_content = await file.read()
            f.write(audio_content)

        print(f"[{datetime.now()}] Received from {meta['mac']}: {meta['name']}")

        return {"code": 200, "message": "success", "data": None}

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Metadata is not valid UTF-8 text")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Metadata is not valid JSON")
    except Exception as e:
        print("Server error:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "upload_dir": UPLOAD_DIR,
        "server_host": SERVER_HOST,
        "server_port": SERVER_PORT,
    }


if __name__ == "__main__":
    print("=== Audio Upload Server Starting ===")
    print(f"UPLOAD_DIR: {UPLOAD_DIR}")
    print(f"LISTEN: {SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
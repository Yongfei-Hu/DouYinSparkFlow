# 尝试从 .env 文件加载环境变量
import os
if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv(".env")

# [2026-08-20 诊断] RUN_TLS_DIAG=1 时先跑只读 TLS 指纹对比（runner 上不发送任何消息）
if os.getenv("RUN_TLS_DIAG") == "1":
    from diag_tls import run_diag

    run_diag()

from core.tasks import runTasks

runTasks()

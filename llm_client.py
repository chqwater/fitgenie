import os
from openai import OpenAI


def get_client() -> OpenAI:
    api_key = os.environ.get("HUNYUAN_API_KEY")

    if not api_key:
        raise EnvironmentError("未找到 HUNYUAN_API_KEY，请检查 .env 文件")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.hunyuan.cloud.tencent.com/v1",
    )
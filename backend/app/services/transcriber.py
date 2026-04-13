import io
import os
import tempfile
from openai import OpenAI
from ..config import settings

def transcribe_audio(file_content: bytes, filename: str) -> str:
    """
    音声ファイルをOpenAI Whisper APIで文字起こしします。
    """
    if not settings.openai_api_key:
        # APIキーがない場合は擬似的な戻り値（またはエラー）を返す
        return "【デモモード】音声解析にはOpenAI APIキーの設定が必要です。"

    client = OpenAI(api_key=settings.openai_api_key)

    # 一時ファイルとして保存（OpenAI SDKはファイルオブジェクトを要求するため）
    ext = os.path.splitext(filename)[1].lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ja"
            )
        return transcript.text
    finally:
        # 一時ファイルの削除
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

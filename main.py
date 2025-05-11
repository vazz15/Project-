import os
import openai
import torch
import soundfile as sf
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from TTS.api import TTS

# === КЛЮЧИ ===
openai.api_key = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Silero Voice Synth ===
tts = TTS(model_name="tts_models/ru/ru_v3", progress_bar=False, gpu=torch.cuda.is_available())

# === Хендлер сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.message.chat_id

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        await update.message.reply_text(f"Ошибка OpenAI: {e}")
        return

    try:
        audio_path = f"output_{user_id}.wav"
        tts.tts_to_file(text=reply, file_path=audio_path)

        ogg_path = f"output_{user_id}.ogg"
        os.system(f"ffmpeg -y -i {audio_path} -acodec libopus {ogg_path}")

        with open(ogg_path, "rb") as voice:
            await update.message.reply_voice(voice=voice)

        os.remove(audio_path)
        os.remove(ogg_path)
    except Exception as e:
        await update.message.reply_text(reply)
        await update.message.reply_text(f"(Озвучка не сработала: {e})")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

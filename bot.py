import asyncio
import logging
import os
import re
import tempfile

import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8828617929:AAG13pLHnIXrfFqdIwKayk-FtdK_j8m4hPo")

LINK_RE = re.compile(r"https?://\S+")


def extract_url(text: str) -> str | None:
    m = LINK_RE.search(text)
    return m.group(0) if m else None


def get_video_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info


def download_video(url: str, workdir: str) -> tuple[str, str]:
    """Returns (file_path, title)."""
    out_template = os.path.join(workdir, "%(title).80s.%(ext)s")
    ydl_opts = {
        "outtmpl": out_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "ffmpeg_location": r"C:\ffmpeg\bin",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info:
            info = info["entries"][0]
        title = info.get("title", "video")
        filepath = ydl.prepare_filename(info)
        # prepare_filename may not include merged ext; find actual file
        for f in os.listdir(workdir):
            if f.endswith((".mp4", ".mkv", ".webm", ".mov")):
                return os.path.join(workdir, f), title
        return filepath, title


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! YouTube yoki Instagram linkini yuboring — video yuklab beraman.\n\n"
        "Qo'llab-quvvatlanadigan saytlar: YouTube, Instagram, TikTok, Twitter/X va boshqalar."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    url = extract_url(msg.text or "")
    if not url:
        await msg.reply_text("Iltimos, to'g'ri link yuboring (http:// yoki https://).")
        return

    status_msg = await msg.reply_text("⏳ Video tayyorlanmoqda...")

    try:
        info = await asyncio.to_thread(get_video_info, url)
        title = info.get("title", "video")
        duration = info.get("duration")
        uploader = info.get("uploader") or info.get("channel") or ""

        caption = f"📹 {title}"
        if uploader:
            caption += f"\n👤 {uploader}"
        if duration:
            caption += f"\n⏱ {duration // 60}:{duration % 60:02d}"

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath, _ = await asyncio.to_thread(download_video, url, tmpdir)
            file_size = os.path.getsize(filepath)

            # Telegram limit: 50 MB for bots via sendVideo (up to 2GB with local Bot API)
            if file_size > 50 * 1024 * 1024:
                await status_msg.edit_text(
                    f"⚠️ Video juda katta ({file_size / 1024 / 1024:.0f} MB). "
                    "Telegram bot 50 MB gacha yubora oladi."
                )
                return

            with open(filepath, "rb") as f:
                await msg.reply_video(
                    video=f,
                    caption=caption[:1024],
                    supports_streaming=True,
                )
            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        logger.warning("DownloadError: %s", e)
        await status_msg.edit_text(
            "❌ Video yuklab bo'lmadi. Sabab: maxfiy video, cheklangan kontent yoki noto'g'ri link."
        )
    except Exception as e:
        logger.exception("Unexpected error")
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error: %s", update, context.error)


def main():
    if "BOT_TOKENINGIZNI" in BOT_TOKEN:
        raise SystemExit("Iltimos, bot.py ichida BOT_TOKEN ni o'zgartiring yoki BOT_TOKEN muhit o'zgaruvchisida bering.")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(60)
        .read_timeout(120)
        .write_timeout(600)
        .pool_timeout(60)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_error_handler(error_handler)

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

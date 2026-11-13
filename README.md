# Video Downloader Bot

Telegram bot — YouTube, Instagram va boshqa saytlardagi link asosida video yuklab beradi.

## O'rnatish

```powershell
pip install -r requirements.txt
```

## Ishga tushirish

1. [@BotFather](https://t.me/BotFather) orqali yangi bot yarating va token oling.
2. `bot.py` ichidagi `BOT_TOKEN` ni o'zgartiring yoki muhit o'zgaruvchisi sifatida bering:

```powershell
$env:BOT_TOKEN = "123456:ABC..."
python bot.py
```

## Ishlatish

Botga istalgan video linkini yuboring — u videoni yuklab qaytaradi.

## Eslatmalar

- Telegram bot orqali **50 MB gacha** fayl yuborish mumkin (standart Bot API).
- Instagram uchun ba'zan `ffmpeg` kerak bo'ladi: `winget install ffmpeg` yoki https://ffmpeg.org dan o'rnating.
- `yt-dlp` ni yangilab turing: `pip install -U yt-dlp`

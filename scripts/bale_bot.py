import logging
import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN       = "1012686174:Wolej1gMFghVAan33PYQxD2HW_qUR8W8LMY"
BASE_URL    = "https://tapi.bale.ai/bot"
TOOLBOX_URL = "https://mahdiyar.info"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Deep-link URL builder ─────────────────────────────────────────────────────
# Uses ?tool= query param — Bale WebView strips URL #fragments but keeps params
def tool_url(tool_id: str) -> str:
    return f"{TOOLBOX_URL}?tool={tool_id}"


# ── Category definitions (label shown in keyboard → list of (name, tool_id)) ──
CATEGORIES = {
    "🧮 ریاضی": [
        ("🧮 ماشین‌حساب",      "calc"),
        ("∫ حسابان",          "calculus"),
        ("📐 حل معادله",      "linsolve"),
        ("⚖️ شاخص BMI",       "bmi"),
        ("📊 میانگین و آمار", "avg"),
        ("% محاسبه درصد",     "pct"),
        ("📐 ماتریس",         "matrix"),
        ("✖️ جدول ضرب",       "multable"),
        ("🏦 محاسبه وام",     "loan"),
        ("💰 سود سپرده",      "deposit"),
        ("🏠 رهن و اجاره",    "rentcalc"),
        ("🏷️ مالیات و تخفیف", "taxdisc"),
        ("🧾 تقسیم صورت‌حساب", "tip"),
    ],
    "📅 زمان": [
        ("⏱️ کرونومتر",       "stopwatch"),
        ("⏳ تایمر",           "timer"),
        ("🍅 پومودورو",        "pomodoro"),
        ("🔢 شمارنده",        "counter"),
        ("📅 تقویم خورشیدی",  "jcal"),
        ("🗓️ مبدل تاریخ",    "dateconv"),
        ("🎂 محاسبه سن",      "age"),
        ("🌐 ساعت جهانی",    "timezone"),
    ],
    "📐 علوم": [
        ("📏 تبدیل واحد",     "unitconv"),
        ("📐 هندسه",          "geometry"),
        ("⚗️ جدول تناوبی",   "periodic"),
        ("🔧 مقاومت رنگی",   "resistor"),
        ("🌐 Subnet",         "subnet"),
    ],
    "✏️ متن": [
        ("✏️ ابزار متن",      "text"),
        ("📊 آنالیز متن",     "charcount"),
        ("␣ حذف فاصله",     "whitespace"),
        ("↔️ تک‌خطی کردن",      "oneline"),
        ("📄 لورم ایپسوم",    "lorem"),
        ("🖊️ Markdown",      "markdown"),
        ("🔀 مقایسه متن",     "diff"),
        ("� ساخت Slug",      "slugify"),
        ("📡 کد مورس",     "morse"),
        ("Ⅰ اعداد رومی",      "roman"),
        ("🔢 تبدیل اعداد",    "numconvert"),
        ("🔤 رفع خرابی متن",  "textfix"),
        ("📝 یادداشت",        "notes"),
        ("😀 ایموجی",         "emojis"),
        (":‑) اِموتیکون",      "emotcn"),
        ("📖 فرهنگ واژه",     "pasban"),
    ],
    "💻 توسعه": [
        ("📋 JSON",           "json"),
        ("🏷️ XML",            "xml"),
        ("🔤 HTML Escaper",   "htmlesc"),
        ("🔏 هش",             "hash"),
        ("🔐 رمزنگاری",       "crypto"),
        ("🔑 JWT Parser",     "jwt"),
        ("📐 PX ↔ REM",       "pxrem"),
        ("🔍 Regex",          "regex"),
        ("🕐 Cron Parser",    "cron"),
        ("🌐 تجزیه URL",      "urlparse"),
        ("🔣 تبدیل مبنا",     "numbase"),
        ("🔤 جدول ASCII",     "asciitbl"),
        ("🔡 ابزار کدگذاری",  "enctools"),
        ("📊 نمودار داده",    "chart"),
        ("🗄️ مولد JSON",      "fakejson"),
        ("💬 عدد به حروف",    "numwords"),
        ("🔍 متا تگ SEO",     "seotools"),
        ("⚙️ .htaccess",      "htaccess"),
        ("🔐 RSA/ECC",        "keypair"),
    ],
    "⚡ مولدها": [
        ("🔐 رمز عبور",       "pass"),
        ("🪪 UUID",           "uuid"),
        ("🎲 عدد تصادفی",     "randnum"),
        ("✨ زیباساز متن",    "textbeauty"),
        ("🧾 فاکتور رسمی",    "invoice"),
        ("🧩 حل روبیک",       "rubik"),
        ("🌐 IP تصادفی",      "randip"),
        ("🎨 رنگ تصادفی",     "randcolor"),
        ("👤 داده ساختگی",    "fake"),
        ("💳 کارت اعتباری",   "credit"),
        ("🖼️ آواتار",         "avatar"),
        ("🗃️ تصویر جایگزین",  "placeholder"),
        ("📱 کد QR",          "qr"),
        ("📷 خواندن QR",      "qrread"),
        ("📊 بارکد",          "barcode"),
    ],
    "🎨 طراحی": [
        ("🖌️ تبدیل رنگ",     "colorpicker"),
        ("♿ کنتراست WCAG",    "wcag"),
        ("👁 کوررنگی",        "colorblind"),
        ("🌈 گرادیان CSS",    "gradient"),
        ("🌑 سایه CSS",       "shadow"),
        ("⬛ گوشه‌گرد CSS",    "borderrad"),
        ("📐 نسبت ابعاد",     "aspect"),
        ("φ نسبت طلایی",     "goldenratio"),
        ("🖼️ SVG Viewer",    "svgviewer"),
        ("⚏ Grid/Flexbox",   "gridbuilder"),
        ("🎨 پالت رنگ",       "imgpalette"),
    ],
    "📁 فایل": [
        ("�️ ابزار تصویر",    "imgtool"),
        ("✂️ حذف پس‌زمینه",   "bgremove"),
        ("🛠️ ابزار PDF",      "pdftool"),
        ("🗂 تقسیم فایل",    "filesplit"),
        ("💧 واترمارک",       "watermark"),
        ("🔄 تصویر ← Base64",  "img2b64"),
        ("↔️ CSV ↔ JSON",    "csvjson"),
    ],
    "🛠️ ایران": [
        ("🚨 شماره ضروری",   "emergency"),
        ("📞 کد شهرها",      "citycodes"),
        ("🚗 جرایم رانندگی", "trafficfines"),
        ("🚇 نقشه مترو",     "metromap"),
        ("💻 اطلاعات دستگاه","device"),
        ("ℹ️ User Agent",     "ua"),
    ],
    "🎮 بازی": [
        ("🕹️ بازی‌های کوچک", "minigames"),
        ("☁️ ابر کلمات",      "wordcloud"),
        ("📖 دیوان شعر",      "diwan"),
    ],
    "🧭 تخصصی": [
        ("🧭 قطب‌نما",        "compass"),
        ("🗂️ بوم کسب‌وکار", "bmc"),
        ("⬜ ماتریس آیزنهاور","eisenhower"),
        ("� ماتریس تصمیم",   "decmatrix"),
        ("📚 استناد دانشگاهی","citation"),
        ("🎓 محاسبه نمره",    "langscores"),
        ("🔊 ابزار صوتی",     "audiotools"),
        ("🗣️ متن به گفتار",   "tts"),
    ],
    "🌐 آنلاین": [
        ("🌤️ آب‌وهوا",       "weather"),
        ("🌍 ترجمه",          "translate"),
        ("💹 قیمت و نرخ",     "currency"),
    ],
}

# Row order for the persistent keyboard
CATEGORY_KEYS = [
    ["🧮 ریاضی",  "📅 زمان",   "📐 علوم"],
    ["✏️ متن",    "💻 توسعه",  "⚡ مولدها"],
    ["🎨 طراحی",  "📁 فایل",   "🛠️ ایران"],
    ["🎮 بازی",   "🧭 تخصصی",  "🌐 آنلاین"],
    ["🧰 همه ابزارها"],
]

def main_keyboard():
    """Persistent bottom keyboard with category buttons."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=btn) for btn in row] for row in CATEGORY_KEYS],
        resize_keyboard=True,
        is_persistent=True,
    )

def category_inline(cat_name: str):
    """Inline keyboard for a specific category's tools."""
    tools = CATEGORIES.get(cat_name, [])
    # Two tools per row
    rows = []
    for i in range(0, len(tools), 2):
        pair = tools[i:i+2]
        rows.append([
            InlineKeyboardButton(name, web_app=WebAppInfo(url=tool_url(tid)))
            for name, tid in pair
        ])
    return InlineKeyboardMarkup(rows)


# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋 به *جعبه‌ابزار ایرانی* خوش آمدید.\n"
        "بیش از ۱۲۰ ابزار کاربردی، سبک و ساده.\n\n"
        "یک دسته‌بندی را از منوی پایین انتخاب کنید، یا مستقیم جعبه‌ابزار را باز کنید:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "🧰 باز کردن جعبه‌ابزار:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🧰 باز کردن جعبه‌ابزار", web_app=WebAppInfo(url=TOOLBOX_URL))
        ]])
    )


# ── /help ─────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *راهنما:*\n\n"
        "از منوی پایین صفحه یک دسته‌بندی را انتخاب کنید تا ابزارهای آن را ببینید.\n\n"
        "*دستورات مستقیم:*\n"
        "/start — شروع و نمایش منو\n"
        "/calc — ماشین‌حساب\n"
        "/qr — ساخت کد QR\n"
        "/pass — مولد رمز عبور\n"
        "/cal — تقویم خورشیدی\n"
        "/help — این پیام",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )


# ── Quick shortcut commands ───────────────────────────────────────────────────
async def _quick(update, tool_id, label):
    await update.message.reply_text(
        f"باز کردن *{label}*:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"🚀 {label}", web_app=WebAppInfo(url=tool_url(tool_id)))
        ]]),
        parse_mode="Markdown"
    )

async def calc_cmd(u, c): await _quick(u, "calc",     "ماشین‌حساب")
async def qr_cmd  (u, c): await _quick(u, "qr",       "ساخت QR")
async def pass_cmd(u, c): await _quick(u, "pass",     "مولد رمز عبور")
async def cal_cmd (u, c): await _quick(u, "jcal",     "تقویم خورشیدی")


# ── Handle category keyboard presses ─────────────────────────────────────────
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # "همه ابزارها" button
    if "همه ابزارها" in text:
        await update.message.reply_text(
            "🧰 جعبه‌ابزار کامل:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🧰 باز کردن جعبه‌ابزار", web_app=WebAppInfo(url=TOOLBOX_URL))
            ]])
        )
        return

    # Category buttons
    if text in CATEGORIES:
        await update.message.reply_text(
            f"ابزارهای *{text}*:",
            reply_markup=category_inline(text),
            parse_mode="Markdown"
        )
        return

    # Unknown text — show keyboard hint
    await update.message.reply_text(
        "از منوی پایین یک دسته‌بندی انتخاب کنید 👇",
        reply_markup=main_keyboard()
    )


# ── Handle web_app_data from miniapp (Bale.WebApp.sendData) ──────────────────
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.web_app_data.data
    try:
        data = json.loads(raw)
    except Exception:
        data = {"raw": raw}

    action = data.get("action", "")
    if action == "share_result":
        await update.message.reply_text(f"📊 نتیجه:\n{data.get('text', '')}")
    else:
        await update.message.reply_text(f"داده دریافت شد:\n`{raw}`", parse_mode="Markdown")


# ── Validate initData on your backend ────────────────────────────────────────
def validate_init_data(init_data: str) -> bool:
    """
    Call this on your web server when the miniapp POSTs initData to you.
    Verifies the HMAC-SHA256 signature to confirm data came from Bale.
    """
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return False
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        computed   = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, received_hash)
    except Exception:
        return False


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).base_url(BASE_URL).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("calc",   calc_cmd))
    app.add_handler(CommandHandler("qr",     qr_cmd))
    app.add_handler(CommandHandler("pass",   pass_cmd))
    app.add_handler(CommandHandler("cal",    cal_cmd))

    # Data sent back from miniapp via Bale.WebApp.sendData()
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

    # Category keyboard presses (must be after WEB_APP_DATA handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
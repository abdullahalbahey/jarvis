"""Telegram interface for Jarvis. It cannot publish to LinkedIn."""
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from agent import create_lesson, draft_linkedin, research_topic
from store import init_db, add_note, recent_notes, recent_drafts, get_draft, set_draft_status

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def allowed(update):
    configured = os.getenv("ALLOWED_TELEGRAM_USER_ID", "").strip()
    user = update.effective_user
    return bool(configured and user and str(user.id) == configured)


async def guard(update):
    if not allowed(update):
        if update.effective_message:
            await update.effective_message.reply_text("Access denied. Ask the owner to configure your Telegram user ID.")
        return False
    return True


async def reply(update, text):
    message = update.effective_message
    if not message:
        return
    chunks = [text[i:i + 3900] for i in range(0, len(text))] or ["(empty result)"]
    for chunk in chunks:
        await message.reply_text(chunk, disable_web_page_preview=True)


def arg(context):
    return " ".join(context.args).strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    await reply(update, "Jarvis . Personal Brand & Learning Agent\nPositioning: Business Analysis + AI + Product Management\n\n"
        "/research <topic> . research and save a brief\n/draft <topic> . prepare a LinkedIn draft\n"
        "/learn <topic> . create a lesson and quiz\n/save <your insight> . save personal knowledge\n"
        "/notes . list saved notes\n/drafts . list drafts\n/review <id> . show a draft\n"
        "/approve <id> . mark approved for manual use only\n/reject <id> . reject a draft\n\n"
        "This bot cannot publish to LinkedIn. Do not submit confidential employer or client data.")


async def research(update, context):
    if not await guard(update): return
    topic = arg(context)
    if not topic:
        await reply(update, "Usage: /research <topic>"); return
    await reply(update, "Researching. Search results are leads and must be verified.")
    try:
        brief, sources = research_topic(topic)
        await reply(update, brief + "\n\nSources:\n" + "\n".join(s["url"] for s in sources))
    except Exception:
        logger.exception("Research failed")
        await reply(update, "Research failed. Check API/search availability and try again.")


async def draft(update, context):
    if not await guard(update): return
    topic = arg(context)
    if not topic:
        await reply(update, "Usage: /draft <topic>"); return
    await reply(update, "Preparing a draft. It will not be published.")
    try:
        draft_id, body, _ = draft_linkedin(topic)
        await reply(update, f"Draft #{draft_id} saved with status DRAFT.\n\n{body}")
    except Exception:
        logger.exception("Draft generation failed")
        await reply(update, "Draft generation failed. Check API/search availability and try again.")


async def learn(update, context):
    if not await guard(update): return
    topic = arg(context)
    if not topic:
        await reply(update, "Usage: /learn <topic>"); return
    await reply(update, "Preparing a lesson and knowledge check.")
    try:
        await reply(update, create_lesson(topic))
    except Exception:
        logger.exception("Lesson generation failed")
        await reply(update, "Lesson generation failed. Check API/search availability and try again.")


async def save(update, context):
    if not await guard(update): return
    body = arg(context)
    if not body:
        await reply(update, "Usage: /save <your own experience, lesson or idea>"); return
    if len(body) > 5000:
        await reply(update, "Please keep a note under 5,000 characters."); return
    note_id = add_note("personal", "Personal insight", body)
    await reply(update, f"Saved personal note #{note_id}.")


async def notes(update, context):
    if not await guard(update): return
    items = recent_notes(10)
    if not items:
        await reply(update, "No saved notes yet. Try /research, /learn or /save."); return
    await reply(update, "\n\n".join(f"#{n['id']} [{n['kind']}] {n['title']}\n{n['body'][:220]}" for n in items))


async def drafts(update, context):
    if not await guard(update): return
    items = recent_drafts(10)
    if not items:
        await reply(update, "No drafts yet. Try /draft <topic>."); return
    await reply(update, "\n\n".join(f"#{d['id']} [{d['status'].upper()}] {d['topic']}\n{d['body'][:180]}" for d in items))


async def review(update, context):
    if not await guard(update): return
    raw = arg(context)
    if not raw.isdigit():
        await reply(update, "Usage: /review <draft_id>"); return
    item = get_draft(int(raw))
    if not item:
        await reply(update, "Draft not found."); return
    sources = "\n".join(s["url"] for s in item["sources"]) or "No sources stored."
    await reply(update, f"Draft #{item['id']} . {item['status'].upper()}\nTopic: {item['topic']}\n\n{item['body']}\n\nStored sources:\n{sources}")


async def set_status(update, context, status):
    if not await guard(update): return
    raw = arg(context)
    if not raw.isdigit():
        await reply(update, f"Usage: /{status} <draft_id>"); return
    draft_id = int(raw)
    if not get_draft(draft_id):
        await reply(update, "Draft not found."); return
    set_draft_status(draft_id, "approved" if status == "approve" else "rejected")
    if status == "approve":
        await reply(update, f"Draft #{draft_id} marked APPROVED for you to copy/edit manually. It has NOT been published.")
    else:
        await reply(update, f"Draft #{draft_id} marked REJECTED.")


async def approve(update, context):
    await set_status(update, context, "approve")


async def reject(update, context):
    await set_status(update, context, "reject")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled bot error", exc_info=context.error)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    user_id = os.getenv("ALLOWED_TELEGRAM_USER_ID", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required.")
    if not user_id.isdigit():
        raise SystemExit("ALLOWED_TELEGRAM_USER_ID must be your numeric Telegram user ID.")
    init_db()
    app = Application.builder().token(token).build()
    for name, fn in [("start", start), ("help", start), ("research", research), ("draft", draft),
                     ("learn", learn), ("save", save), ("notes", notes), ("drafts", drafts),
                     ("review", review), ("approve", approve), ("reject", reject)]:
        app.add_handler(CommandHandler(name, fn))
    app.add_error_handler(error_handler)
    logger.info("Jarvis is running. LinkedIn publishing is disabled.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

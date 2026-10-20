# Jarvis: LinkedIn Personal Brand & Learning Agent

MVP positioning: Business Analysis + AI + Product Management. Audience: recruiters, hiring managers, technology professionals, future leaders, business leaders and potential clients.

## Features
- Telegram commands for research, LinkedIn drafts, short lessons, quizzes and personal notes.
- Web search with source URLs attached to research and drafts.
- Persistent local SQLite notes and draft review states.
- Human approval workflow. **This MVP never publishes to LinkedIn.**
- Private-user access restriction by Telegram numeric user ID.

## Setup in GitHub Codespaces
1. Create a Telegram bot using Telegram's official BotFather.
2. Create a Gemini API key in Google AI Studio.
3. Copy .env.example to .env and fill in the values.
4. Install and run:

    pip install -r requirements.txt
    python app.py

Keep tokens in Codespaces Secrets/environment variables. Never commit .env or share keys in chat.

## Commands
- /research <topic> . research and save a source-linked brief
- /draft <topic> . create a LinkedIn draft for your review
- /learn <topic> . create a short lesson and quiz
- /save <your insight> . save your own experience or idea
- /notes . list saved notes
- /drafts . list drafts
- /review <id> . show a draft and its sources
- /approve <id> . mark approved for manual use; does not publish
- /reject <id> . reject a draft

## Security and limitations
- The bot denies users whose Telegram ID does not match ALLOWED_TELEGRAM_USER_ID.
- No LinkedIn credentials, auto-posting, browser control, email access or autonomous consequential actions.
- Do not submit confidential employer or client data.
- The model must not invent personal experiences, achievements, metrics or credentials. Add real examples to PERSONAL_VOICE.md.
- Search snippets are untrusted. Open source URLs and verify claims before publishing.
- SQLite is local to the runtime. A Codespace can stop or be deleted, so this is a development setup, not durable 24/7 hosting. Back up the database securely.
- The MVP does not connect to LinkedIn analytics. Add performance data manually in a later version.

## Tests
    python -m unittest discover -s tests -v

## Milestones
1. Run the bot in Codespaces and test private access.
2. Refine PERSONAL_VOICE.md with real examples of your writing.
3. Add weekly learning reviews and manual performance tracking.
4. Consider always-on hosting only after the MVP proves useful and backups/security are planned.

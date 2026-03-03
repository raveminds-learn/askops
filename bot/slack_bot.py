"""
bot/slack_bot.py — AskOps by RaveMinds
==========================================
Progressive disclosure Slack bot.
- Everyone sees the business summary first
- Buttons let users drill into manager, technical, or full view
- No role setup needed
"""
import os
import re
import json
import httpx
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])
API_URL = os.getenv("API_URL", "http://localhost:8001/ask")


# ── Helpers ────────────────────────────────────────────────────────

def call_api(user_id: str, question: str, on_progress=None) -> dict:
    """Call AskOps API. Uses streaming for progress when on_progress(msg) is provided, else regular POST."""
    if on_progress:
        stream_url = API_URL.replace("/ask", "/ask/stream")
        result = None
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", stream_url, json={"user_id": user_id, "question": question}) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue
                        if data.get("event") == "progress" and data.get("stage") == "data_ready":
                            tid = data.get("trade_id", "")
                            on_progress(f"Trade {tid} found, analyzing the trade...")
                        elif data.get("event") == "result":
                            result = data
                            break
        if not result:
            raise httpx.HTTPError("No result from stream")
        return result
    else:
        resp = httpx.post(API_URL, json={"user_id": user_id, "question": question}, timeout=120.0)
        resp.raise_for_status()
        return resp.json()


def business_blocks(answer: str, question: str, trade_id: str, latency_ms: int) -> list:
    """
    Business view Slack blocks with drill-down buttons.
    This is what everyone sees first.
    """
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "AskOps by RaveMinds", "emoji": True}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": answer}
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"❓ _{question}_"}]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📊 Manager View", "emoji": True},
                    "style": "primary",
                    "action_id": "view_manager",
                    "value": json.dumps({"question": question, "trade_id": trade_id}),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔧 Technical Detail", "emoji": True},
                    "action_id": "view_technical",
                    "value": json.dumps({"question": question, "trade_id": trade_id}),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📋 Full Report", "emoji": True},
                    "action_id": "view_full",
                    "value": json.dumps({"question": question, "trade_id": trade_id}),
                },
            ],
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"⏱ {latency_ms}ms · AskOps by RaveMinds · Ask your infrastructure anything."}]
        },
    ]


def detail_blocks(title: str, content: str, emoji: str) -> list:
    """Blocks for manager/technical/full drill-down views."""
    return [
        {"type": "divider"},
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {title}", "emoji": True}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": content}
        },
        {"type": "divider"},
    ]


# ── Event handlers ─────────────────────────────────────────────────

@app.event("app_mention")
def handle_mention(event, say, client):
    """Handle @AskOps mentions in channels."""
    _handle_question(event, say, client)


@app.event("message")
def handle_dm(event, say, client):
    """Handle direct messages to AskOps."""
    if event.get("channel_type") == "im" and not event.get("bot_id"):
        _handle_question(event, say, client)


def _handle_question(event, say, client):
    """Core handler — calls API, shows business view + buttons."""
    user_id  = event["user"]
    channel  = event["channel"]
    question = re.sub(r"<@[A-Z0-9]+>", "", event["text"]).strip()

    # Post immediate ack so user knows we're working (avoids timeout)
    ack_msg = client.chat_postMessage(
        channel=channel,
        text="⏳ AskOps is looking into this... (~30 sec)",
    )
    ts = ack_msg["ts"]

    def update_progress(msg):
        client.chat_update(channel=channel, ts=ts, text=msg)

    try:
        data = call_api(user_id, question, on_progress=update_progress)
        business   = data.get("business", "No answer generated.")
        trade_id   = data.get("trade_id", "")
        latency_ms = data.get("latency_ms", 0)

        blocks = business_blocks(business, question, trade_id, latency_ms)

        client.chat_update(
            channel=channel,
            ts=ts,
            blocks=blocks,
            text="AskOps response",
        )
    except Exception as e:
        client.chat_update(
            channel=channel,
            ts=ts,
            text=f"❌ Sorry, something went wrong: `{str(e)}`",
        )


# ── Button handlers (progressive disclosure) ──────────────────────

@app.action("view_manager")
def handle_manager_view(ack, body, say, client):
    """User clicked 📊 Manager View."""
    ack()
    payload  = json.loads(body["actions"][0]["value"])
    question = payload["question"]
    user_id  = body["user"]["id"]

    try:
        data    = call_api(user_id, question)
        content = data.get("manager", "No manager view available.")
        blocks  = detail_blocks("Manager View", content, "📊")
    except Exception as e:
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": f"❌ Error: `{str(e)}`"}}]

    say(blocks=blocks, text="Manager View")


@app.action("view_technical")
def handle_technical_view(ack, body, say, client):
    """User clicked 🔧 Technical Detail."""
    ack()
    payload  = json.loads(body["actions"][0]["value"])
    question = payload["question"]
    user_id  = body["user"]["id"]

    try:
        data    = call_api(user_id, question)
        content = data.get("technical", "No technical view available.")
        blocks  = detail_blocks("Technical Deep-Dive", content, "🔧")
    except Exception as e:
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": f"❌ Error: `{str(e)}`"}}]

    say(blocks=blocks, text="Technical View")


@app.action("view_full")
def handle_full_view(ack, body, say, client):
    """User clicked 📋 Full Report."""
    ack()
    payload  = json.loads(body["actions"][0]["value"])
    question = payload["question"]
    user_id  = body["user"]["id"]

    try:
        data    = call_api(user_id, question)
        content = data.get("full", "No full report available.")
        blocks  = detail_blocks("Full Report", content, "📋")
    except Exception as e:
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": f"❌ Error: `{str(e)}`"}}]

    say(blocks=blocks, text="Full Report")


# ── Start ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AskOps by RaveMinds — Ask your infrastructure anything.")
    print("Bot is running and listening...")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

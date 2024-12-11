import os
import logging
import requests
from enum import Enum
from dotenv import load_dotenv
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InputTextMessageContent, 
    InlineQueryResultArticle
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters
)

class ActionsUsed(Enum):
    MORE_DETAILS = "more_details"
    SYNONYMS = "synonyms"
    ANTONYMS = "antonyms"

def save_word_data(context: ContextTypes.DEFAULT_TYPE, data: dict) -> None:
    context.user_data["data"] = data

def get_word_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.get("data", {})


def fetch_word_data(word: str) -> dict:
    host = os.getenv("WORDSAPI_HOST")
    key = os.getenv("WORDSAPI_KEY")
    url = f"https://{host}/words/{word}"
    headers = {
        "X-RapidAPI-Host": host,
        "X-RapidAPI-Key": key,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_definition_list(data: dict) -> list:
    results = data.get("results", [])
    if not results:
        return []
    return [r.get("definition", "No definition available.") for r in results]

def get_synonym_list(data: dict) -> list:
    results = data.get("results", [])
    all_synonyms = set()
    for r in results:
        synonyms = r.get("synonyms", [])
        for synonym in synonyms:
            all_synonyms.add(synonym)
    return sorted(all_synonyms) if all_synonyms else []

def get_antonym_list(data: dict) -> list:
    results = data.get("results", [])
    all_antonyms = set()
    for r in results:
        antonyms = r.get("antonyms", [])
        for antonym in antonyms:
            all_antonyms.add(antonym)
    return sorted(all_antonyms) if all_antonyms else []

def generate_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    buttons.append(InlineKeyboardButton("Synonyms", callback_data="synonyms"))
    buttons.append(InlineKeyboardButton("Antonyms", callback_data="antonyms"))
    buttons.append(InlineKeyboardButton("Close", callback_data="close"))
    return InlineKeyboardMarkup([buttons])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Hello! I can look up words for you using WordsAPI.\n"
        "Type a word and I'll give you its definition.\n\n"
        "Use /help to see available commands.\n\n"
        "By Danil Petrov"
    )
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "I can help you find definitions of words.\n"
        "- Type a word directly to get its definition.\n"
        "- After getting a definition, use the 'More details' button for origin, synonyms and more.\n"
        "Commands:\n"
        "/help - Show this help message\n\n"
        "By Danil Petrov"
    )
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Action cancelled.")
    return ConversationHandler.END

async def provide_word_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    word = update.message.text.strip().lower()
    context.user_data["word"] = word
    data = fetch_word_data(word)

    if not data or "results" not in data:
        await update.message.reply_text("I couldn't find that word in WordsAPI.")
        return ConversationHandler.END

    definitions = get_definition_list(data)
    main_meaning = definitions[0] if definitions else "No definitions found."
    if "No definitions found" in main_meaning:
        await update.message.reply_text(main_meaning)
        return ConversationHandler.END

    save_word_data(context, data)

    keyboard = [
        [InlineKeyboardButton("More details", callback_data="more_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Main meaning of '{word}':\n\n{main_meaning}",
        reply_markup=reply_markup
    )
    return 0

async def more_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = generate_keyboard()
    await query.edit_message_reply_markup(reply_markup=keyboard)

def merge_with_query(existing_text: str, append_text: str) -> str:
    return f"{existing_text}\n\n{append_text}"

async def synonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    synonyms_list = get_synonym_list(get_word_data(context))
    synonyms_text = ", ".join(synonyms_list) if synonyms_list else "No synonyms found."
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"Synonyms:\n{synonyms_text}")
    keyboard = generate_keyboard()
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def antonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    antonyms_list = get_antonym_list(get_word_data(context))
    antonyms_text = ", ".join(antonyms_list) if antonyms_list else "No antonyms found."
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"Antonyms:\n{antonyms_text}")
    keyboard = generate_keyboard()
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)

def main():
    # test()

    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Bot token not found. Please set TELEGRAM_BOT_TOKEN.")

    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            0: [],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(CallbackQueryHandler(more_details_callback, pattern="^more_details$"))
    application.add_handler(CallbackQueryHandler(synonyms_callback, pattern="^synonyms$"))
    application.add_handler(CallbackQueryHandler(antonyms_callback, pattern="^antonyms$"))
    application.add_handler(CallbackQueryHandler(close_callback, pattern="^close$"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, provide_word_information), group=1)

    application.run_polling()

def test():
    word = "table"
    data = fetch_word_data(word)
    definitions = get_definition_list(data)
    synonyms = get_synonym_list(data)

    print(f"Data for '{word}': {data}")
    print(f"Definitions for '{word}': {definitions}")
    print(f"Synonyms for '{word}': {synonyms}")


if __name__ == "__main__":
    main()

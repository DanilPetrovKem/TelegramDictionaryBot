import os
import logging
from enum import Enum

import requests
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

from words_api_client import WordsAPIClient
from inline_keyboard import Buttons, InlineKeyboard

words_api = WordsAPIClient()

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def save_word_data(context: ContextTypes.DEFAULT_TYPE, data: dict) -> None:
    context.user_data["data"] = data

def get_word_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.get("data", {})

def get_definition_list(data: dict) -> list:
    results = data.get("results", [])
    if not results:
        return []
    return [r.get("definition", "No definition available.") for r in results]

def get_synonym_list(data: dict) -> list:
    results = data.get("results", [])
    all_synonyms = {synonym for r in results for synonym in r.get("synonyms", [])}
    return sorted(all_synonyms)

def get_antonym_list(data: dict) -> list:
    results = data.get("results", [])
    all_antonyms = {antonym for r in results for antonym in r.get("antonyms", [])}
    return sorted(all_antonyms)

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
    data = words_api.fetch_word_data(word)

    if not data or "results" not in data:
        await update.message.reply_text("I couldn't find that word in WordsAPI.")
        return ConversationHandler.END

    definitions = get_definition_list(data)
    main_meaning = definitions[0] if definitions else "No definitions found."
    if "No definitions found" in main_meaning:
        await update.message.reply_text(main_meaning)
        return ConversationHandler.END

    save_word_data(context, data)

    keyboard = InlineKeyboard.generate([Buttons.MORE_DETAILS])
    await update.message.reply_text(
        f"Main meaning of '{word}':\n\n{main_meaning}",
        reply_markup=keyboard
    )
    return 0

async def more_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboard.generate([
        [Buttons.SYNONYMS, Buttons.ANTONYMS],
        [Buttons.CLOSE]
    ])
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
    keyboard = InlineKeyboard.generate([
        [Buttons.SYNONYMS, Buttons.ANTONYMS],
        [Buttons.CLOSE]
    ])
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def antonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    antonyms_list = get_antonym_list(get_word_data(context))
    antonyms_text = ", ".join(antonyms_list) if antonyms_list else "No antonyms found."
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"Antonyms:\n{antonyms_text}")
    keyboard = InlineKeyboard.generate([
        [Buttons.SYNONYMS, Buttons.ANTONYMS],
        [Buttons.CLOSE]
    ])
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)

CALLBACK_HANDLERS = {
    Buttons.MORE_DETAILS.callback_data: more_details_callback,
    Buttons.SYNONYMS.callback_data: synonyms_callback,
    Buttons.ANTONYMS.callback_data: antonyms_callback,
    Buttons.CLOSE.callback_data: close_callback,
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    handler = CALLBACK_HANDLERS.get(data)
    if handler:
        await handler(update, context)
    else:
        logging.warning(f"Unknown callback data: {data}")
        await query.answer("Unknown action")

def test() -> None:
    word = "table"
    data = words_api.fetch_word_data(word)
    definitions = get_definition_list(data)
    synonyms = get_synonym_list(data)

def load_config():
    required_vars = ["WORDSAPI_HOST", "WORDSAPI_KEY", "TELEGRAM_BOT_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

def main() -> None:
    load_config()
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Bot token not found. Please set TELEGRAM_BOT_TOKEN.")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(CallbackQueryHandler(callback_dispatcher))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, provide_word_information), group=1)

    application.run_polling()

if __name__ == "__main__":
    main()

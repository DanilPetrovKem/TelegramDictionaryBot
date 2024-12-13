import os
import logging
from dotenv import load_dotenv
from telegram import Update
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
from inline_keyboard import Button, InlineKeyboard
from localization import Localization
from localization_keys import Phrases

logging.basicConfig(level=logging.INFO, format='%(message)s')

words_api = WordsAPIClient()
localization_instances = {}

def get_user_locale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    custom_locale = context.user_data.get("locale")
    if custom_locale in Localization.locales:
        return custom_locale
    return update.effective_user.language_code or "en"

def get_localization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Localization:
    user_locale = get_user_locale(update, context)
    if user_locale not in localization_instances:
        localization_instances[user_locale] = Localization(locale=user_locale)
    return localization_instances[user_locale]

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
    localization = get_localization(update, context)
    text = localization.get(Phrases.START_MESSAGE)
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    text = localization.get(Phrases.HELP_MESSAGE)
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.CANCEL_MESSAGE))
    return ConversationHandler.END

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    if len(context.args) != 1:
        await update.message.reply_text(localization.get(Phrases.INVALID_COMMAND_USAGE))
        return
    language = context.args[0].lower()
    if language not in Localization.locales:
        await update.message.reply_text(localization.get(Phrases.INVALID_LANGUAGE))
        return
    context.user_data["locale"] = language
    localization = get_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.LANGUAGE_CHANGED).format(language=language))

async def provide_word_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    localization = get_localization(update, context)
    word = update.message.text.strip().lower()
    data = words_api.fetch_word_data(word)

    if not data or "results" not in data:
        await update.message.reply_text(localization.get(Phrases.WORD_NOT_FOUND))
        return ConversationHandler.END

    definitions = get_definition_list(data)
    main_meaning = definitions[0] if definitions else localization.get(Phrases.NO_DEFINITIONS_FOUND)
    if not definitions:
        await update.message.reply_text(main_meaning)
        return ConversationHandler.END

    save_word_data(context, data)

    keyboard = InlineKeyboard.generate([Button.MORE_DETAILS], localization)

    if "last_message_id" in context.user_data:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=context.user_data["last_message_id"],
                reply_markup=None
            )
        except Exception as e:
            logging.warning(f"Failed to edit previous message: {e}")

    sent_message = await update.message.reply_text(
        f"'{word}':\n\n1. {main_meaning}",
        reply_markup=keyboard
    )
    context.user_data["last_message_id"] = sent_message.message_id

    return 0

async def more_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    query = update.callback_query
    await query.answer()

    context.user_data["used_buttons"] = []
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_reply_markup(reply_markup=keyboard)

def merge_with_query(existing_text: str, append_text: str) -> str:
    return f"{existing_text}\n\n{append_text}"

async def synonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    query = update.callback_query
    await query.answer()

    synonyms_list = get_synonym_list(get_word_data(context))
    synonyms_text = ", ".join(synonyms_list) if synonyms_list else localization.get(Phrases.NO_SYNONYMS_FOUND)
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"{localization.get(Phrases.SYNONYMS)}:\n{synonyms_text}")
    context.user_data["used_buttons"].append(Button.SYNONYMS.value)
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def antonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    query = update.callback_query
    await query.answer()

    antonyms_list = get_antonym_list(get_word_data(context))
    antonyms_text = ", ".join(antonyms_list) if antonyms_list else localization.get(Phrases.NO_ANTONYMS_FOUND)
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"{localization.get(Phrases.ANTONYMS)}:\n{antonyms_text}")
    context.user_data["used_buttons"].append(Button.ANTONYMS.value)
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    context.user_data["used_buttons"] = []
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)

CALLBACK_HANDLERS = {
    Button.MORE_DETAILS.callback_data: more_details_callback,
    Button.SYNONYMS.callback_data: synonyms_callback,
    Button.ANTONYMS.callback_data: antonyms_callback,
    Button.CLOSE.callback_data: close_callback,
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = get_localization(update, context)
    query = update.callback_query
    data = query.data

    handler = CALLBACK_HANDLERS.get(data)
    if handler:
        await handler(update, context)
    else:
        logging.warning(f"Unknown callback data: {data}")
        await query.answer("Unknown action")


def main() -> None:
    Localization.validate_localizations()
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token: raise ValueError("Bot token not found. Please set TELEGRAM_BOT_TOKEN.")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("lang", set_language))

    application.add_handler(CallbackQueryHandler(callback_dispatcher))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, provide_word_information), group=1)

    application.run_polling()

if __name__ == "__main__":
    main()

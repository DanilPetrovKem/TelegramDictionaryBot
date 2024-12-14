import os
import logging
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
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
from localization import Localization, select_localization
from localization_keys import Phrases
from enums import ContextKey

logging.basicConfig(level=logging.INFO, format='%(message)s')

words_api = WordsAPIClient()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    text = localization.get(Phrases.START_MESSAGE)
    keyboard = InlineKeyboard.generate([
        Button.RANDOM,
        Button.LANG_EN,
        Button.LANG_RU
    ], localization)
    await update.message.reply_text(text, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    text = localization.get(Phrases.HELP_MESSAGE)
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.CANCEL_MESSAGE))
    return ConversationHandler.END

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    if len(context.args) != 1:
        await update.message.reply_text(localization.get(Phrases.INVALID_COMMAND_USAGE))
        return
    language = context.args[0].lower()
    if language not in Localization.locales:
        await update.message.reply_text(localization.get(Phrases.INVALID_LANGUAGE))
        return
    context.user_data[ContextKey.LOCALE] = language
    localization = select_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.LANGUAGE_CHANGED).format(language=language))

async def provide_word_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    localization = select_localization(update, context)
    word = update.message.text.strip().lower()
    data = words_api.fetch_word_data(word)

    if not data or "results" not in data:
        await update.message.reply_text(localization.get(Phrases.WORD_NOT_FOUND))
        return ConversationHandler.END

    definitions = words_api.get_definition_list(data)
    main_meaning = definitions[0] if definitions else localization.get(Phrases.NO_DEFINITIONS_FOUND)
    if not definitions:
        await update.message.reply_text(main_meaning)
        return ConversationHandler.END

    context.user_data[ContextKey.DATA] = data

    keyboard = InlineKeyboard.generate([Button.MORE_DETAILS], localization)

    if ContextKey.LAST_MESSAGE_ID in context.user_data:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=context.user_data[ContextKey.LAST_MESSAGE_ID],
                reply_markup=None
            )
        except Exception as e:
            logging.warning(f"Failed to edit previous message: {e}")

    sent_message = await update.message.reply_text(
        f"'{word}':\n\n1. {main_meaning}",
        reply_markup=keyboard
    )
    context.user_data[ContextKey.LAST_MESSAGE_ID] = sent_message.message_id
    return 0

def merge_with_query(query_text: str, append_text: str) -> str:
    return f"{query_text}\n\n{append_text}"

async def more_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    query = update.callback_query
    await query.answer()

    context.user_data[ContextKey.USED_BUTTONS] = []
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_reply_markup(reply_markup=keyboard)

async def all_definitions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    query = update.callback_query
    await query.answer()

    definitions_list = words_api.get_definition_list(context.user_data[ContextKey.DATA])
    definitions_list = definitions_list[1:] if len(definitions_list) > 1 else definitions_list
    definitions_text = "\n".join([f"{i+1}. {definition}" for i, definition in enumerate(definitions_list, start=1)])
    existing_text = query.message.text
    lines = existing_text.split('\n')
    for idx, line in enumerate(lines):
        if line.startswith("1. "):
            insert_idx = idx + 1
            break
    new_text = "\n".join(lines[:insert_idx] + [definitions_text] + lines[insert_idx:])
    context.user_data[ContextKey.USED_BUTTONS].append(Button.ALL_DEFINITIONS.value)
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def synonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    query = update.callback_query
    await query.answer()

    synonyms_list = words_api.get_synonym_list(context.user_data[ContextKey.DATA])
    synonyms_text = ", ".join(synonyms_list) if synonyms_list else localization.get(Phrases.NO_SYNONYMS_FOUND)
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"{localization.get(Phrases.SYNONYMS)}:\n{synonyms_text}")
    context.user_data[ContextKey.USED_BUTTONS].append(Button.SYNONYMS.value)
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def antonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    query = update.callback_query
    await query.answer()

    antonyms_list = words_api.get_antonym_list(context.user_data[ContextKey.DATA])
    antonyms_text = ", ".join(antonyms_list) if antonyms_list else localization.get(Phrases.NO_ANTONYMS_FOUND)
    existing_text = query.message.text
    new_text = merge_with_query(existing_text, f"{localization.get(Phrases.ANTONYMS)}:\n{antonyms_text}")
    context.user_data[ContextKey.USED_BUTTONS].append(Button.ANTONYMS.value)
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    context.user_data[ContextKey.USED_BUTTONS] = []
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)

CALLBACK_HANDLERS = {
    Button.ALL_DEFINITIONS.callback_data: all_definitions_callback,
    Button.MORE_DETAILS.callback_data: more_details_callback,
    Button.SYNONYMS.callback_data: synonyms_callback,
    Button.ANTONYMS.callback_data: antonyms_callback,
    Button.CLOSE.callback_data: close_callback,
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    query = update.callback_query
    data = query.data

    handler = CALLBACK_HANDLERS.get(data)
    if handler:
        await handler(update, context)
    else:
        logging.warning(f"Unknown callback data: {data}")
        await query.answer("Unknown action")

async def lang_en_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language_specific(update, context, 'en')

async def lang_ru_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language_specific(update, context, 'ru')

async def set_language_specific(update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
    context.user_data[ContextKey.LOCALE] = language
    localization = select_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.LANGUAGE_CHANGED).format(language=language))

def get_localized_commands(localization: Localization) -> list:
    return [
        BotCommand("lang_en", localization.get(Phrases.COMMAND_LANG_EN)),
        BotCommand("lang_ru", localization.get(Phrases.COMMAND_LANG_RU)),
        BotCommand("help", localization.get(Phrases.COMMAND_HELP)),
    ]

async def post_init(application: Application) -> None:
    bot = application.bot
    for locale in Localization.locales:
        localization = Localization(locale)
        commands = get_localized_commands(localization)
        await bot.set_my_commands(commands=commands, language_code=locale)

def main() -> None:
    Localization.validate_localizations()
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token: raise ValueError("Bot token not found. Please set TELEGRAM_BOT_TOKEN.")

    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .build()
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("lang", set_language))
    application.add_handler(CommandHandler("lang_en", lang_en_command))
    application.add_handler(CommandHandler("lang_ru", lang_ru_command))

    application.add_handler(CallbackQueryHandler(callback_dispatcher))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, provide_word_information), group=1)

    application.run_polling()

if __name__ == "__main__":
    main()

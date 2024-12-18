import os
import logging
from dotenv import load_dotenv
import functools
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
from enums import UserData, MessageResult

logging.basicConfig(level=logging.INFO, format='%(message)s')

words_api = WordsAPIClient()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    text = localization.get(Phrases.START_MESSAGE)
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    text = localization.get(Phrases.HELP_MESSAGE)
    await update.message.reply_text(text)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.CANCEL_MESSAGE))
    return ConversationHandler.END

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = words_api.fetch_random_word()
    if not word:
        return
    await provide_word_information(word, update, context)

async def plain_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = update.message.text.strip().lower()
    await close_previous_markup(update, context)
    await provide_word_information(word, update, context)

def convert_word_data_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, MessageResult]:
    localization = select_localization(update, context)
    used_buttons = context.user_data.get(UserData.USED_BUTTONS, [])

    data = context.user_data.get(UserData.DATA, {})

    if not data or "word" not in data:
        return (localization.get(Phrases.WORD_NOT_FOUND), MessageResult.NOT_FOUND)
    
    word = data.get("word", "")
    results = data.get("results", [])
    message_text = f"\"{word}\":\n\n"

    if not results:
        message_text += localization.get(Phrases.NO_DEFINITIONS_FOUND)
        return (message_text, MessageResult.NO_DEFINITIONS)

    show_all_definitions = Button.ALL_DEFINITIONS.value in used_buttons
    show_synonyms = Button.SYNONYMS.value in used_buttons
    show_antonyms = Button.ANTONYMS.value in used_buttons
    show_rhymes = Button.RHYMES.value in used_buttons
    
    results_to_process = results if show_all_definitions else results[:1]
    for i, result in enumerate(results_to_process, start=1):
        definition = result.get("definition", "ERROR: No definition available.")
        message_text += f"{i}. {definition}\n"

        if show_synonyms:
            synonyms = result.get("synonyms", [])
            if synonyms:
                synonyms_text = ", ".join(synonyms)
                message_text += f"   ≈ {synonyms_text}\n"

        if show_antonyms:
            antonyms = result.get("antonyms", [])
            if antonyms:
                antonyms_text = ", ".join(antonyms)
                message_text += f"   ≠ {antonyms_text}\n"

    if show_rhymes:
        rhymes = words_api.fetch_rhymes(word)
        if rhymes:
            rhymes_text = ", ".join(rhymes)
        else:
            rhymes_text = "-"
        message_text += f"\n{localization.get(Phrases.RHYMES)}:\n{rhymes_text}\n"

    return (message_text, MessageResult.OK)

async def close_previous_markup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if UserData.LAST_MESSAGE_ID in context.user_data:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=context.user_data[UserData.LAST_MESSAGE_ID],
                reply_markup=None
            )
        except Exception as e:
            logging.warning(f"Failed to edit previous message: {e}")

async def provide_word_information(word: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    localization = select_localization(update, context)
    data = words_api.fetch_word_data(word)
    context.user_data[UserData.USED_BUTTONS] = []
    context.user_data[UserData.DATA] = data

    message_text, message_result = convert_word_data_to_message(update, context)
    inline_keyboard = None
    if message_result == MessageResult.OK:
        inline_keyboard = InlineKeyboard.generate([Button.MORE_DETAILS], localization)

    sent_message = await update.message.reply_text(message_text, reply_markup=inline_keyboard)
    context.user_data[UserData.LAST_MESSAGE_ID] = sent_message.message_id

async def more_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, query, localization) -> None:
    context.user_data[UserData.USED_BUTTONS] = []
    inline_keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_reply_markup(reply_markup=inline_keyboard)

async def all_definitions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, query, localization) -> None:
    context.user_data[UserData.USED_BUTTONS].append(Button.ALL_DEFINITIONS.value)
    new_text, _ = convert_word_data_to_message(update, context)
    inline_keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=inline_keyboard)

async def synonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, query, localization) -> None:
    context.user_data[UserData.USED_BUTTONS].append(Button.SYNONYMS.value)
    new_text, _ = convert_word_data_to_message(update, context)
    inline_keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=inline_keyboard)

async def antonyms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, query, localization) -> None:
    context.user_data[UserData.USED_BUTTONS].append(Button.ANTONYMS.value)
    new_text, _ = convert_word_data_to_message(update, context)
    inline_keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=inline_keyboard)

async def rhymes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, query, localization) -> None:
    context.user_data[UserData.USED_BUTTONS].append(Button.RHYMES.value)
    new_text, _ = convert_word_data_to_message(update, context)
    keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization)
    await query.edit_message_text(new_text, reply_markup=keyboard)

async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, query, localization) -> None:
    context.user_data[UserData.USED_BUTTONS] = []
    await query.edit_message_reply_markup(reply_markup=None)

BUTTON_CALLBACK_HANDLERS = {
    Button.ALL_DEFINITIONS.callback_data: all_definitions_callback,
    Button.MORE_DETAILS.callback_data: more_details_callback,
    Button.SYNONYMS.callback_data: synonyms_callback,
    Button.ANTONYMS.callback_data: antonyms_callback,
    Button.RHYMES.callback_data: rhymes_callback,
    Button.CLOSE.callback_data: close_callback,
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    button_callback = BUTTON_CALLBACK_HANDLERS.get(data)
    if button_callback:
        try:
            localization = select_localization(update, context)
            query = update.callback_query
            await query.answer()
            await button_callback(update, context, query, localization)
        except Exception as e:
            logging.error(f"Error handling callback data '{data}': {e}")
            await close_previous_markup(update, context)
            await query.message.reply_text(f"Error: {str(e)}")
    else:
        logging.warning(f"Unknown callback data: {data}")
        await query.answer("Unknown action")

async def lang_en_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language_specific(update, context, 'en')

async def lang_ru_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language_specific(update, context, 'ru')

async def set_language_specific(update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
    context.user_data[UserData.LOCALE] = language
    localization = select_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.LANGUAGE_CHANGED).format(language=language))

def get_localized_commands(localization: Localization) -> list:
    return [
        BotCommand("random", localization.get(Phrases.COMMAND_RANDOM)),
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
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("lang_en", lang_en_command))
    application.add_handler(CommandHandler("lang_ru", lang_ru_command))
    application.add_handler(CommandHandler("random", random_command))

    application.add_handler(CallbackQueryHandler(callback_dispatcher))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_message_handler), group=1)

    application.run_polling()

if __name__ == "__main__":
    main()

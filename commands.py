from telegram import Update, BotCommand
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from localization import select_localization
from localization_keys import Phrases
from enums import UserData

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

# async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     word = words_api.fetch_random_word()
#     if not word:
#         return
#     await provide_word_information(word, update, context)

async def lang_en_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language_specific(update, context, 'en')

async def lang_ru_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await set_language_specific(update, context, 'ru')

async def set_language_specific(update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
    context.user_data[UserData.LOCALE] = language
    localization = select_localization(update, context)
    await update.message.reply_text(localization.get(Phrases.LANGUAGE_CHANGED).format(language=language))

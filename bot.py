import os
import logging
from dotenv import load_dotenv
import telegram
from telegram import Update, BotCommand
from telegram.constants import ParseMode
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
from lingua_robot_api import LinguaRobotAPIClient
from inline_keyboard import Button, InlineKeyboard
from localization import Localization, select_localization
from localization_keys import Phrases
from enums import UserData
import commands

logging.basicConfig(level=logging.INFO, format='%(message)s')

main_api = LinguaRobotAPIClient()

async def plain_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = update.message.text.strip().lower()
    await close_previous_markup(update, context)
    await provide_word_information(word, update, context)

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
    data = main_api.fetch_data(word)
    context.user_data[UserData.USED_BUTTONS] = []
    context.user_data[UserData.DATA] = data
    context.user_data[UserData.DEFINITIONS_REQUESTED] = 1

    sent_message = await refresh_message(update, context, new=True)
    context.user_data[UserData.LAST_MESSAGE_ID] = sent_message.message_id

roman_numerals = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
}

def build_message_text(context: ContextTypes.DEFAULT_TYPE, entries, chosen_lexeme, localization) -> tuple[str, int]:
    message_parts = []
    lexeme_number = 0
    definitions_requested = context.user_data.get(UserData.DEFINITIONS_REQUESTED, 1)

    lexeme_amount = sum(len(entry.get("lexemes", [])) for entry in entries)

    word = entries[0].get("entry", "")

    message_parts.append(f"\"{word}\":\n\n")

    for etymology_idx, entry in enumerate(entries, start=1):
        etymology_header = f"<b><u>Etymology {roman_numerals.get(etymology_idx, etymology_idx)}</u></b>\n" if not chosen_lexeme and len(entries) > 1 else ""
        etymology_content = []
        for lexeme in entry.get("lexemes", []):
            lexeme_number += 1
            if chosen_lexeme and lexeme_number != chosen_lexeme:
                continue

            part_of_speech = f"{lexeme.get('partOfSpeech', '-').title()}"
            senses = lexeme.get("senses", [])
            lexeme_text = ""

            if not chosen_lexeme:
                lexeme_text = (
                    f"<b>{lexeme_number}. </b>" if not chosen_lexeme else ""
                ) + f"<b>{part_of_speech}</b>\n{senses[0].get('definition', '')}\n"
            else:
                for sense_number, sense in enumerate(senses[:definitions_requested], start=1):
                    definition = sense.get("definition", "")
                    lexeme_text += (
                        f"<b>{sense_number}. {part_of_speech}</b>\n"
                        f"{definition}\n"
                    )

            etymology_content.append(lexeme_text + "\n")

        if etymology_content:
            message_parts.append(etymology_header + "".join(etymology_content))

    complete_message = "".join(message_parts) or localization.get(Phrases.WORD_NOT_FOUND)
    return complete_message, lexeme_amount

async def refresh_message(update:  Update, context: ContextTypes.DEFAULT_TYPE, new: bool = False) -> None:
    localization = select_localization(update, context)
    used_buttons = context.user_data.get(UserData.USED_BUTTONS, [])
    data = context.user_data.get(UserData.DATA, {})

    entries = data.get("entries", [])
    if not entries:
        return await update.message.reply_text(localization.get(Phrases.WORD_NOT_FOUND))

    chosen_lexeme = None
    for button in used_buttons:
        if Button.is_lexeme(button):
            chosen_lexeme = int(button.split('-')[1])
            break

    message_text, lexeme_amount = build_message_text(context, entries, chosen_lexeme, localization)
    inline_keyboard = InlineKeyboard.generate_details_buttons(context.user_data, localization, lexeme_amount)

    if new:
        return await update.message.reply_text(message_text, reply_markup=inline_keyboard, parse_mode=ParseMode.HTML)
    else:
        return await update.callback_query.edit_message_text(message_text, reply_markup=inline_keyboard, parse_mode=ParseMode.HTML)

async def more_definitions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[UserData.DEFINITIONS_REQUESTED] += 1
    await refresh_message(update, context)

async def less_definitions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data[UserData.DEFINITIONS_REQUESTED] > 1:
        context.user_data[UserData.DEFINITIONS_REQUESTED] -= 1

    await refresh_message(update, context)

SPECIAL_BUTTON_CALLBACKS = {
    Button.MORE_DEFINITIONS: more_definitions_callback,
    Button.LESS_DEFINITIONS: less_definitions_callback,
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    button = query.data

    await query.answer()
    if button in SPECIAL_BUTTON_CALLBACKS:
        await SPECIAL_BUTTON_CALLBACKS[button](update, context)
    else:
        context.user_data[UserData.USED_BUTTONS].append(button)
        await refresh_message(update, context)

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
    
    application.add_handler(CommandHandler("start", commands.start_command))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("cancel", commands.cancel_command))
    application.add_handler(CommandHandler("lang_en", commands.lang_en_command))
    application.add_handler(CommandHandler("lang_ru", commands.lang_ru_command))
    # application.add_handler(CommandHandler("random", random_command))

    application.add_handler(CallbackQueryHandler(callback_dispatcher))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_message_handler), group=1)

    application.run_polling()

if __name__ == "__main__":
    main()

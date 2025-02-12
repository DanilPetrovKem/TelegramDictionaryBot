import os
import logging
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.constants import ParseMode, ChatAction
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
from inline_keyboard import Button, InlineKeyboard
from localization import Localization, select_localization
from localization_keys import Phrases
from enums import UserData
from wikked_api import WikkedAPI
from Entry import Entry
import commands

# logging.basicConfig(level=logging.WARNING, format='%(message)s')
wikked_api = WikkedAPI()

async def plain_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = update.message.text.strip()
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

async def provide_word_information(requested_entry: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    entry = wikked_api.fetch(requested_entry)
    
    # If entry is not found, try to invert the case of the first letter
    invertcase_entry = requested_entry[0].swapcase() + requested_entry[1:]
    if not entry.entry:
        entry = wikked_api.fetch(invertcase_entry)
    context.user_data[UserData.USED_BUTTONS] = []
    context.user_data[UserData.ENTRY] = entry
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

def build_message_text(context: ContextTypes.DEFAULT_TYPE, entry: Entry, chosen_lexeme_id, localization: Localization) -> tuple[str, int]:
    SUBSENSE_MAX_DEPTH = 5  # Adjustable max recursion depth
    def render_sense(sense, level, example_requested, synonyms_requested, antonyms_requested, collocations_requested, indent_base="       "):
        indent = indent_base * level
        # Format sense definition (including labels if any)
        definition = f"({', '.join(sense.labels)}) {sense.definition}" if sense.labels else sense.definition
        result = definition + "\n"
        if example_requested and sense.examples:
            for example in sense.examples:
                result += f"{indent}{indent_base}<i>{example}</i>\n"
        if synonyms_requested and sense.synonyms:
            result += f"{indent}{indent_base}<i><b>≈</b> {', '.join(sense.synonyms)}</i>\n"
        if antonyms_requested and sense.antonyms:
            result += f"{indent}{indent_base}<i><b>≠</b> {', '.join(sense.antonyms)}</i>\n"
        if collocations_requested and sense.collocations:
            result += f"{indent}{indent_base}<i>Collocations: {', '.join(sense.collocations)}</i>\n"
        if level < SUBSENSE_MAX_DEPTH:
            for idx, subsense in enumerate(sense.subsenses, start=1):
                result += f"{indent}{indent_base}<b>{idx}.</b> " + render_sense(subsense, level + 1, example_requested, synonyms_requested, antonyms_requested, collocations_requested, indent_base)
        return result

    message_parts = []
    lexeme_number = 0
    buttons_used = context.user_data.get(UserData.USED_BUTTONS, [])
    definitions_requested = context.user_data.get(UserData.DEFINITIONS_REQUESTED, 1)
    example_requested = Button.EXAMPLES in buttons_used
    synonyms_requested = Button.SYNONYMS in buttons_used
    antonyms_requested = Button.ANTONYMS in buttons_used
    collocations_requested = Button.COLLOCATIONS in buttons_used

    lexeme_amount = entry.lexeme_amount()
    single_lexeme = lexeme_amount == 1
    word = entry.etymologies[0].lexemes[0].lemma

    message_parts.append(f"Redirected from <b>{entry.redirected_from}</b>\n\n" if entry.redirected_from else "")
    message_parts.append(f"\"{word}\":\n\n")

    for etymology_idx, etymology in enumerate(entry.etymologies, start=1):
        etymology_header = f"<b><u>Etymology {roman_numerals.get(etymology_idx, etymology_idx)}</u></b>\n" if not chosen_lexeme_id and len(entry.etymologies) > 1 else ""
        if chosen_lexeme_id:
            chosen_lexeme = entry.get_lexeme_by_index(chosen_lexeme_id - 1)
            etymology_header += f"<b>{chosen_lexeme.part_of_speech.title()}</b>\n"

        etymology_content = []
        for lexeme in etymology.lexemes:
            lexeme_number += 1
            if chosen_lexeme_id and lexeme_number != chosen_lexeme_id:
                continue

            part_of_speech = f"{lexeme.part_of_speech.title()}"
            lexeme_text = ""

            if not chosen_lexeme_id and not single_lexeme:
                definition = f"({', '.join(lexeme.senses[0].labels)}) {lexeme.senses[0].definition}" if lexeme.senses[0].labels else lexeme.senses[0].definition
                lexeme_text += f"<b>{lexeme_number}. </b><b>{part_of_speech}</b>\n{definition}\n"
            else:
                for sense_number, sense in enumerate(lexeme.senses[:definitions_requested], start=1):
                    lexeme_text += f"<b>{sense_number}.</b> " + render_sense(sense, 0, example_requested, synonyms_requested, antonyms_requested, collocations_requested) + "\n"
            etymology_content.append(lexeme_text + "\n")

        if etymology_content:
            message_parts.append(etymology_header + "".join(etymology_content))

    complete_message = "".join(message_parts) or localization.get(Phrases.WORD_NOT_FOUND)
    return complete_message, lexeme_amount

async def refresh_message(update:  Update, context: ContextTypes.DEFAULT_TYPE, new: bool = False) -> None:
    localization = select_localization(update, context)
    used_buttons = context.user_data.get(UserData.USED_BUTTONS, [])
    entry: Entry = context.user_data.get(UserData.ENTRY, Entry())

    if not entry.entry:
        return await update.message.reply_text(localization.get(Phrases.WORD_NOT_FOUND))

    chosen_lexeme = None
    for button in used_buttons:
        if Button.is_lexeme(button):
            chosen_lexeme = int(button.split('-')[1])
            break

    message_text, lexeme_amount = build_message_text(context, entry, chosen_lexeme, localization)
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

async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[UserData.USED_BUTTONS] = []
    context.user_data[UserData.DEFINITIONS_REQUESTED] = 1

    await refresh_message(update, context)

async def close_markup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[UserData.USED_BUTTONS] = []
    await update.callback_query.edit_message_reply_markup(reply_markup=None)

async def definitions_border_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

SPECIAL_BUTTON_CALLBACKS = {
    Button.MORE_DEFINITIONS: more_definitions_callback,
    Button.LESS_DEFINITIONS: less_definitions_callback,
    Button.BACK: back_callback,
    Button.CLOSE: close_markup,
    Button.DEFINITIONS_BORDER: definitions_border_callback,
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
        # BotCommand("random", localization.get(Phrases.COMMAND_RANDOM)),
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
    if not token:
        raise ValueError("Bot token not found. Please set TELEGRAM_BOT_TOKEN in your environment variables.")

    PORT = int(os.environ.get("PORT", 8000))
    HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME", "your-heroku-app-name")
    WEBHOOK_URL = f"https://{HEROKU_APP_NAME}.herokuapp.com/{token}"
    debug = os.getenv("DEBUG", False)
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

    if debug:
        print("Running in polling mode")
        application.run_polling()
    else:
        print(f"Webhook URL: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=token,
            webhook_url=WEBHOOK_URL
        )


if __name__ == "__main__":
    main()
import asyncio
import logging
import re
import os


from contextlib import suppress
from datetime import datetime, timedelta
from idlelib.window import add_windows_to_menu
from time import time_ns

from decouple import config
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums.parse_mode import ParseMode
from aiogram.enums.chat_member_status import ChatMemberStatus


TOKEN = config('TOKEN')

logging.basicConfig(level=logging.INFO)


bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

router = Router()
router.message.filter(F.chat.type != "private")


@dp.message(F.chat.type == 'private')
async def private(message: types.Message):
    await message.reply("<b>Бот работает только в группах!</b>")


async def is_admin(message, bot):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    bot = await bot.get_chat_member(message.chat.id, bot.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] or bot.status != ChatMemberStatus.ADMINISTRATOR:
        return False
    return True

def parse_time(time: str | None):
    if not time:
        return None

    re_match = re.match(r"(\d+)([a-z])", time.lower().strip())
    now_datetime = datetime.now()

    if re_match:
        value = int(re_match.group(1))
        unit = re_match.group(2)

        match unit:
            case "s" : time_delta = timedelta(seconds=value)
            case "h" : time_delta = timedelta(hours=value)
            case "d" : time_delta = timedelta(days=value)
            case "w" : time_delta = timedelta(weeks=value)
            case _: return None
    else:
        return None

    new_datetime = now_datetime + time_delta
    return new_datetime

@router.message(Command("ban"))
async def func_ban(message: types.Message, command=CommandObject):
    reply_message = message.reply_to_message

    if not reply_message or not await is_admin(message, bot):
        await message.reply("<b> Произошла ошибка!</b>")
        return

    date = parse_time(command.args)
    mention = reply_message.from_user.mention_html(reply_message.from_user.first_name)

    with suppress(TelegramBadRequest):
        await bot.ban_chat_member(chat_id=message.chat.id,
                                  user_id=reply_message.from_user.id,
                                  until_date=date)
        await message.answer(f"Пользователь <b>{mention}</b> был заблокирован!")


@router.message(Command("mute"))
async def func_mute(message: types.Message, command: CommandObject, bot: Bot):
    reply_message = message.reply_to_message

    if not reply_message or not await is_admin(message, bot):
        await message.reply("<b> Произошла ошибка!</b>")
        return

    date = parse_time(command.args)
    mention = reply_message.from_user.mention_html(reply_message.from_user.first_name)

    with suppress(TelegramBadRequest):
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=reply_message.from_user.id,
                                       until_date=date, permissions=types.ChatPermissions(can_send_messages=False))
        await message.answer(f"Пользователь <b>{mention}</b> был заглушен!")


@router.message(Command("unmute"))
async def func_unmute(message: types.Message, command: CommandObject, bot: Bot):
    reply_message = message.reply_to_message

    if not reply_message or not await is_admin(message, bot):
        await message.reply("<b> Произошла ошибка!</b>")
        return

    mention = reply_message.from_user.mention_html(reply_message.from_user.first_name)

    await bot.restrict_chat_member(chat_id=message.chat.id,
                                   user_id=reply_message.from_user.id,
                                   permissions=types.ChatPermissions(can_send_messages=True,
                                                                     can_send_other_messages=True))
    await message.answer(f"Все ограничения с пользователя <b>{mention}</b> были сняты!")



@router.message(Command('unban'))
async def func_unban(message: types.Message, bot: Bot):
    reply_message = message.reply_to_message

    if not reply_message or not await is_admin(message, bot):
        await message.reply('<b>Произошла ошибка!</b>')
        return

    await bot.unban_chat_member(chat_id=message.chat.id,
                                user_id=reply_message.from_user.id,
                                only_if_banned=True)
    await message.answer('Блокировка была снята!')





async def main():
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
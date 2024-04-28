from aiogram import Dispatcher, Bot, types
from configs import API_TOKEN
import strings as strs
from model import ThemeModel, ModelFeedbackType, ModelFeedback
import asyncio
from database import get_exitsting_user, add_user, add_session, get_answer_by_id

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
qa_model = ThemeModel()

message_history = {}
lock = asyncio.Lock()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username

    exist = await get_exitsting_user(user_id)
    if exist is None:
        await add_user(user_id, username)
    async with lock:
        message_history[user_id] = []
    await message.reply(strs.introduction)


@dp.message_handler()
async def echo(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    async with lock:
        if user_id in message_history:
            message_history[user_id].append(text)
        else:
            message_history[user_id] = [text]

    decision = await qa_model(message_history[user_id])

    text = await get_answer_by_id(int(decision.data))

    if decision.feedback_type == ModelFeedbackType.end_point:
        async with lock:
            if user_id in message_history:
                await add_session(user_id, message_history[user_id])
                message_history[user_id] = []
        await message.answer(text)
    elif decision.feedback_type == ModelFeedbackType.continue_point:
        await message.answer(text)
    elif decision.feedback_type == ModelFeedbackType.no_class_point:
        await message.answer(strs.invite_operator)

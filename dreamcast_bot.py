import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram import F
import challonge
from datetime import datetime, timezone, timedelta
import sqlite3

from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "6965505332:AAEUx-z2iBk2bEe6fizyuqlnT7AEfoh0ha8"

# Установка учетных данных Challonge
TOURNAMENT_ID = "14341335"
challonge.set_credentials("Sla1mer", "zVCFWkhItCVtQ2mUOFSbeBBsEQdbwbI36652E5g7")

# Получение информации о всех участниках (командах) турнира
participants = challonge.participants.index(TOURNAMENT_ID)

# Создание словаря для хранения названий команд
team_names = {participant["group_player_ids"][0]: participant["name"] for participant in participants}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")

dp = Dispatcher()

conn = sqlite3.connect('forecasts.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS user_forecasts
             (username TEXT, match_id INTEGER, select_team TEXT, PRIMARY KEY (username, match_id, select_team))''')

conn.commit()


# Функция для добавления прогноза пользователя в базу данных
def add_forecast(username, match_id, select_team):
    c.execute("INSERT INTO user_forecasts (username, match_id, select_team) VALUES (?, ?, ?)", (username, match_id, select_team))
    conn.commit()

def get_user_forecasts(username):
    c.execute("SELECT match_id FROM user_forecasts WHERE username = ?", (username,))
    forecasts = c.fetchall()
    return [forecast[0] for forecast in forecasts]

def get_selected_team_forecasts(username, match_id):
    c.execute("SELECT select_team FROM user_forecasts WHERE username = ? AND match_id = ?", (username, match_id))
    forecasts = c.fetchone()
    return forecasts


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Начать делать прогнозы")],
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Нажмите на кнопку")

    await message.answer("Привет! Я бот студии Dreamcast для прогнозирования результатов матчей турнира."
                         "\nДля прогнозирования нажмите кнопку <b>\"Начать делать прогнозы\"</b>",
                         reply_markup=keyboard)


@dp.message(F.text.lower() == "начать делать прогнозы")
async def cmd_main_menu(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Сделать прогноз")],
        [types.KeyboardButton(text="Посмотреть историю своих прогнозов")]
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие")


    await message.answer("Выберите действие:", reply_markup=keyboard)

@dp.message(F.text.lower() == "посмотреть историю своих прогнозов")
async def cmd_check_history_forecast(message: types.Message):
    matches = get_user_forecasts(message.from_user.username)

    result_str = "История ваших прогнозов:\n\n"

    for match in matches:
        info_match = challonge.matches.show(TOURNAMENT_ID, match)
        print(info_match)
        print()

        player1_name = team_names.get(info_match["player1_id"], "Unknown")
        player2_name = team_names.get(info_match["player2_id"], "Unknown")

        selected_team = get_selected_team_forecasts(message.from_user.username, match)[0]

        match_result = "Матч еще не состоялся"
        if info_match.get("winner_id") is not None:
            winner_name = team_names.get(info_match["winner_id"], "Unknown")
            if selected_team == winner_name:
                match_result = "Прогноз успешен!"
            else:
                match_result = "Прогноз провалился"

        match_info_str = f"Матч: {player1_name} vs {player2_name}\nПрогноз: {selected_team}\nРезультат: {match_result}\n\n"

        result_str += match_info_str

    await message.answer(result_str)
    await cmd_main_menu(message)


@dp.message(F.text.lower() == "сделать прогноз")
async def cmd_forecast_menu(message: types.Message):
    matches = challonge.matches.index(TOURNAMENT_ID)

    now = datetime.now()
    now = now.astimezone(timezone(timedelta(hours=2)))

    scheduled_matches = [match for match in matches if
                         match.get("scheduled_time") is not None and
                         match.get("scheduled_time").date() == now.date() and
                         match.get("scheduled_time") > now]

    scheduled_matches.sort(key=lambda x: x["started_at"])

    user_name = message.from_user.username
    user_forecasts = get_user_forecasts(user_name)
    print(get_user_forecasts(user_name))

    buttons = []
    for match in scheduled_matches:
        match_id = match.get("id")
        if match_id not in user_forecasts:
            player1_name = team_names.get(match.get("player1_id"), "Unknown")
            player2_name = team_names.get(match.get("player2_id"), "Unknown")
            buttons.append([types.KeyboardButton(text=f"Прогноз - {player1_name} vs {player2_name} : {match_id}")])

    buttons.append([types.KeyboardButton(text="Назад в главное меню")])

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Нажмите на кнопку",
        row_width=1)

    if len(buttons) > 1:
        await message.answer("Выберите матч для прогнозирования:", reply_markup=keyboard)
    else:
        await message.answer('На сегодня вы сделали всевозможные прогнозы. Ожидайте появления новых матчей.\n\nУзнать последнюю информацию о матчах и мероприятиях вы можете у нас в Telegram канале <a href="https://t.me/+YhoXcckX8INmMWIy">Dreamcast</a>', reply_markup=keyboard)
        await cmd_main_menu(message)


@dp.message(F.text.lower() == "назад в главное меню")
async def back_main_menu(message: types.Message):
    await cmd_main_menu(message)

@dp.message(F.text.lower().startswith('прогноз'))
async def cmd_forecast_match(message: types.Message):
    str_list = message.text.split(" - ")

    buttons = []

    team1 = str_list[1].split(" vs ")[0]
    team2 = str_list[1].split(" vs ")[1].split(" : ")[0]
    match_id = str_list[1].split(" vs ")[1].split(" : ")[1]

    buttons.append([types.KeyboardButton(text=f"Команда {team1} - Match ID {match_id}")])
    buttons.append([types.KeyboardButton(text=f"Команда {team2} - Match ID {match_id}")])
    buttons.append([types.KeyboardButton(text=f"Назад в выбор матчей")])

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите команду которая по вашему мнению победит:",
        row_width=1)

    await message.answer("Выберите команду которая по вашему мнению победит:", reply_markup=keyboard)

@dp.message(F.text.lower() == "назад в выбор матчей")
async def back_forecast_match(message: types.Message):
    await cmd_forecast_menu(message)

@dp.message(F.text.lower().startswith('команда'))
async def cmd_forecast_team(message: types.Message):
    str_list = message.text.split("-")


    team = str_list[0].split("Команда ")[1].rstrip()
    match_id = str_list[1].split(" ")[3]
    print(message.from_user.username)

    add_forecast(message.from_user.username, match_id, team)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Twitch", url="https://www.twitch.tv/kbkcup")
    )
    builder.row(types.InlineKeyboardButton(
        text="Оф. Telegram канал Dreamcast",
        url="https://t.me/+YhoXcckX8INmMWIy")
    )

    await message.answer(f"Вы выбрали команду {team}.\n\nПосмотреть матчи вы можете на нашем Twitch канале.\n\nЧто бы не пропускать последние новости Dreamcast, подпишитесь на наш Telegram канал", reply_markup=builder.as_markup())
    await cmd_main_menu(message)
# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
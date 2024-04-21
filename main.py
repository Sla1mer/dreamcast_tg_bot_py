import telebot
from telebot import types
import challonge
from datetime import datetime, timezone, timedelta

BOT_TOKEN = "6965505332:AAEUx-z2iBk2bEe6fizyuqlnT7AEfoh0ha8"

# Установка учетных данных Challonge
TOURNAMENT_ID = "14341335"
challonge.set_credentials("Sla1mer", "zVCFWkhItCVtQ2mUOFSbeBBsEQdbwbI36652E5g7")

# Создание объекта бота
bot = telebot.TeleBot(BOT_TOKEN)

# Получение информации о турнире
tournament = challonge.tournaments.show(TOURNAMENT_ID)

# Получение информации о всех участниках (командах) турнира
participants = challonge.participants.index(TOURNAMENT_ID)

# Создание словаря для хранения названий команд
team_names = {participant["group_player_ids"][0]: participant["name"] for participant in participants}

# Получение информации о всех матчах турнира
matches = challonge.matches.index(TOURNAMENT_ID)

# Создаем словарь для хранения прогнозов пользователей
user_forecasts = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для прогнозирования результатов матчей турнира. "
                                      "Для прогнозирования нажмите /forecast.")


@bot.message_handler(commands=['forecast'])
def send_forecast(message):
    now = datetime.now()
    now = now.astimezone(timezone(timedelta(hours=2)))

    scheduled_matches = [match for match in matches if
                         match["scheduled_time"] is not None and match["scheduled_time"] > now]
    scheduled_matches.sort(key=lambda x: x["started_at"])

    # Фильтруем матчи, исключая те, на которые пользователь уже сделал прогноз
    chat_id = message.chat.id
    user_forecasted_matches = user_forecasts.get(chat_id, [])
    scheduled_matches = [match for match in scheduled_matches if str(match['id']) not in user_forecasted_matches]

    if len(scheduled_matches) == 0:
        bot.send_message(message.chat.id, "На сегодня прогнозы закончены. Спасибо!")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for match in scheduled_matches:
        player1_name = team_names.get(match["player1_id"], "Unknown")
        player2_name = team_names.get(match["player2_id"], "Unknown")
        callback_data = f"forecast_{match['id']}"
        button_text = f"{player1_name} vs {player2_name}"
        button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
        keyboard.add(button)

    bot.send_message(message.chat.id, "Выберите матч для прогнозирования:", reply_markup=keyboard)


@bot.callback_query_handler(lambda call: call.data.startswith('forecast_'))
def handle_forecast_button(call):
    match_id = call.data.split('_')[1]

    selected_match = next((match for match in matches if str(match["id"]) == match_id), None)

    if selected_match is None:
        bot.send_message(call.message.chat.id, "Матч не найден.")
        return

    player1_id = selected_match['player1_id']
    player2_id = selected_match['player2_id']
    player1_name = team_names.get(player1_id, "Unknown")
    player2_name = team_names.get(player2_id, "Unknown")

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton(player1_name, callback_data=f"result_{match_id}_{player1_id}_{player2_id}")
    button2 = types.InlineKeyboardButton(player2_name, callback_data=f"result_{match_id}_{player2_id}_{player1_id}")
    keyboard.add(button1, button2)

    bot.send_message(call.message.chat.id,
                     f"Вы выбрали матч: {player1_name} vs {player2_name}. Прогнозируйте результат.",
                     reply_markup=keyboard)


@bot.callback_query_handler(lambda call: call.data.startswith('result_'))
def handle_forecast_result_button(call):
    data_parts = call.data.split('_')
    match_id = data_parts[1]
    team_selected = data_parts[2]
    team_enemy = data_parts[3]

    user_id = f"@{call.from_user.username}" if call.from_user.username else str(call.from_user.id)

    forecast_message = f"User {user_id} made a forecast for the match  {team_names.get(int(team_selected))} vs {team_names.get(int(team_enemy))}: {team_names.get(team_selected, 'Unknown')}\n"
    bot.send_message(747551551, forecast_message)

    bot.send_message(call.message.chat.id,
                     f"Вы выбрали команду {team_names.get(int(team_selected), 'Unknown')}.\n\nПосмотреть матчи вы можете на нашем Twitch канале https://www.twitch.tv/kbkcup.\n\nА так же подписывайтесь на наш Telegram канал. Там публикуются самые последние новости о турнирнах. https://t.me/+YhoXcckX8INmMWIy")

    if call.message.chat.id not in user_forecasts:
        user_forecasts[call.message.chat.id] = []
    user_forecasts[call.message.chat.id].append(match_id)

    # Отправляем обратно меню выбора матчей для прогноза
    send_forecast(call.message)


# Функция для отправки меню выбора команд для прогноза
def send_teams_menu(chat_id, match_id):
    # Проверяем, делал ли пользователь уже прогноз для этого матча
    if chat_id in user_forecasts and match_id in user_forecasts[chat_id]:
        bot.send_message(chat_id, "Вы уже сделали прогноз для этого матча.")
        return

    # Создаем клавиатуру с меню выбора команд
    keyboard = types.InlineKeyboardMarkup()

    # Добавляем кнопки для каждой команды
    for team_id, team_name in team_names.items():
        keyboard.add(types.InlineKeyboardButton(team_name, callback_data=f"forecast_result_{match_id}_{team_id}"))

    # Отправляем сообщение с клавиатурой
    bot.send_message(chat_id, f"Выберите команду для матча с ID {match_id}:", reply_markup=keyboard)


# Запуск бота
bot.polling()



# import challonge
# from datetime import datetime, timezone, timedelta
# from telebot import *
# BOT_TOKEN = "6965505332:AAEUx-z2iBk2bEe6fizyuqlnT7AEfoh0ha8"
#
# bot = telebot.TeleBot(BOT_TOKEN)
#
# @bot.message_handler(commands=['start'])
# def send_welcome(message):
#     # Проверяем, что объект message не равен None
#     if message is not None:
#         # Создаем клавиатуру
#         keyboard = types.ReplyKeyboardMarkup(row_width=2)
#
#         # Создаем кнопки
#         btn1 = types.KeyboardButton("Кнопка 1")
#         btn2 = types.KeyboardButton("Кнопка 2")
#
#         # Добавляем кнопки на клавиатуру
#         keyboard.add(btn1, btn2)
#
#         # Отправляем сообщение с клавиатурой
#         bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)
#     else:
#         print("Сообщение None")
#
# # Обработчик нажатий на кнопки
# @bot.message_handler(func=lambda message: True)
# def handle_message(message):
#     if message.text == "Кнопка 1":
#         bot.send_message(message.chat.id, "Вы нажали кнопку 1")
#     elif message.text == "Кнопка 2":
#         bot.send_message(message.chat.id, "Вы нажали кнопку 2")
#
# # Запускаем бота
# bot.polling()


# TOURNAMENT_ID = "14341335"
#
# challonge.set_credentials("Sla1mer", "zVCFWkhItCVtQ2mUOFSbeBBsEQdbwbI36652E5g7")
#
# # Получаем информацию о турнире
# tournament = challonge.tournaments.show(TOURNAMENT_ID)
#
# # Получаем информацию о всех участниках (командах) турнира
# participants = challonge.participants.index(TOURNAMENT_ID)
#
# # Создаем словарь для хранения названий команд
# team_names = {participant["group_player_ids"][0]: participant["name"] for participant in participants}
#
# # Получаем информацию о всех матчах турнира
# matches = challonge.matches.index(TOURNAMENT_ID)
#
# def nearest_matches():
#     now = datetime.now()
#     now = now.astimezone(timezone(timedelta(hours=2)))
#
#     # # Преобразуем дату и время начала матчей в объекты datetime и приводим к offset-aware
#     scheduled_matches = [match for match in matches if
#                          match["scheduled_time"] is not None and match["scheduled_time"] > now]
#
#     scheduled_matches.sort(key=lambda x: x["started_at"], reverse=True)
#     print(scheduled_matches)
#
#     # Выводим информацию о каждом матче с названиями команд и счетом
#     for match in scheduled_matches:
#         # Получаем названия команд из словаря team_names
#         player1_name = team_names.get(match["player1_id"], "Unknown")
#         player2_name = team_names.get(match["player2_id"], "Unknown")
#
#         scores = match["scores_csv"] if match["state"] == "complete" else "Not played"
#         print("Match ID:", match["id"])
#         print("Player 1:", player1_name)
#         print("Player 2:", player2_name)
#         print("Scores:", scores)
#         print()

import telebot
import time, random, datetime
from telebot.types import Message, InlineKeyboardButton as IB, CallbackQuery
from telebot import types
from config import TOKEN
from text import *
from database import *
from fight import *

bot = telebot.TeleBot(TOKEN)
clear = types.ReplyKeyboardRemove()

temp = {}


@bot.message_handler(["start"])
def start(msg: Message):
    if is_new_player(msg):
        reg_1(msg)
        temp[msg.chat.id] = {"nick": None}
    else:
        pass


@bot.message_handler(["menu"])
def menu(msg: Message):
    try:
        print(temp[msg.chat.id])
    except KeyError:
        temp[msg.chat.id] = {}
    bot.send_message(msg.chat.id, menu1, reply_markup=clear)


@bot.message_handler(["square"])
def square(msg: Message):
    kb = types.ReplyKeyboardMarkup(True, True)
    kb.row("Тренировка", "Проверить силы")
    bot.send_message(msg.chat.id, "Ты на тренировочной площадке", reply_markup=kb)
    bot.register_next_step_handler(msg, reg_4)


@bot.message_handler(["home"])
def home(msg: Message):
    kb = types.ReplyKeyboardMarkup(True, True)
    kb.row("Пополнить ХП", "Передохнуть")
    bot.send_message(msg.chat.id, "Ты дома", reply_markup=kb)
    bot.register_next_step_handler(msg, reg_5)


@bot.message_handler(["stats"])
def stats(msg: Message):
    player = db.read_obj("user_id", msg.chat.id)
    t = f"{player.power} {player.nick}:\n" \
        f"Здоровье: {player.hp}❤️\n" \
        f"Урон: {player.dmg}⚔️\n" \
        f"LVL: {player.lvl}.{player.exp}⚜️\n\n" \
        f"Еда:\n"
    _, food = heals.read("user_id", msg.chat.id)

    for f in food:
        t += f"{f} ❤️{food[f][1]} — {food[f][0]}шт.\n"
    bot.send_message(msg.chat.id, t)
    time.sleep(3)
    menu(msg)


@bot.callback_query_handler(func=lambda call: True)
def callback(call: CallbackQuery):
    print(call.data)
    if call.data.startswith("food_"):
        a = call.data.split("_")
        eating(call.message, a[1], a[2])
        # Придётся ещё раз создать клавиатуру
        kb = telebot.types.InlineKeyboardMarkup()
        _, food = heals.read("user_id", call.message.chat.id)
        if food == {}:
            bot.send_message(call.message.chat.id, 'Кушать нечего', reply_markup=clear)
            menu(call.message)
            return
        for key in food:
            kb.row(IB(f"{key} {food[key][1]} hp. - {food[key][0]} шт.", callback_data=f"food_{key}_{food[key][1]}"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    if call.data.startswith("sleep_"):
        a = call.data.split("_")
        t = int(a[1]) // 2
        bot.send_message(call.message.chat.id, f"Ты лег отдыхать на {t} минут")
        time.sleep(t * 60)
        sleeping(call.message, a[1])
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)
    if call.data == '0':
        menu(call.message)
    if call.data == "menu":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        menu(call.message)
    if call.data == "workout":
        player = db.read("user_id", call.message.chat.id)
        player[4] += player[5] / 10
        player[4] = round(player[4], 4)
        db.write(player)
        bot.answer_callback_query(call.id, "Ты тренируешься и твоя сила увеличивается! \n"
                                           f"Теперь ты наносишь {player[4]}⚔️", True)


@bot.message_handler(["add_heal"])
def add_heal(msg: Message):
    _, food = heals.read("user_id", msg.chat.id)
    print(food)

    food["Пельмени"] = [15, 15]

    heals.write([msg.chat.id, food])
    bot.send_message(msg.chat.id, "Выдали еду твоему герою")


def eat(msg: Message):
    kb = types.InlineKeyboardMarkup()
    _, food = heals.read("user_id", msg.chat.id)
    if food == {}:
        bot.send_message(msg.chat.id, 'Кушать нечего', reply_markup=clear)
        menu(msg)
        return
    for key in food:
        if food[key][0] > 0:
            kb.row(IB(f"{key} {food[key][1]} hp. - {food[key][0]} шт.", callback_data=f"food_{key}_{food[key][1]}"))
    bot.send_message(msg.chat.id, "Выбери что будешь есть:", reply_markup=kb)


def eating(msg, ft, hp):
    _, food = heals.read("user_id", msg.chat.id)
    player = db.read("user_id", msg.chat.id)
    # Отнимаем хлеб
    if food[ft][0] == 1:
        del food[ft]
    else:
        food[ft][0] -= 1

    heals.write([msg.chat.id, food])

    # Добавляем ХП
    player[3] += int(hp)
    db.write(player)
    print("Игрок поел.")


def sleep(msg: Message):
    player = db.read("user_id", msg.chat.id)
    low = int(powers[player[2]][0] * player[5]) // 2 - player[3]
    high = int(powers[player[2]][0] * player[5]) - player[3]
    kb = telebot.types.InlineKeyboardMarkup()
    if low > 0:
        kb.row(IB(f"Вздремнуть — +{low}❤️", callback_data=f"sleep_{low}"))
    if high > 0:
        kb.row(IB(f"Поспать — +{high}❤️", callback_data=f"sleep_{high}"))
    if len(kb.keyboard) == 0:
        kb.row(IB('Спать не хочется', callback_data='0'))
    bot.send_message(msg.chat.id, "Выбери, сколько будешь отдыхать:", reply_markup=kb)


def sleeping(msg: Message, hp):
    player = db.read("user_id", msg.chat.id)
    player[3] += int(hp)
    db.write(player)
    print("Игрок поспал.")


def workout(msg: Message):
    kb = types.InlineKeyboardMarkup()
    kb.row(IB("Тренироваться", callback_data="workout"))
    kb.row(IB("Назад", callback_data="menu"))
    bot.send_message(msg.chat.id, "Жми, чтобы тренироваться!", reply_markup=kb)


def exam(msg: Message):
    player = db.read_obj("user_id", msg.chat.id)
    bot.send_message(msg.chat.id, f"Приготовься к испытанию, {player.nick}!", reply_markup=clear)
    time.sleep(2)
    start_exam(msg)


def start_exam(msg: Message):
    # random.choice((block, attack))(msg)
    block(msg)


def block(msg: Message):
    # Создаём список сторон и перемешиваем его
    sides = ["Слева", "Справа", "Сверху", "Снизу"]
    random.shuffle(sides)

    # Создаём клавиатуру
    kb = types.ReplyKeyboardMarkup(True, False)
    kb.row(sides[0], sides[3])
    kb.row(sides[1], sides[2])

    # Выбираем сторону удара и отправляем сообщение
    right = random.choice(sides)
    bot.send_message(msg.chat.id, f"Защищайся! Удар {right}!", reply_markup=kb)
    temp[msg.chat.id]["block_start"] = datetime.datetime.now().timestamp()
    bot.register_next_step_handler(msg, block_handler, right)


def block_handler(msg: Message, side: str):
    final = datetime.datetime.now().timestamp()
    player = db.read_obj("user_id", msg.chat.id)
    if final - temp[msg.chat.id]["block_start"] > player.dmg / 5 or side != msg.text:
        bot.send_message(msg.chat.id, "Твоя реакция слишком медлительна! Ты не готов!")
        time.sleep(5)
        menu(msg)
        return

    bot.send_message(msg.chat.id, "Ты справился, продолжаем!")
    block(msg)


def is_new_player(msg: Message):
    result = db.read_all()
    for user in result:
        if user[0] == msg.chat.id:
            return False
    return True


def reg_1(msg: Message):
    bot.send_message(msg.chat.id, text=reg % msg.from_user.first_name)
    bot.register_next_step_handler(msg, reg_2)


def reg_2(msg: Message):
    if not temp[msg.chat.id]["nick"]:
        temp[msg.chat.id]["nick"] = msg.text
    kb = types.ReplyKeyboardMarkup(True, True)
    kb.row("Вода", "Воздух")
    kb.row("Металл", "Земля")
    kb.row("Огонь", "Дерево")
    bot.send_message(msg.chat.id, "Выбери стихию:", reply_markup=kb)
    bot.register_next_step_handler(msg, reg_3)


def reg_3(msg: Message):
    temp[msg.chat.id]["power"] = msg.text
    hp, dmg = powers[msg.text]
    db.write([msg.chat.id, temp[msg.chat.id]["nick"], temp[msg.chat.id]["power"], hp, dmg, 1, 0])
    heals.write([msg.chat.id, {}])
    print("Пользователь добавлен в базу данных")
    bot.send_message(msg.chat.id, tren)
    time.sleep(2)
    menu(msg)


def reg_4(msg: Message):
    if msg.text == "Тренировка":
        workout(msg)
    if msg.text == "Проверить силы":
        exam(msg)


def reg_5(msg: Message):
    if msg.text == "Пополнить ХП":
        eat(msg)
    if msg.text == "Передохнуть":
        sleep(msg)


def reg_6(msg: Message):
    if msg.text == "Открыть статистику":
        stats(msg)


bot.polling(non_stop=True)

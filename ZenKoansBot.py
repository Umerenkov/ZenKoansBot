from telegram.ext import CommandHandler, Updater
import telegram
import sqlite3
import random
import logging

TOKEN = '622528019:AAHfg61qSS4KV2cGBEw_YV2TqiBdLyAL0Ro'
bot = telegram.Bot(TOKEN)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

help_message = '''\nВведи */new*, чтобы получить новую историю прямо сейчас,
Введи */help*, чтобы прочесть инструкцию снова,
Введи */enso*, чтобы обнулить прогресс и начать с начала. \n'''

greeting = '''*Здравствуй, путник!* \n
Этот бот предназначен для чтения книги "101 коан Дзен" в переводе Юрия Канчукова.
Раз в день он будет отправлять тебе одну случайно выбранную историю из книги. \n''' + help_message
greeting += '''\nЧерез несколько секунд тебе будет отправлено предисловие. \n'''

success = '''*Поздравляю! Ты прочёл всю книгу до конца.* \n 
Введи */enso*, чтобы обнулить прогресс и начать с начала. \n
Первая история будет прислана по расписанию или по команде */new*.'''


def foreword(context):
    # Предисловие. Текст хранится в нулевой строке koans.db
    conn = sqlite3.connect('koans.db')
    cur = conn.cursor()
    cur.execute('SELECT koan FROM Koans WHERE Number == 0')
    foreword = cur.fetchall()
    conn.close()

    job = context.job
    context.bot.send_message(job.context, text='*Предисловие* \n \n' + foreword[0][0],
                             parse_mode=telegram.ParseMode.MARKDOWN)


def start(update, context):
    # Вывод приветственного сообщения с командами
    chat_id = '@zenkoanseveryday'
    bot.send_message(chat_id=chat_id, text=greeting, parse_mode=telegram.ParseMode.MARKDOWN)

    # Вывод предисловия через 25 секунд после вызова функции
    job = context.job_queue.run_once(foreword, 25, context=chat_id)
    context.chat_data['job'] = job

    # Вывод нового коана каждые N секунд (рекомендуются значения, кратные 3600)
    job = context.job_queue.run_repeating(scheduled, 900, context=chat_id)
    context.chat_data['job'] = job


def scheduled(context):
    # Вывод запланированного коана
    job = context.job
    koan, complete = print_new()
    if complete:
        bot.send_message(job.context, text=success, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.send_message(job.context, text=koan, parse_mode=telegram.ParseMode.MARKDOWN)


def print_new():
    # Основная функция: выбирает и выводит случайную из непрочитанных коанов
    conn = sqlite3.connect('koans.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM Koans WHERE Done == 0')
    not_read = cur.fetchall()

    # Оставляем tuple из номеров коанов и их текстов, убираем предисловие
    not_read = [(item[0], item[1]) for item in not_read]
    not_read = not_read[1:]

    # Прочитаны ли все коаны? Да – печатает сообщение об успешно завершённом прочтении
    if len(not_read) == 0:
        complete = True
        return None, complete

    # Нет – выбирает случайное число от 1 до кол-ва непрочитанных, помечает выбранный как прочитанный, выводит выбранный
    else:
        rand_int = random.randint(1, len(not_read))
        selected = not_read[rand_int - 1][0]
        cur.execute('UPDATE Koans SET Done = ? WHERE Number = ?', (1, selected))
        conn.commit()
        conn.close()
        complete = False
        koan = '*' + str(selected) + '.* \t' + str(not_read[rand_int - 1][1])

    return koan, complete


def new(update, context):
    # Новый коан по вызову команды
    koan, complete = print_new()
    if complete:
        bot.send_message(chat_id='@zenkoanseveryday', text=success, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id='@zenkoanseveryday', text=koan, parse_mode=telegram.ParseMode.MARKDOWN)


def enso(update, context):
    # Обнуление прогресса прочитанного
    conn = sqlite3.connect('koans.db')
    cur = conn.cursor()
    cur.execute('UPDATE Koans SET Done = 0')
    conn.commit()
    conn.close()
    update.message.reply_text('⚠ Прогресс был обнулён.')


def help(update, context):
    # Вывод вспомогательного сообщения
    bot.send_message(chat_id='@zenkoanseveryday',
                     text=help_message, parse_mode=telegram.ParseMode.MARKDOWN)


def error(update, context):
    # Логи ошибок, вызванных апдейтами
    logger.warning('Update %s caused error %s', update, context.error)


def main():
    # Главная функция: объявление апдейтера и хэндлеров, начало опроса
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('new', new))
    dp.add_handler(CommandHandler('enso', enso))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == main():
    main()

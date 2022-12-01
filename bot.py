import telebot
from telebot import types
import fdb
import time

# Соединение
con = fdb.connect(dsn='', user='', password='', role='',charset='UTF8')
global address_short
# Объект курсора
cur = con.cursor()

bot = telebot.TeleBot("", parse_mode=None)
bot.remove_webhook()

#команда start
@bot.message_handler(commands=['start'])
def sendindication(message):
    msg = bot.send_message(message.chat.id, 'Пришлите лицевой счет!') 
    bot.register_next_step_handler(msg,order)
    
def order(message): 
    paccount = message.text
    try:
        cur.execute("")
        for row in cur:
            address_short=row[0]
            v_abonsid=row[1] 
        msg = bot.send_message(message.chat.id, 'Адрес: '+address_short+'. Верно ? Да/Нет') 
        bot.register_next_step_handler(msg,chek, v_abonsid,0)
    except Exception as e:
        bot.send_message(message.chat.id, 'Не правильный лицевой счет! '+str(e))
        sendindication(message)
    

#выбор счетчиков по полученому лицевому    
def chek(message,v_abonsid, nextmetr):
    if nextmetr == 0:
        pschek = message.text
        if pschek.upper() == 'ДА':
            cur.execute("")  
            data = cur.fetchall()
            keyboard = types.InlineKeyboardMarkup()
            for data_out in data: 
                keyboard.add(types.InlineKeyboardButton(text=str(data_out[1]), callback_data=str(data_out[0])+"|"+str(v_abonsid)))
            bot.send_message(message.chat.id, text="Счетчики:", reply_markup=keyboard)
        else:
            sendindication(message)
    else:
        cur.execute("")  
        data = cur.fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for data_out in data: 
            keyboard.add(types.InlineKeyboardButton(text=str(data_out[1]), callback_data=str(data_out[0])+"|"+str(v_abonsid)))
        bot.send_message(message.chat.id, text="Счетчики:", reply_markup=keyboard)

#ожидания нажатия на кнопки          
@bot.callback_query_handler(func=lambda call: True)
def longname(call):
    cml_id,v_abonsid=call.data.split("|")  
    msg = bot.send_message(call.from_user.id,'Пришлите показание и ожидайте ответа')
    bot.register_next_step_handler(msg,add,cml_id,v_abonsid)
    
#обработка переданых показаний    
def add(message,cml_id,v_abonsid):
    try:
        cur.execute("select coalesce(nullif(rmessage, ''), 'Показания переданы') from WEB_METER_CHARGE("+str(cml_id)+", "+message.text+", 1, 0, null, "+str(v_abonsid)+")")  
        results = cur.fetchall()
        for data_out in results: 
            bot.send_message(message.chat.id, '*'+str(data_out[0])+'*', parse_mode='Markdown')
        con.commit()
        chek(message, v_abonsid, 1)
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка передачи показаний! '+str(e))
        chek(message, v_abonsid, 1)

#реакций на ввод текста до выполнения комманд
@bot.message_handler(content_types=['text'])   
def mess(message):
    bot.send_message(message.from_user.id, '/start - передача показаний')
    
  
if __name__ == '__main__':
    bot.infinity_polling()
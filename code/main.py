import os
import sys
import csv
import logging
import threading
import datetime
from time import sleep
from telegram import ( Bot, ParseMode, Update )
from telegram.ext import ( Updater, CommandHandler, MessageHandler, Filters, CallbackContext )

import ib
import utils


if 'BOT_LOG_LEVEL' in os.environ and os.environ['BOT_LOG_LEVEL'] in ['DEBUG','INFO','WARNING','ERROR','CRITICAL']:
    logLevel = os.environ['BOT_LOG_LEVEL']
else:
    logLevel = 'INFO'

logging.basicConfig(
    filename='/tmp/alert-bot.log', 
    level=logging.getLevelName(logLevel),
    filemode='w', 
    format='%(asctime)s - [%(name)s][%(levelname)s] - %(message)s'
)

reportDict =	{
  'DIVS_DAILY': {
      'id':'377985'
  },
  'OPS_CUR_YEAR': {
      'id':'377354'
  },
  'DIVS_CUR_YEAR': {
      'id':'377884'
  },
  'CUR_POSITIONS': {
      'id':'378530'
  }

}

def main():

    logging.info("Initializing bot")

    # Get environment variables
    requiredEnv = [ 'TELEGRAM_BOT_TOKEN','TELEGRAM_USER_ID','IB_TOKEN' ]

    for envVar in requiredEnv:
        if envVar not in os.environ:
            logging.critical("Required environment variable not found %s", envVar)
            sys.exit()

    try:
        ibToken = os.environ['IB_TOKEN']
        telegramBotToken = os.environ['TELEGRAM_BOT_TOKEN']
        telegramUserId = os.environ['TELEGRAM_USER_ID']
    except Exception:
        logging.critical("Error getting environment variables",exc_info=True)
        sys.exit()

    # Initialize telegram bot
    bot_instance = Bot(token=telegramBotToken)
    updater = Updater(bot=bot_instance)
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler( CommandHandler( 'start', _cmdStart ) )
    dispatcher.add_handler( CommandHandler( 'list_reports', _cmdListReports ) )

    updater.start_polling()

    # Create loop
    th_update = threading.Thread(target=_sendUpdatesDaily,args=( bot_instance, telegramUserId, reportDict, ibToken ) )
    th_update.start()


def _cmdStart( bot: Bot, update: Update ):

    bot.send_message( chat_id=update.message.chat.id, text="Hi, I am alerter bot" )


def _cmdListReports( bot: Bot, update: Update ):
   
    textMessage = ""

    for reportName in reportDict:
        textMessage = textMessage + "\n- " + reportName

    bot.send_message( chat_id=update.message.chat.id, text=textMessage )


def _sendUpdatesDaily( bot, userId, reports, token="dummy" ):

    while True:

        todayStr = datetime.date.today().strftime('%Y%m%d')

        if os.path.isfile('/tmp/alert-bot.stat'):

            if (open('/tmp/alert-bot.stat','r').read()) != todayStr:
                
                _sendReport(bot,userId,'DIVS_DAILY',token)
                open('/tmp/alert-bot.stat','w').write(todayStr)

        else:

            _sendReport(bot,userId,'DIVS_DAILY',token)
            open('/tmp/alert-bot.stat','w').write(todayStr)            

        sleep(60)


def _sendReport( bot, userId, reportName, token="dummy" ):

    flexResult = ib.getIBFlex( token, reportDict[reportName]['id'] )

    if flexResult is None:
        bot.send_message(
            chat_id=userId,
            text="Error getting flex query result"
        )
        return
    else:
        flexCsv = csv.reader(flexResult.splitlines())

    line_count = 0
    fields = []
    for line in flexCsv:
        if len(line) > 0:
            if line_count == 0:
                for headerField in line:
                    fields.append(headerField)
            else:
                count = 0
                botMessage = ""
                for field in fields:
                    botMessage = botMessage + "*" + field + "*: " + line[count] + " \n"
                    count = count + 1

                bot.send_message(
                    chat_id=userId,
                    text=botMessage,
                    parse_mode=ParseMode.MARKDOWN
                )
        line_count = line_count + 1


if __name__ == "__main__":
    main()
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
  'DIVS_RETR_DAILY': {
      'id':'381072'
  },
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
  },
  'INTERESTS_CUR_YEAR': {
      'id':'380500'
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
    dispatcher.add_handler( CommandHandler( 'start', _cmdStart, pass_args=True ) )
    dispatcher.add_handler( CommandHandler( 'list_reports', _cmdListReports ) )
    dispatcher.add_handler( CommandHandler( 'get_report', _sendReportImg, pass_args=True ) )

    updater.start_polling()

    # Create loop
    th_update = threading.Thread(target=_sendUpdatesDaily,args=( bot_instance, telegramUserId, reportDict, ibToken ) )
    th_update.start()


def _cmdStart( bot, update, args ):

    user_says = " ".join(args)
    bot.send_message( chat_id=update.message.chat.id, text="User said: " + user_says )


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
                
                #_sendReport( bot, userId, 'DIVS_DAILY', token)
                _sendChargedDividends( bot, userId, 'DIVS_RETR_DAILY', token )
                open('/tmp/alert-bot.stat','w').write(todayStr)

        else:

            #_sendReport(bot,userId,'DIVS_DAILY',token)
            _sendChargedDividends( bot, userId, 'DIVS_RETR_DAILY', token )
            open('/tmp/alert-bot.stat','w').write(todayStr)            

        sleep(60)


def _sendReportImg( bot: Bot, update: Update, args: list ):

    reportName = args[0]

    logging.info( "Executing callback function [_sendReportImg] for report " + reportName )

    flexResult = ib.getIBFlex( os.environ['IB_TOKEN'], reportDict[reportName]['id'] )

    if flexResult is None:
        bot.send_message(
            chat_id=update.message.chat.id,
            text="Error getting flex query result"
        )
        return
    else:
        flexCsv = csv.reader(flexResult.splitlines())

        flexHtml = "<head><style>td { border: 1px solid; padding: 2px; text-align: center; }</style></head><table>"
        for line in flexCsv:
            htmlLine = "<tr>"
            for item in line:
                htmlLine = htmlLine + "<td>" + item
            flexHtml = flexHtml + htmlLine

        flexHtml = flexHtml + "</table>"

        imgPath = utils.htmlToImage(flexHtml)

        bot.send_photo(
            chat_id=update.message.chat.id, 
            photo=open(imgPath, 'rb'), 
            caption="IB Report " + reportName
        )


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

def _sendChargedDividends( bot, userId, reportName, token="dummy" ):

    flexResult = ib.getIBFlex( token, reportDict[reportName]['id'] )

    if flexResult is None:
        bot.send_message(
            chat_id=userId,
            text="Error getting flex query result"
        )
        return
    else:
        dividendsObj = utils.csvDividendsToObj( flexResult )

    if len(dividendsObj) > 0:

        bot.send_message(
                chat_id=userId,
                text="*Dividends found !!*",
                parse_mode=ParseMode.MARKDOWN
        )

        for dividend in dividendsObj:
            botMessage = ""
            for item in dividend:
                botMessage = botMessage + "*" + item + "*: " + dividend[item] + " \n"

            bot.send_message(
                chat_id=userId,
                text=botMessage,
                parse_mode=ParseMode.MARKDOWN
            )


def _sendChargedDividendsOld( bot, userId, reportName, token="dummy" ):

    flexResult = ib.getIBFlex( token, reportDict[reportName]['id'] )

    if flexResult is None:
        bot.send_message(
            chat_id=userId,
            text="Error getting flex query result"
        )
        return
    else:
        flexCsv = csv.reader(flexResult.splitlines())

    dataHeaders = []
    rowCount = 0

    for row in flexCsv:

        if rowCount == 0:
            for field in row:
                dataHeaders.append(field)
        else:
            if len(row) == len(dataHeaders):

                if row[dataHeaders.index('ActivityCode')] == 'DIV' and row[dataHeaders.index('LevelOfDetail')] == 'Currency':
                    
                    headerCount = 0
                    botMessage = ""

                    for header in dataHeaders:
                        botMessage = botMessage + "*" + header + "*: " + row[headerCount] + " \n"
                        headerCount = headerCount + 1

                    bot.send_message(
                        chat_id=userId,
                        text=botMessage,
                        parse_mode=ParseMode.MARKDOWN
                    )

        rowCount = rowCount + 1


if __name__ == "__main__":
    main()
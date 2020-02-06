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
import stock


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

reportDict = {
  'YEAR_FUNDS_STATEMENT': {
      'id':'388465'
  },
  'DAILY_FUNDS_STATEMENT': {
      'id':'389665'
  },
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
    dispatcher.add_handler( CommandHandler( 'stock', _cmdStockInfo, pass_args=True ) )
    #dispatcher.add_handler( CommandHandler( 'get_report', _sendReportImg, pass_args=True ) )

    updater.start_polling()

    # Create loop
    th_update = threading.Thread(target=_sendUpdatesHourly,args=( bot_instance, telegramUserId, reportDict, ibToken ) )
    th_update.start()


def _cmdStart( bot, update, args ):

    user_says = " ".join(args)
    bot.send_message( chat_id=update.message.chat.id, text="User said: " + user_says )

def _cmdStockInfo( bot, update, args ):

    ticker = " ".join(args)
    tickerPrice = stock.getPrice( ticker )
    bot.send_message( chat_id=update.message.chat.id, text="Stock price: " + str(tickerPrice) )

def _cmdListReports( bot: Bot, update: Update ):
   
    textMessage = ""

    for reportName in reportDict:
        textMessage = textMessage + "\n- " + reportName

    bot.send_message( chat_id=update.message.chat.id, text=textMessage )


def _sendUpdatesHourly( bot, userId, reports, token="dummy" ):

    while True:

        launchHourly = False

        todayHourStr = datetime.datetime.now().strftime('%Y%m%d%H')

        if os.path.isfile('/tmp/alert-bot.stat'):

            if (open('/tmp/alert-bot.stat','r').read()) != todayHourStr:

                launchHourly = True
                logging.debug( "Updating state file" )
                open('/tmp/alert-bot.stat','w').write(todayHourStr)

        else:

            launchHourly = True
            logging.debug( "Creating state file" )
            open('/tmp/alert-bot.stat','w').write(todayHourStr)


        if launchHourly and datetime.datetime.now().hour == 7:
            logging.info( "Executing daily launch for matched hour [7]" )
            _sendDividendsFundMoves( bot, userId, 'DAILY_FUNDS_STATEMENT', token )
            #_sendChargedDividends( bot, userId, 'DIVS_RETR_DAILY', token )

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
    else:
        logging.info( "No charged dividends for this day" )


def _sendDividendsFundMoves( bot, userId, reportName, token="dummy" ):

    flexResult = ib.getIBFlex( token, reportDict[reportName]['id'] )

    if flexResult is None:
        bot.send_message(
            chat_id=userId,
            text="Error getting flex query result"
        )
        return
    else:
        dividendsObj = utils.csvFundsToDividends( flexResult )

    if len(dividendsObj) > 0:

        bot.send_message(
                chat_id=userId,
                text="*Dividends funds moves found !!*",
                parse_mode=ParseMode.MARKDOWN
        )

        for symbol in dividendsObj:
            for date in dividendsObj[symbol]:

                botMessage = "*SYMBOL*: " + symbol + " \n*Date*: " + date + " \n"
                for item in dividendsObj[symbol][date]:
                    botMessage = botMessage + "*" + item + "*: " + str(dividendsObj[symbol][date][item]) + " \n"

                bot.send_message(
                    chat_id=userId,
                    text=botMessage,
                    parse_mode=ParseMode.MARKDOWN
                )

    else:
        logging.info( "No funds for dividends found" )



if __name__ == "__main__":
    main()
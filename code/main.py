import os
import sys
import requests
import urllib3
import csv
import logging
import threading
import datetime
from time import sleep
import xml.etree.ElementTree as ET
from prettytable import PrettyTable
from telegram import Bot
from telegram import ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters )


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
    updater.start_polling()

    start_handler = CommandHandler('getTable', _getTable)
    dispatcher.add_handler(start_handler)

    # Create loop
    th_update = threading.Thread(target=_sendUpdates,args=(bot_instance,telegramUserId))
    th_update.start()

    #flexResult = getIBFlexQuery( ibToken, ibFlexId )
    #flexTable = printCsvAsTable( flexResult )


def _getTable(bot,update):

    bot.send_message(
        chat_id=update.message.chat_id, 
        text="*bold* _italic_ `fixed width font` [link](http://google.com).",
        parse_mode=ParseMode.MARKDOWN
    )


def _sendUpdates(bot,userId):

    while True:

        todayStr = datetime.date.today().strftime('%Y%m%d')

        if os.path.isfile('/tmp/alert-bot.stat'):

            f = open('/tmp/alert-bot.stat','r')

            if f.read() != todayStr:

                f.close()
                f = open('/tmp/alert-bot.stat','w')

                if f.write(todayStr):
                    _sendReport(bot,userId,'DIVS_DAILY')

        else:

            f = open('/tmp/alert-bot.stat','w')

            if f.write(todayStr):
                _sendReport(bot,userId,'DIVS_DAILY')

        sleep(60)


def _sendReport(bot,userId,reportName):

    flexResult = getIBFlexQuery( os.environ['IB_TOKEN'], reportDict[reportName]['id'] )

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

def getIBFlexQuery( ibToken, ibFlexId ):

    # Get IB API info

    logging.debug("Obtaining report reference code with token %s and query ID %s",ibToken,ibFlexId)

    referenceParams = {'t': ibToken, 'q': ibFlexId, 'v': '3'}
    referenceEndpoint = 'https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest'

    try:
        referenceReq = requests.get(referenceEndpoint, params=referenceParams,timeout=5)
    except requests.exceptions.ConnectTimeout as timeoutExc:
        logging.critical("Timeout calling IB reference endpoint: %s" % referenceEndpoint )
        return
    except Exception:
        logging.critical("Error calling IB reference endpoint",exc_info=True)
        return

    if referenceReq.status_code == 200:
        referenceTree = ET.fromstring(referenceReq.text)
        referenceCode = referenceTree.findtext('ReferenceCode')
        if referenceTree.findtext('Status') != "Success":
            logging.critical("Got [%s] result from request [%s]: %s", referenceTree.findtext('Status'),referenceTree.findtext('ErrorCode'),referenceTree.findtext('ErrorMessage'))
            return
        else:
            logging.debug("Got reference code %s", referenceCode)
    else:
        logging.critical("Error getting reference code %d", referenceReq.status_code)
        return


    # Get IB FlexQuery result

    flexParams = {'t': ibToken, 'q': referenceCode, 'v': '3'}
    flexEndpoint = 'https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement'

    try:
        flexReq = requests.get(flexEndpoint, params=flexParams,timeout=5)
    except requests.exceptions.ConnectTimeout as timeoutExc:
        logging.critical("Timeout calling IB flexQuery endpoint: %s" % flexEndpoint )
        return
    except Exception:
        logging.critical("Error calling IB flexQuery endpoint",exc_info=True)
        return

    if flexReq.status_code == 200:
        # Check if response has XML format
        try:
            flexTree = ET.fromstring(flexReq.text)
            if referenceTree.findtext('Status') != "Success":
                logging.critical("Got [%s] result from request [%s]: %s",flexTree.findtext('Status'),flexTree.findtext('ErrorCode'),flexTree.findtext('ErrorMessage'))
                return
        except:
            pass

        return flexReq.text

    else:
        logging.critical("Error getting flex query result %d", flexReq.status_code)
        return


def printCsvAsTable( csvString ):

    flexCsv = csv.reader(csvString.splitlines())

    flexTable = PrettyTable()
    
    count = 0

    for line in flexCsv:
        if len(line) > 0:
            if count == 0:
                flexTable.field_names = line
            else:
                flexTable.add_row(line)

        count = count + 1

    return flexTable


if __name__ == "__main__":
    main()

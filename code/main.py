import os
import sys
import requests
import csv
import xml.etree.ElementTree as ET
from prettytable import PrettyTable
from telegram import Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters )


reportDict =	{
  'DIVS_DAILY': {
      'id':'377985',
      'fields': ['symbol','exdate','paydate','cur','gross','tax','net']
  }
}

def main():

    # Get environment variables

    requiredEnv = [ 'TELEGRAM_BOT_TOKEN','IB_TOKEN' ]

    for envVar in requiredEnv:
        if envVar not in os.environ:
            print("Required environment variable not found %s" % (envVar))
            sys.exit()

    try:
        ibToken = os.environ['IB_TOKEN']
        telegramBotToken = os.environ['TELEGRAM_BOT_TOKEN']
    except Exception:
        print("Error getting environment variables")
        sys.exit()

    # Initialize telegram bot
    bot_instance = Bot(token=telegramBotToken)
    updater = Updater(bot=bot_instance)
    dispatcher = updater.dispatcher
    updater.start_polling()

    start_handler = CommandHandler('getReport', getReport)
    dispatcher.add_handler(start_handler)

    #flexResult = getIBFlexQuery( ibToken, ibFlexId )
    #flexTable = printCsvAsTable( flexResult )


def getReport(bot, update):

    reportName = "DIVS_DAILY"

    flexResult = getIBFlexQuery( os.environ['IB_TOKEN'], reportDict[reportName]['id'] )
    flexCsv = csv.reader(flexResult.splitlines())

    for line in flexCsv:
        if len(line) > 0:

            count = 0
            botMessage = ""
            for field in reportDict[reportName]['fields']:
                botMessage = botMessage + field + ":" + line[count] + " "
                count = count + 1

            bot.send_message(
                chat_id=update.message.chat_id,
                text=botMessage
            )


def getIBFlexQuery( ibToken, ibFlexId ):

    # Get IB API info

    print("Obtaining report reference code with token %s and query ID %s" % (ibToken,ibFlexId))

    referenceParams = {'t': ibToken, 'q': ibFlexId, 'v': '3'}
    referenceReq = requests.get('https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest', params=referenceParams)

    if referenceReq.status_code == 200:
        referenceTree = ET.fromstring(referenceReq.text)
        referenceCode = referenceTree.findtext('ReferenceCode')
        if referenceTree.findtext('Status') != "Success":
            print("Got [%s] result from request [%s]: %s" % (referenceTree.findtext('Status'),referenceTree.findtext('ErrorCode'),referenceTree.findtext('ErrorMessage')))
            sys.exit()
        else:
            print("Got reference code %s" % (referenceCode))
    else:
        print("Error getting reference code %d" % (referenceReq.status_code))
        sys.exit()


    # Get IB FlexQuery result

    flexParams = {'t': ibToken, 'q': referenceCode, 'v': '3'}
    flexReq = requests.get('https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement', params=flexParams)

    if flexReq.status_code == 200:
        # Check if response has XML format
        try:
            flexTree = ET.fromstring(flexReq.text)
            if referenceTree.findtext('Status') != "Success":
                print("Got [%s] result from request [%s]: %s" % (flexTree.findtext('Status'),flexTree.findtext('ErrorCode'),flexTree.findtext('ErrorMessage')))
                sys.exit()
        except:
            pass

        return flexReq.text

    else:
        print("Error getting flex query result %d" % (flexReq.status_code))
        sys.exit()


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

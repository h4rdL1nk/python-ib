import utils
import ib
from sys import argv
import csv
import re
import json


secret_token = argv[1]

def test():

    # Get year funds report
    fundsReport = ib.getIBFlex( secret_token, '388465' )

    dividendsDict = {}

    fundsCsv = csv.reader(fundsReport.splitlines()) 

    row_count = 0
    for row in fundsCsv:
        if len(row) > 0:
            if row_count == 0:
                headers = []
                for header in row:
                    headers.append(header)

            if row[headers.index('LevelOfDetail')] == 'Currency':

                chargeDate = row[headers.index('Date')]
                desc = row[headers.index('ActivityDescription')]
                symbol = row[headers.index('Symbol')]
                exchange = row[headers.index('ListingExchange')]
                amount = row[headers.index('Amount')]
                currency = row[headers.index('CurrencyPrimary')]

                descMatches = re.match("(.*)\(([A-Z0-9]+)\).*([0-9]+.[0-9]+)",desc)

                if row[headers.index('ActivityCode')] == 'DIV':
                    if symbol not in dividendsDict: dividendsDict[symbol] = {}
                    if chargeDate not in dividendsDict[symbol]: dividendsDict[symbol][chargeDate] = {}
                    if currency not in dividendsDict[symbol][chargeDate]: dividendsDict[symbol][chargeDate]['Currency'] = currency

                    amount_per_share = descMatches.group(3)
                    shares = str((float(amount) / float(amount_per_share)))

                    dividendsDict[symbol][chargeDate]['NetAmount'] = amount
                    dividendsDict[symbol][chargeDate]['Shares'] = shares

                if row[headers.index('ActivityCode')] == 'FRTAX':
                    if symbol not in dividendsDict: dividendsDict[symbol] = {}
                    if chargeDate not in dividendsDict[symbol]: dividendsDict[symbol][chargeDate] = {}
                    if currency not in dividendsDict[symbol][chargeDate]: dividendsDict[symbol][chargeDate]['Currency'] = currency

                    dividendsDict[symbol][chargeDate]['Tax'] = amount

        row_count = row_count + 1

    print(json.dumps(dividendsDict))



if __name__ == "__main__":
    test()

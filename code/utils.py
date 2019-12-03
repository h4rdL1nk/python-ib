import os
import subprocess
import datetime
import csv
import re
from prettytable import PrettyTable

def csvToTable( csvString ):

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


def htmlToImage( htmlString ):

    convertImgTs = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    convertImgOrig = "/tmp/image-" + convertImgTs + ".html"
    convertImgDest = "/tmp/image-" + convertImgTs + ".jpg"

    open(convertImgOrig,'w').write(htmlString)
    
    #subprocess.run(["wkhtmltoimage",convertImgOrig,convertImgDest], check=True)
    proc = subprocess.Popen(["wkhtmltoimage",convertImgOrig,convertImgDest], stdout=subprocess.PIPE)
    output = proc.stdout.read()

    return convertImgDest


def csvDividendsToObj( csvString ):

    dividendsDict = []

    flexCsv = csv.reader(csvString.splitlines()) 

    row_count = 0
    for row in flexCsv:
        if len(row) > 0:
            if row_count == 0:
                headers = []
                for header in row:
                    headers.append(header)

            if row[headers.index('ActivityCode')] == 'DIV' and row[headers.index('LevelOfDetail')] == 'Currency':
                chargeDate = row[headers.index('Date')]
                desc = row[headers.index('ActivityDescription')]
                symbol = row[headers.index('Symbol')]
                amount = row[headers.index('Amount')]
                currency = row[headers.index('CurrencyPrimary')]

                matches = re.match("(.*)\(([A-Z0-9]+)\).*([0-9]+.[0-9]+)",desc)

                if matches:
                    isin = matches.group(2)
                    amount_per_share = matches.group(3)
                else:
                    isin = "n/a"
                    amount_per_share = "n/a"

                dividendObj = { 
                    "Date": chargeDate, 
                    "Symbol": symbol, 
                    "Shares": str((float(amount) / float(amount_per_share))), 
                    "Currency": currency, 
                    "AmountShare": str(amount_per_share), 
                    "AmountTotal": str(amount)
                }
                
                dividendsDict.append(dividendObj)

        row_count = row_count + 1

    return dividendsDict


def csvFundsToDividends( csvString ):

    dividendsDict = {}

    fundsCsv = csv.reader(csvString.splitlines()) 

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

                    amount_per_share = float(descMatches.group(3))
                    shares = round( (float(amount) / float(amount_per_share) ), 2 )

                    dividendsDict[symbol][chargeDate]['GrossAmount'] = float(amount)
                    dividendsDict[symbol][chargeDate]['Shares'] = shares

                    if 'Tax' in dividendsDict[symbol][chargeDate]: 
                        dividendsDict[symbol][chargeDate]['NetAmount'] = float(amount) - ( float(dividendsDict[symbol][chargeDate]['Tax']) * -1 )

                if row[headers.index('ActivityCode')] == 'FRTAX':
                    if symbol not in dividendsDict: dividendsDict[symbol] = {}
                    if chargeDate not in dividendsDict[symbol]: dividendsDict[symbol][chargeDate] = {}
                    if currency not in dividendsDict[symbol][chargeDate]: dividendsDict[symbol][chargeDate]['Currency'] = currency

                    dividendsDict[symbol][chargeDate]['Tax'] = ( float(amount) * -1 )

                    if 'GrossAmount' in dividendsDict[symbol][chargeDate]:
                        dividendsDict[symbol][chargeDate]['NetAmount'] = round( float(dividendsDict[symbol][chargeDate]['GrossAmount']) - ( float(amount) * -1 ), 2 )

        row_count = row_count + 1
    
    return dividendsDict


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
                desc = row[headers.index('ActivityDescription')]
                symbol = row[headers.index('Symbol')]
                amount = row[headers.index('Amount')]

                matches = re.match("(.*)\(([A-Z0-9]+)\).*([0-9]+.[0-9]+)",desc)

                if matches:
                    isin = matches.group(2)
                    amount_per_share = matches.group(3)
                else:
                    isin = "n/a"
                    amount_per_share = "n/a"

                dividendObj = { "symbol": symbol, "shares": str((float(amount) / float(amount_per_share))), "amountSh": str(amount_per_share), "amountTotal": str(amount)}
                dividendsDict.append(dividendObj)

        row_count = row_count + 1

    return dividendsDict
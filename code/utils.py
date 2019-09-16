import os
import subprocess
import datetime
import csv
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


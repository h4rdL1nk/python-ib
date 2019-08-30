import os
import sys
import requests
import csv
import xml.etree.ElementTree as ET
from prettytable import PrettyTable


# Get environment variables

requiredEnv = [ 'IB_TOKEN','IB_FLEX_ID' ]

for envVar in requiredEnv:
    if envVar not in os.environ:
        print("Required environment variable not found %s" % (envVar))
        sys.exit()

try:
    ibToken = os.environ['IB_TOKEN']
    ibFlexId = os.environ['IB_FLEX_ID']
except Exception:
    print("Error getting environment variables")
    sys.exit()


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

    flexCsv = csv.reader(flexReq.text.splitlines())

    flexTable = PrettyTable()
    
    count = 0

    for line in flexCsv:
        if len(line) > 0:
            if count == 0:
                flexTable.field_names = line
            else:
                flexTable.add_row(line)

        count = count + 1

    print(flexTable)

else:
    print("Error getting flex query result %d" % (flexReq.status_code))
    sys.exit()

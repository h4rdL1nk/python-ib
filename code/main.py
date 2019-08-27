import os
import sys
import requests
import xml.etree.ElementTree as ET


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

referenceParams = {'t': ibToken, 'q': ibFlexId, 'v': '3'}
referenceReq = requests.get('https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest', params=referenceParams)

if referenceReq.status_code == 200:
    referenceTree = ET.fromstring(referenceReq.text)
    referenceCode = referenceTree.findtext('ReferenceCode')
else:
    print("Error getting reference code %d" % (referenceReq.status_code))
    sys.exit()


# Get IB FlexQuery result

flexParams = {'t': ibToken, 'q': referenceCode, 'v': '3'}
flexReq = requests.get('https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement', params=flexParams)

if flexReq.status_code == 200:
    print(flexReq.text)
else:
    print("Error getting flex query result %d" % (flexReq.status_code))
    sys.exit()

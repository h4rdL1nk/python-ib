import requests
import logging
import urllib3
from time import sleep
import xml.etree.ElementTree as ET

def getIBFlex( ibToken, ibFlexId ):

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

    sleep(5)

    # Get IB FlexQuery result

    flexParams = {'t': ibToken, 'q': referenceCode, 'v': '3'}
    flexEndpoint = 'https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.GetStatement'

    retry = 4
    http_code = 0
    xml_status = ""

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
            xml_status = referenceTree.findtext('Status')

            while retry > 0 and xml_status != "Success":
                flexReq = requests.get(flexEndpoint, params=flexParams,timeout=5)
                flexTree = ET.fromstring(flexReq.text)
                xml_status = referenceTree.findtext('Status')
                retry = retry - 1

            if xml_status != "Success":
                logging.critical("Got [%s] result from request [%s]: %s after %d retries",flexTree.findtext('Status'),flexTree.findtext('ErrorCode'),flexTree.findtext('ErrorMessage'),retry)
                return

        except:
            pass

        return flexReq.text

    else:
        logging.critical("Error getting flex query result %d", flexReq.status_code)
        return
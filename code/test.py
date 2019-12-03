import utils
import ib
from sys import argv
import csv
import re
import json

def test( token ):

    # Get year funds report
    fundsReport = ib.getIBFlex( token, '388465' )

    fundsObject = utils.csvFundsToDividends( fundsReport )

    print(json.dumps(fundsObject))



if __name__ == "__main__":
    
    if len(argv) > 0:
        secret_token = argv[1]
    
    test(secret_token)
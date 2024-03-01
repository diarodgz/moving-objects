from astropy.time import Time
from astropy.coordinates import SkyCoord
import os
from collections import namedtuple
from astropy.table.table import Table, Row, Column
from backend.variables import ob_path

def read_ob(path: str):
    '''
    Receives the path where the OB.paf file is located,
    and returns a dictionary that contains all of the relevant
    instrument information and more. The keys are consistent 
    with the original file.

    --------------
    Parameters
    --------------

    path: str
    '''
    
    OB = {}
    
    try:
        with open(path) as file:
            data = file.readlines()
    except FileNotFoundError:
        msg = "Path not found."
        return msg
    else:
        for line in data:
            word = line.split()
            if word != []:
                # We set the first item in the list as a dict_key
                # And the content is what follows.
                OB[word[0]] = word[1].lstrip('"').rstrip('";')
    
        return OB


def read_eph(path: str):
    '''
    Receives the path of where the OB.eph file is located.
    Returns two dictionaries that contains the unprocessed information
    of the OB.eph file. 
    
    One dictionary, the 'desc' dictionary contains 
    only information pertaining to the target description, start and end date,
    and time step. The 'eph' dictionary  contains all the information regarding
    the ephemeris itself.

    --------------
    Parameters
    --------------

    path: str
    '''

    eph = {}
    eph_desc = {}

    i = 0
    j = 0
    
    try:
        with open(path) as file:
            data = file.readlines()
    except FileNotFoundError:
        msg = "Path not found."
        return msg
    else:
        for line in data:
            word = line.split()
            if len(word) > 1:
                # Items with these keys will contain the ephemeris information in it.
                if 'INS.EPHEM.RECORD' in word[0]:
                    rec = word[0] + f'.{i}'
                    eph[rec] = [x for x in word]
                    eph[rec].pop(0)

                    i += 1
                elif 'DESC' in word[0]:
                    desc = word[0] + f'.{j}'
                    eph_desc[desc] = [x for x in word]
                    eph_desc[desc].pop(0)
                    j += 1
                    
        return eph, eph_desc
    
def process_eph(eph: dict):
    '''
    Takes the unprocessed *ephemeris* information from the OB.eph file 
    and organizes it into a dictionary that's easier to understand. Returns a dict object.

    -------------
    Parameters
    -------------

    eph: dict.
    '''
    
    #keys = ['Date', 'RA', 'DEC']
    #units = ['Time', 'hh:mm:ss', 'dd:mm:ss']
    
    #eph_table = Table(names=keys, dtype=units)
    # Try to make astropy table later, easier to work with!
    
    clean_eph = {}
    
    # Clean strings (or at least, the ones that matter to us).
    for key in eph.keys():
        
        hh = eph[key][2].lstrip('"').rstrip(',')
        mra = eph[key][3].lstrip('"').rstrip(',')
        sra = eph[key][4].lstrip('"').rstrip(',')
        
        dd = eph[key][5].lstrip('"').rstrip(',')
        mdec = eph[key][6].lstrip('"').rstrip(',')
        sdec = eph[key][7].lstrip('"').rstrip(',')
        
        # Store DATE and RADEC information.
        RA = f"{hh}:{mra}:{sra}"
        DEC = f"{dd}:{mdec}:{sdec}"
        date = eph[key][0][:11].lstrip('"').rstrip(',') + ' ' + eph[key][0][13:].lstrip('"').rstrip(',')
        
        date_obj = Time(date, format='iso', scale='utc')
        
        Eph = namedtuple('Eph', ['date', 'ra', 'dec'])
        
        e = Eph(date_obj, RA, DEC)

        clean_eph[key] = e
    
    
    return clean_eph



def process_desc(eph: dict):
    '''
    Takes the unprocessed **description** information from the OB.eph file and organizes it into 
    a dictionary that's easier to understand. Returns a dict object.
    '''
    
    clean_desc = {}
    valid_keys = [
        'PAF.DESC.1', 
        'PAF.DESC.3', 
        'PAF.DESC.4',
        'PAF.DESC.5',
    ]
    
    for key in valid_keys:
        desc = ''
        for word in eph[key]:
            desc += word + ' '
            
        desc = desc.lstrip('"').rstrip(' "')    
        new_key = desc[:desc.find(':')].rstrip(' ') 
        clean_desc[new_key] = desc[desc.find(':') + 1:].lstrip(' ')
    
    return clean_desc

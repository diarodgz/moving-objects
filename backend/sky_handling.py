from backend.sky import Sky
from astropy.time import Time
from astroquery.mpc import MPC
from astroquery.vizier import Vizier
from tqdm import tqdm
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from urllib.parse import urlencode
import yaml
import os
import multiprocessing

config_path = os.path.join('settings', 'config.yml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)


def query(id, start_from, step, num_results, t_start, t_end):

    '''
    Generates the query from the Minor Planet Center according to the parameters
    input by the user.

    id: str. Minor planet ID.
    start_from: str. Date in YYYY-MM-DD format. Indicates the starting observing date.
    step: str. An integer followed by the unit, e.g. 5s, 10min, 1h, 7d.
    t_start: str. in YYYY-MM-DD hh:mm:ss format.
    t_end: str. in YYYY-MM-DD hh:mm:ss format.
    '''

    eph = MPC.get_ephemeris(id, start=start_from, step=step, number=num_results)

    time_start = Time(t_start, format='iso', scale='utc')
    time_end = Time(t_end, format='iso', scale='utc')
    
    time_mask = (eph['Date'] >= time_start) & (eph['Date'] <= time_end)
    eph_req = eph[time_mask]
    
    return eph_req

    
def sky_init(eph, fov, hips, catalog, filter):
    '''
    Creates a sky object for each region of the sky that the object will pass through
    acccording the requested ephemeris files.

    eph: astropy.Table that contains the requested ephemeris of the object.
    fov: int
    hips: str
    catalog: str
    filter: str
    '''

    if fov <= 1:
        fov += 1
    else:
        pass
    
    i = 0
    skys = []

    # Amplifies FOV by 1 arcminute to have search results.
        
    print(f'Using small FOV {fov}... Amplifying by 1 arcmin.')
    for RA, DEC, date in tqdm(zip(eph['RA'], eph['Dec'], eph['Date']), total=len(eph)):
        c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')
        v = Vizier(catalog=catalog, row_limit=-1, columns=['all'],
                column_filters=filter) # SDSS16
        result = v.query_region(coordinates=c, width=Angle(fov, u.arcminute), 
                                height=Angle(fov, u.arcminute), frame='icrs')
        sky = Sky(i, result, c, date, catalog, hips, fov)
        skys.append(sky)
        i += 1
        
    return skys

    
def sky_process(skys):
    '''
    Receives iterable with Sky objects and applies each method.
    skys: array of Sky objects
    fov: int
    '''
    for sky in tqdm(skys):
        sky.filter_detec()
        if not sky.no_sources:
            sky.store_radec()
            sky.separate()
        
        print(f'Sky {sky.num} has no sources: {sky.no_sources}')
        sky.set_query_params()
        #sky.img_query(fov / 2) # Divided by two because the image query takes a radius.

def query_sky_img(sky):
    '''
    Method that executes the img_query method in a Sky object.
    
    -------
    Parameters
    -------
    sky: instance of Sky.
    '''
    return sky.img_query()

def run_parallel_queries(skys):
    """
    Executes multiple HIPS queries in parallel using multiprocessing.

    -------
    Parameters:
    ---------
    query_params_list: list of Sky objects.
    """

    with multiprocessing.Pool(processes=len(skys)) as pool:
        results = pool.map(query_sky_img, skys)
    return results
        

def single_sky_query(ra, dec, fov, catalog, filter):

    '''
    Queries a single sky image in the given coordinates.
    -------
    Parameters
    --------
    ra: str
    dec: str
    fov: float
    '''

    if fov <= 1:
        fov += 1
    else:
        pass

    c = SkyCoord(f'{ra} {dec}', frame='icrs')
    v = Vizier(catalog=catalog, row_limit=-1, columns=['all'],
                column_filters=filter) 
    result = v.query_region(coordinates=c, width=Angle(fov, u.arcminute), 
                            height=Angle(fov, u.arcminute), frame='icrs')

    return result

def single_sky_flag():
    pass


def get_img(fov, ra, dec, hips, rot):
    
        '''
        fov: int.

        Takes the fov of the instrument and the central coordinates of the moving object and 
        querys a FITS file from the DSS.
        '''

        coord = SkyCoord(f"{ra} {dec}", unit=(u.hourangle, u.deg), frame='icrs')

        query_params = { 
         'hips': hips,
         'ra': coord.ra.value,
         'dec': coord.dec.value,
         'fov': (config['BG_FOV'] * u.arcmin).to(u.deg).value, # Consider reducing the FOV by half.
         'width': 1000, 
         'height': 1000,
         'rotation_angle': float(rot)
     }   

        url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'

        hdu = fits.open(url)[0] # Opening FITS file.


        wcs = WCS(hdu.header)

        img_data = hdu.data
        
        return coord, fov, wcs, img_data

def query_sky_object(sky_obj):
    return sky_obj.img_query()

def best_seen(skys):
    best_dates = []

    for sky in skys:
        flag = sky.flag_bright()
        if flag == 'no sources' or flag['dist'] >= 1 * u.arcmin:
            best_dates.append(sky)
        else:
            pass
    
    if best_dates != []:
        return f'The object is best seen from \
{best_dates[0].date.value} to {best_dates[len(best_dates) - 1].date.value}'
    else:
        return f'The object is best seen from dates before {skys[0].date.value}\nand after {skys[len(skys)-1].date.value}'

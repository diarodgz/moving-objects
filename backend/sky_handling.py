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
    '''
    
    i = 0
    skys = []

    if fov <= 1:
        # Amplifies FOV by 1 arcminute to have search results.
        print(f'Using small FOV {fov}... Amplifying by 1 arcmin.')
        for RA, DEC, date in tqdm(zip(eph['RA'], eph['Dec'], eph['Date']), total=len(eph)):
            c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')
            v = Vizier(catalog=catalog, row_limit=-1, columns=['all'],
                    column_filters=filter) # SDSS16
            result = v.query_region(coordinates=c, width=Angle(fov+1, u.arcminute), 
                                    height=Angle(fov+1, u.arcminute), frame='icrs')
            sky = Sky(i, result, c, date, catalog, hips, fov)
            skys.append(sky)
            i += 1
    else:
        for RA, DEC, date in tqdm(zip(eph['RA'], eph['Dec'], eph['Date']), total=len(eph)):
            c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')
            v = Vizier(catalog=catalog, row_limit=-1, columns=['all'],
                    column_filters=filter) 
            result = v.query_region(coordinates=c, width=Angle(fov, u.arcminute), 
                                    height=Angle(fov, u.arcminute), frame='icrs')
            sky = Sky(i, result, c, date, catalog, hips, fov)
            skys.append(sky)
            i += 1
        
    return skys

    
def sky_process(skys, fov):
    '''
    Receives iterable with Sky objects and applies each method.
    '''
    for sky in tqdm(skys):
        sky.filter_detec()
        if not sky.no_sources:
            sky.store_radec()
            sky.separate()
        
        print(f'Sky {sky.num} has no sources: {sky.no_sources}')
        sky.img_query(fov / 2) # Divided by two because the image query takes a radius.

        


def sky_query(coordinates, radius=None, fov=None):

    '''
    Queries sky images in the given coordinates.
    '''

    RA = [coordinates][0]
    DEC = [coordinates][1]

    c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')

    if fov is not None:

        v = Vizier(catalog='V/154', keywords=['optical'], row_limit=1000, columns=['all']) # SDSS16
        result = v.query_region(coordinates=c, width=Angle(fov, u.arcminute), 
                                    height=Angle(fov, u.arcminute), frame='icrs')
        
    elif radius is not None:

        v = Vizier(catalog='V/154', keywords=['optical'], row_limit=1000, columns=['all']) # SDSS16
        result = v.query_region(coordinates=c, radius=Angle(fov, u.arcminute), frame='icrs')


    return result


def get_img(fov, ra, dec):
    
        '''
        fov: int.

        Takes the fov of the instrument and the central coordinates of the moving object and 
        querys a FITS file from the DSS.
        '''

        coord = SkyCoord(f"{ra} {dec}", unit=(u.hourangle, u.deg), frame='icrs')

        query_params = { 
         'hips': 'DSS',
         'ra': coord.ra.value,
         'dec': coord.dec.value,
         'fov': (fov * u.arcmin).to(u.deg).value, # Consider reducing the FOV by half.
         'width': 500, 
         'height': 500 
     }   
        url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'

        hdu = fits.open(url) # Opening FITS file.
        hdu = hdu[0]

        wcs = WCS(hdu.header)

        img_data = hdu.data

        info = {
            'data': img_data,
            'wcs': wcs,
            'ra': coord.ra.value,
            'dec': coord.dec.value
        }
        
        return info

def flags(skys, cat):

    print("Flagging bright objects...")
    b_flag = list(map(lambda sky: sky.flag_bright() if not sky.no_sources else 'no sources', skys)) # Flags bright objects.
        
    print("Flagging objects within 0.5 arcmin...")
    dist_flag = list(map(lambda sky: sky.flag_dist(0.5 * u.arcmin) if not sky.no_sources else 'no sources', skys)) # Flags objects within a 0.5' radius.

    # We prepare an empty string to fill it with the brightness flags.
    b_notice = f""

    mag = config['CATALOG'][cat]['flag']

    for item in b_flag: # Goes through each flagged source for each patch of sky 
        if item != 'no sources': # Make sure that the sky isn't empty.
            b_notice += f'There is a {item["mag"]:.3f} {mag} source within \
    {item["dist"].to_string(unit=u.arcmin)} of the target on {item["date"]}\n'

    # Empty string to fill with distance info.
    dist_notice = f""

    # Filling empty string with information about distances.
    for item in dist_flag:
        if item is not 'no sources':
            dist_notice += f'There are {item["flagged"]} sources within \
    {item["thresh"]} of the target on {item["date"]}\n'
            
    return b_notice, dist_notice

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
        return f'The object is best seen from dates before {skys[0].date.value} and after {skys[len(skys)-1].date.value}'

# METHODS WILL NOW REQUIRE A PARAMETER CALLED "FOV" !!! ADJUST ACCORDINGLY
# NOTES:
# Allow option to change catalogue?
# Allow option to change frame?
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

    
def sky_init(eph, fov):
    '''
    Creates a sky object for each region of the sky that the object will pass through
    acccording the requested ephemeris files.

    eph: astropy.Table that contains the requested ephemeris of the object.
    '''
    
    i = 0
    skys = []

    for RA, DEC, date in tqdm(zip(eph['RA'], eph['Dec'], eph['Date']), total=len(eph)):
        c = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')
        v = Vizier(catalog='V/154', keywords=['optical'], row_limit=-1, columns=['all'],
                   column_filters={"gmag":"<21"}) # SDSS16
        result = v.query_region(coordinates=c, width=Angle(fov, u.arcminute), 
                                height=Angle(fov, u.arcminute), frame='icrs')
        sky = Sky(i, result, c, date)
        skys.append(sky)
        i += 1
        
    return skys

    
def sky_process(skys, fov):
    '''
    Receives iterable with Sky objects and applies each method.
    '''
    for sky in tqdm(skys):
        sky.filter_detec()
        sky.store_radec()
        sky.img_query(fov / 2) # Divided by two because the image query takes a radius.
        sky.separate()


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
         'hips': 'CDS/P/HLA/SDSSg',
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


# METHODS WILL NOW REQUIRE A PARAMETER CALLED "FOV" !!! ADJUST ACCORDINGLY
# NOTES:
# Allow option to change catalogue?
# Allow option to change frame?
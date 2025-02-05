from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from urllib.parse import urlencode
from urllib.parse import quote
from regions import CircleSkyRegion
import os
import yaml

config_path = os.path.join('settings', 'config.yml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)


'''
Contains everything necessary to generate sky objects 
and store their respective data.
'''


class Sky:
    def __init__(self, num: int, result, coords, date, catalog, hips, fov):
        
        '''
        A class for storing important information about each sky region.

        --------------
        Attributes
        --------------
        
        num: int, identifier for the Sky object.
        result: astroquery.utils.TableList object. Contains the initial result of the query.
        coords: astropy.coordinates.SkyCoord object.
        date: astopy.time.Time object.
        catalog: str, ID of CDS catalog to use.
        hips: str, ID of HIPS image survey to use.
        fovt: int, FOV of the instrument in arcmin.
        self.sources: Astropy table with filtered results. Astropy Table.
        self.source_ra: Iterable that contains the RA coordinates of ALL self.sources (deg)
        self.source_de: Iterable that contains the DEC coordinates of ALL self.sources (deg)
        self.distances: Iterable that contains the distance from the source to the center (deg)
        self.thresh: Astropy Quantity object that sets the radius of the flagged items.
        self.wcs: astropy.wcs.WCS object of the sky FITS
        self.flagged_ra: Iterable that contains the RA coordinates of the flagged items (deg)
        self.flagged_de: Iterable that contains the DE coordinates of the flagged items (deg)
        self.pix_region: regions.CircleSkyRegion object converted to pixels.
        self.img_data: 2D array of the image data from the FITS file.
        self.hdu: HDU object of the sky FITS file. 
        self.no_sources: boolean, determines whether or not there are any sources detected in the sky based on the Vizier query results.
        '''
        self.num = num 
        self.result = result
        self.coords = coords
        self.date = date
        self.catalog = catalog
        self.hips = hips
        self.fov = fov
        self.sources = None
        self.source_ra = [] 
        self.source_de = [] 
        self.distances = [] 
        self.thresh = None 
        self.wcs = None 
        self.flagged_ra = [] 
        self.flagged_de = [] 
        self.pix_region = None 
        self.img_data = None
        self.hdu = None
        self.no_sources = False
        
    def filter_detec(self):
        '''
        Takes itself and filters through the repeated detections by using the first field ID.
        Stores the filtered results to the attribute self.sources
        '''

        if self.result != []:
            s_id = config['CATALOG'][self.catalog]['source_id']
            detec_mask = (self.result[0][s_id] == self.result[0][s_id][0])
            source_table = self.result[0][detec_mask]
            self.sources = source_table
        else:
            self.no_sources = True
        
    def store_radec(self):
        '''
        Takes the RADEC coordinates (in degrees) stored in self.sources and separates them into
        self.source_ra and self.source_de to be able to plot them later.
        '''

        self.ra_key = config['CATALOG'][self.catalog]['ra']
        self.dec_key = config['CATALOG'][self.catalog]['dec']

        for RA, DEC in zip(self.sources[self.ra_key], self.sources[self.dec_key]):
            c_source = SkyCoord(f'{RA} {DEC}', frame='icrs', unit=(u.deg, u.deg))
            self.source_ra.append(c_source.ra.value)
            self.source_de.append(c_source.dec.value)
    
        
    def img_query(self, fov):
    
        '''
        fov: astropy Quantity object (arcmin or arcsec)

        Takes the fov of the instrument and the central coordinates of the moving object and 
        querys a FITS file from the DSS. Returns the image data
        '''

        query_params = { 
         'hips': config['HIPS_SURVEY'][self.hips],
         'ra': self.coords.ra.value, 
         'dec': self.coords.dec.value, 
         'fov': (config['BG_FOV'] * u.arcmin).to(u.deg).value, # Consider reducing the FOV by half.
         'width': 1000, 
         'height': 1000 
     }   
        url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'

        hdu = fits.open(url) # Opening FITS file.
        self.hdu = hdu[0]
        self.wcs = WCS(hdu[0].header)

        self.img_data = hdu[0].data
        
        # Check if image data is empty.
        
    def flag_bright(self):
        '''
        Takes itself and automatically checks for any bright independent of a radius. 
        In this case, it will search for that are similar to the brightest source in the image.
        Prints a message alerting the user of the coordinates of this objects, the date it will be
        found, and how far it is from the moving object, which band it's brightest in.
        '''
        
        if not self.no_sources: # If there are not detected sources in this sky patch, do not flag.
            # Search for top 5.
            top_5 = []
        
            # Allow option to search through each magnitude.
            mag = config['CATALOG'][self.catalog]['flag']

            # Brightest source in optical wavelength.
            b_mask = self.sources[mag] == min(self.sources[mag])
            brightest = self.sources[b_mask]

            # Handling multiple detections
            if len(brightest) > 0:
                ra_brite, dec_brite = brightest[self.ra_key][0], brightest[self.dec_key][0]
                # Magnitude of brightest object in the sky.
                b_mag = brightest[mag][0]
            else:
                ra_brite, dec_brite = brightest[self.ra_key], brightest[self.dec_key]
                b_mag = brightest[mag]

            # Distance from target.
            c_source = SkyCoord(f'{ra_brite} {dec_brite}', unit=(u.deg, u.deg), frame='icrs')

            b_dist = c_source.separation(self.coords)

            info = {
                'mag': b_mag,
                'ra': ra_brite,
                'dec': dec_brite,
                'dist': b_dist,
                'date': self.date
            }

            return info
        else:
            print(f'Sky at {self.date.value} has no sources.')
            return 'no sources'
    
    def flag_dist(self, thresh):
        '''
        thresh: Astropy Quantity object in arcminutes or arcseconds to define a 
        radius of a circle-shaped search region.
        
        Takes a circular region in the sky of radius "thresh", centered on the moving object 
        (or center sky coordinates) and detects whether or not there are sources 
        in this region. It adds all of the coordinates of sources that are in this region into 
        the self.flagged_ra and self.flagged_de lists in degrees.
        
        '''
        self.thresh = thresh
        
        c = SkyCoord(self.source_ra, self.source_de, unit='deg')
    
        sky_region = CircleSkyRegion(center=self.coords, radius=thresh)
        in_circle = sky_region.contains(c, wcs=self.wcs)

        for n, flagged in enumerate(in_circle):
            if flagged:
                self.flagged_ra.append(self.source_ra[n])
                self.flagged_de.append(self.source_de[n])
        
        self.pix_region = sky_region.to_pixel(self.wcs)

        info = {
            'thresh': thresh,
            'flagged': len(self.flagged_ra),
            'date': self.date
        }

        return info
        
    def separate(self):
        '''
        Calculates the angular separation between each of the flagged sources and
        the center coorindate where the moving is supposed to be. Adds it to self.distances.
        '''
        for RA, DEC in zip(self.source_ra, self.source_de):
            c_source = SkyCoord(f'{RA} {DEC}', frame='icrs', unit=(u.deg, u.deg))
            
            dist = c_source.separation(self.coords)
        
        self.distances.append(dist)
        
        
    def __repr__(self):
        return f"sky {self.num} at {self.date.value}"
        
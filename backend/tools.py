import datetime
import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
import astropy.units as u

def parallactic_angle(ra, dec):
    '''
    Calculates the parallactic angle according to the observatory
    location

    '''
    location = EarthLocation.of_site('Paranal')

    # Convert input time to Astropy Time object
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    observing_time = Time(current_time)

    # Define the sky position
    sky_coord = SkyCoord(f'{ra} {dec}', unit=(u.hourangle, u.deg))

    # Convert to AltAz frame to get Hour Angle (H)
    altaz = AltAz(obstime=observing_time, location=location)
    altaz_coord = sky_coord.transform_to(altaz)

    # Compute Hour Angle (H)
    H = altaz_coord.az.radian  # Hour Angle in radians

    # Convert latitude and declination to radians
    phi = np.radians(location.lat.value)
    delta = np.radians(sky_coord.dec.value)

    # Compute parallactic angle (q)
    q = np.arctan2(np.sin(H), np.cos(H) * np.sin(phi) - np.tan(delta) * np.cos(phi))

    # Convert result to degrees
    return np.degrees(q)
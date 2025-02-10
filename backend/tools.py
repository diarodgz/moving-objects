import datetime
import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
import astropy.units as u

def parallactic_angle(ra, dec, time):
    '''
    Calculates the parallactic angle according to the observatory
    location

    '''
    location = EarthLocation.of_site('Paranal')

    # Convert input time to Astropy Time object
    user_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    user_time = user_time.replace(tzinfo=datetime.timezone.utc)
    observing_time = Time(user_time)
    lst = observing_time.sidereal_time('apparent', longitude=location.lon.value*u.deg)
    

    # Define the sky position
    sky_coord = SkyCoord(f'{ra} {dec}', unit=(u.hourangle, u.deg))

    # Compute Hour Angle (H)
    H = lst.to('radian') - sky_coord.ra.to('radian')  # Hour Angle in radians

    # Convert latitude and declination to radians
    phi = np.radians(location.lat.value)
    delta = np.radians(sky_coord.dec.value)

    # Compute parallactic angle (q)
    psi = np.sin(H) / (np.cos(H) * np.sin(phi) - np.tan(delta) * np.cos(phi))
    q = np.arctan(psi)

    # Convert result to degrees
    return np.degrees(q.value)
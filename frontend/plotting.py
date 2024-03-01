from reproject import reproject_interp
from reproject.mosaicking import reproject_and_coadd, find_optimal_celestial_wcs
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.visualization.wcsaxes import add_scalebar
from matplotlib.patches import FancyArrowPatch
from astropy.visualization import (MinMaxInterval, SqrtStretch, AsinhStretch,
                                   ImageNormalize, LogStretch, simple_norm)

'''
Plotting methods.
'''


def plot_region(sky):
    
    '''
    Takes a Sky object and accesses all of the corresponding attributes to make a plot
    of the sky region.
    '''
    
    fig = plt.figure(figsize=(11, 11))
    norm = simple_norm(sky.img_data, 'sqrt', percent=99.)

    ax = plt.subplot(projection=sky.wcs)

    ax.imshow(sky.img_data, cmap='Greys', origin='lower', norm=norm)
    ax.plot(sky.source_ra, sky.source_de, 'o', color='red', mfc='None',
    transform=ax.get_transform('world'), ms=25, mew=0.5)
    
    ax.plot(sky.coords.ra.value, sky.coords.dec.value, '+', color='blue', mfc='None',
            transform=ax.get_transform('world'), ms=20, mew=0.5) # Center marker
    
    if sky.flagged_ra != [] and sky.flagged_de != []: # Make sure the flagged lists aren't empty.
        ax.plot(sky.flagged_ra, sky.flagged_de, 'o', color='lime', mfc='None',
            transform=ax.get_transform('world'), ms=20, mew=0.5)
        
    ax.set_xlabel('Right Ascension', fontsize=15)
    ax.set_ylabel('Declination', fontsize=15)
    ax.coords.grid(True, color='white', ls='solid')
    ax.autoscale(enable=True, axis='x', tight=True)
    ax.autoscale(enable=True, axis='y', tight=True)

    sky.pixel_region.plot(ax=ax, color='red')
    add_scalebar(ax, label="0.75'", length=0.75 * u.arcmin, corner='bottom right', color='black', label_top=True)

    arrow_up = FancyArrowPatch((10, 10), (10, 70),
                               color='black', arrowstyle='->',
                               mutation_scale=15, linewidth=1.5)
    ax.add_patch(arrow_up)
    ax.text(10, 72, 'N', ha='center', va='bottom', fontsize=15, weight='bold')


    arrow_right = FancyArrowPatch((10, 10), (70, 10),
                                  color='black', arrowstyle='->',
                                  mutation_scale=15, linewidth=1.5)
    ax.add_patch(arrow_right)
    ax.text(72, 10, 'E', ha='left', va='center', fontsize=15, weight='bold')
    

    
def mosaic(skys):
    '''
    skys: iterable that contains Sky objects.
    
    Receives an iterable that contains Sky objects and creates a mosaic using their
    PrimaryHDUs.
    '''
    
    sky_hdus = [sky.hdu for sky in skys] # Storing the PrimaryHDU objects of each sky FITS
    wcs_out, shape_out = find_optimal_celestial_wcs(sky_hdus, frame='icrs') 
    # Creating an optimal WCS and shape for the final image
    
    array, footprint = reproject_and_coadd(sky_hdus,
                                       wcs_out, shape_out=shape_out,
                                       reproject_function=reproject_interp)

    # reproject_and_coadd: Given a set of input images (a list of HDU objects), 
    # reproject and co-add these to a single final image.
    # Returns an array.
    
    # Plotting the mosaic.
    fig = plt.figure(figsize=(11, 11))
    norm = simple_norm(array, 'sqrt', percent=99.)

    ax = plt.subplot(projection=wcs_out)

    ax.imshow(array, cmap='Greys', origin='lower', norm=norm)
    ax.set_xlabel('Right Ascension', fontsize=15)
    ax.set_ylabel('Declination', fontsize=15)
    ax.grid(color='white', ls='solid', b=True)

    for sky in skys:
        ax.plot(sky.coords.ra.value, sky.coords.dec.value, '+', color='blue', mfc='None',
                transform=ax.get_transform('world'), ms=20, mew=0.5) # Center marker
        
    add_scalebar(ax, label="1'", length=1 * u.arcmin, color='black', label_top=True)

    arrow_up = FancyArrowPatch((10, 10), (10, 70),
                               color='black', arrowstyle='->',
                               mutation_scale=15, linewidth=1.5)
    ax.add_patch(arrow_up)
    ax.text(10, 72, 'N', ha='center', va='bottom', fontsize=15, weight='bold')


    arrow_right = FancyArrowPatch((10, 10), (70, 10),
                                  color='black', arrowstyle='->',
                                  mutation_scale=15, linewidth=1.5)
    ax.add_patch(arrow_right)
    ax.text(72, 10, 'E', ha='left', va='center', fontsize=15, weight='bold')

    return fig, ax
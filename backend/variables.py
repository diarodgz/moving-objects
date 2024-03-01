# ESO instrument fovs. Units in arcmin.

bg_fov = 8 # Background for plotting sky images.

fovs = {
    "FORS2_std" : 7.1,
    "FORS2_hres" : 4.25,
    "MUSE_wfm" : 1,
    "MUSE_nfm" : 0.125 
}


# Catalogs for the image query.

catalogs = {
    "SDSS16": 'V/154',
    "2MASS": 'II/246/out',
    "2MASS 6X": "II/281/2mass6x"
}

ob_path = "" # CHANGE THIS PATH TO THE LOCATION OF THE OB FILES
from backend.sky_handling import query, sky_process, sky_init, get_img
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from datetime import datetime
from astroquery.exceptions import InvalidQueryError
from requests.exceptions import ConnectTimeout
from backend.variables import fovs, ob_path
from reproject import reproject_interp
from reproject.mosaicking import reproject_and_coadd, find_optimal_celestial_wcs
from backend.ob import read_ob, read_eph, process_eph, process_desc
import astropy.units as u
import os

class BackThread(QThread):
    '''
    Thread to stop GUI from freezing.
    '''

    def __init__(self, signal_update, prog):
        super().__init__()
        self.signal_update = signal_update
        self.prog = prog

    def update(self):
        self.signal_update.emit(self.prog)

    def run(self):
        self.update()
        



class Backend(QObject):

    '''
    Class in charge of carrying out all of the processing. Inherits
    from QObject. Two main purposes: one, to carry out communication 
    with the frontend via signals, and two, in charge of carrying out
    all of the tasks to process inputs and deliver the mosaic to the
    frontend.

    -------------
    Attributes
    -------------

    signal_plot: pyqtSignal object. Sends the info neccesary to make the 
    plot to the frontend.

    signal_error: pyqtSignal object. Sends every error message to the frontend error dialogue.

    signal_progress: pyqtSignal object. Sends an update message and percent to the progressbar.

    finished: pyqtSignal object. Alerts the main thread that all of the processes has been finished.

    -------------
    Methods
    -------------

    validation:
    retrieve_eph:
    sky_generator:
    send_mosaic:

    '''

    signal_plot = pyqtSignal(list)
    signal_splot = pyqtSignal(dict)
    signal_error = pyqtSignal(str)
    signal_progress = pyqtSignal(tuple)
    signal_flags = pyqtSignal(str, str)
    signal_finished = pyqtSignal()
    signal_best = pyqtSignal(str)
    signal_datebox = pyqtSignal(list)
    signal_dates = pyqtSignal(list)
    signal_skyfov =pyqtSignal(int, int, int)

    def __init__(self, inst=None, rot=None, cat=None, validated=None, skys=None,
                 fov=None):
        super().__init__()
        self.validated = True
        self.inst = None
        self.rot = None
        self.fov = None
        self.cat = None
        self.thread = None
        self.skys = None

    def validation(self, inputs: dict) -> None:

        '''
        Validates the inputs for: target name, start and end datetime format,
        step, and n_results. Reformats the inputs. Once validated,
        it calls the self.retrieve.eph method to begin the ephemeris query.

        --------------
        Parameters
        --------------

        inputs: dict.
        '''

        self.thread = BackThread(self.signal_progress, (0, "Validating inputs..."))
        self.thread.start()

        #self.signal_progress.emit((0, "Validating inputs..."))
        print("Validating inputs...")

        if inputs['info'] == 'targ':
            
            self.validate_target(**inputs)

        elif inputs['info'] == 'coords':

            self.validate_coords(**inputs)

        elif inputs['info'] == 'ob':

            self.validate_ob(**inputs)


    def validate_target(self, info, id, start, end, time_start, 
                        time_end, step, step_u, n_result,
                        inst, cat):
        
        '''
        Validate search by target name or ID.

        ------------
        Parameters
        ------------

        '''
        self.validated = True

        print("Validating target...")
        self.thread.prog = (5, "Validating target...")
        #self.signal_progress.emit((5, "Validating target..."))
        
        starttime = f'{time_start[0]}:{time_start[1]}:{time_start[2]}'
        endtime = f'{time_end[0]}:{time_end[1]}:{time_end[2]}'

        # Transforming date and time into 'YYYY-MM-DD HH:MM:SS' format.
        datetime_start = f'{start} {starttime}'
        datetime_end = f'{end} {endtime}'

        # Validating UTC date-time format.
            
        if self.validate_datetime(datetime_start, datetime_end):
            print("Validated datetime...")
            self.thread.prog = (10, "Validated datetime...")
            #self.signal_progress.emit((10, "Validated datetime..."))
        else:
            self.validated = False


        # Combining step number and unit and vaildating step.
        if not step.isdigit():
            self.validated = False
            self.signal_error.emit("Step must be an integer.")
        else:
            step_units = step + step_u

        # Validating n_result input and converting to int.
        if not n_result.isdigit():
            self.validated = False
            self.signal_error.emit("N. Results must be an integer.")
        else:
            n = int(n_result)


        if self.validated:
            print("Validated target...")
            # Creating a dictionrary with all of the necessary keyword
            # args to pass onto the query method.

            params_start = {}

            params_start['id'] = id
            params_start['start_from'] = datetime_start
            params_start['step'] = step_units
            params_start['t_start'] = datetime_start
            params_start['t_end'] = datetime_end
            params_start['num_results'] = n

            self.inst = inst
            self.cat = cat

            #self.signal_progress.emit((15, "Validated inputs..."))
            self.thread.prog = (15, "Validated inputs...")
            self.retrieve_eph(params_start)
            

        else:
            print(f'Validation state: {self.validated}')
        

    def validate_datetime(self, datetime_start, datetime_end):

        print("Validating datetimes...")

        try:
            datetime.strptime(datetime_start, '%Y-%m-%d %H:%M:%S')
            datetime.strptime(datetime_end, '%Y-%m-%d %H:%M:%S')
            # or date_object = datetime.strptime(DATE, '%Y-%m-%d %H:%M:%S')
            # if you need the actual date object later
        except ValueError as e:
            # handle invalid date
            self.signal_error.emit("Invalid Date.")
            print(f'Invalid Date: {e}')
        else:
            return True

    def validate_coords(self, info, ra, dec, 
                        inst, cat):
        
        '''
        Validate coordinate search.

        --------------
        Parameters
        --------------
        ra: list
        dec: list
        inst: str
        rot: str
        cat: str
        '''
        
        print("Validating coordinates...")
        self.thread.prog = (20, "Validating coordinates...")
        #self.signal_progress.emit((20, "Validating coordinates..."))


        # Validating RA:
        try:
            # Validating RA in hh:mm:ss format.
            ra = f'{ra[0]}:{ra[1]}:{ra[2]}'
            datetime.strptime(ra, '%H:%M:%S')
        except:
            self.validated = False
            self.signal_error.emit("Invalid RA value for hh:mm:ss format.")
        else:
            pass
                
    
        # Valildating DEC:
        if int(dec[0]) <= -90 or int(dec[0]) >= 90:
            self.validated = False
            self.signal_error.emit("Invalid dd value for dd:mm:ss format.")
        elif int(dec[1]) > 59:
            self.validated = False
            self.signal_error.emit("Invalid mm value for dd:mm:ss format.")
        elif int(dec[1]) > 59:
            self.validated = False
            self.signal_error.emit("Invalid ss value for dd:mm:ss format.")
        else:
            dec = f'{dec[0]}:{dec[1]}:{dec[2]}'
        
        if self.validated:
            print("Validated coordinates...")
            self.thread.prog = (25, "Validated coordinates...")
            #self.signal_progress.emit((25, "Validated coordinates..."))
            print(ra, dec)
            self.inst = inst
            self.cat = cat

            for key in fovs.keys():
                if self.inst == key:
                    self.fov = fovs[self.inst]

            self.single_img(self.fov, ra, dec)
        else:
            print(f"Inputs invalid.")


    def validate_ob(self, id, start_date, end_date,
                    start_time, end_time, step, step_u,
                    n_result, rot, cat):
        
        '''
        Validate OB path.

        --------------
        Parameters
        --------------
        id: str
        start_date: str
        end_date: str
        start_time: list
        end_time: list
        step: str
        step_u: str
        n_result: str
        rot: str
        cat: str
        '''
        
        print("Validating OB...")
        self.thread.prog = (10, "Validated OB...")
        #self.signal_progress.emit((10, "Validated OB..."))
        
        path = os.path.join(ob_path, id)

        try:
            with open(path) as r:
                r.readlines()
        except FileNotFoundError:
            self.validated = False
            self.signal_error.emit("Path not found.")
        else:
            ob_raw = read_ob(path)
            eph_raw = read_eph

            ob_processed = process_desc(ob_raw)
            eph_processed = process_eph(eph_raw)

            print("Validated OB.")
            self.thread.prog = (15, "Validated OB...")
            #self.signal_progress.emit((15, "Validated OB..."))

    def load_ob(path):
        print("WIP")
    
    def retrieve_eph(self, inputs: dict) -> None:
        '''
        Receives all of the inputs from the window once they've been validated
        and queries ephemeris files from Vizier. Calls the query method from
        the sky_handling module, then passes the result to self.sky_genetor.

        ------------
        Parameters
        ------------

        inputs: dict
        '''
        
        print("Retrieving ephemeris...")

        try:
            eph = query(**inputs)
        except InvalidQueryError as e:
            print(f"Query error. Target not found.")
            self.signal_error.emit(e)
        else:
            print(f"Retrieved ephemeris.\nResults: {len(eph)} dates. Final date available is: \
{eph['Date'][len(eph) - 1]}")
            
            self.thread.prog = (20, "Retrieved ephemeris...")
            #self.signal_progress.emit((20, "Retrieved ephemeris..."))
            self.sky_generator(eph)


    def single_img(self, ra, dec, fov):
        '''
        Query a single image.

        ---------------
        Parameters
        ---------------
        ra: str
        dec: str
        fov: int
        '''

        img_info = get_img(ra, dec, fov)
        self.signal_splot.emit(img_info)

        print("Sending plot to front end...")
        self.thread.prog = (60, "Sending plot to front end...")
        #self.signal_progress.emit((60, "Sending plot to front end..."))
    


    def sky_generator(self, eph):
        '''
        Uses the sky_init method from the sky_handling module
        to initilize Sky instances for every patch of sky according to the
        ephemeris files. Afterwards, it applies the sky_process method from the same
        module to prepare the Sky instancess for plotting.

        ------------
        Parameters
        ------------

        eph: astropy.Table instance.
        fov: int. Depends on instrument selected.
        '''

        # Assigns FOV variable according to the chosen instrument.

        for key in fovs.keys():
            if self.inst == key:
                self.fov = fovs[self.inst]

        self.thread.prog = (25, "Generating skys...")
        #self.signal_progress.emit((25, "Generating skys..."))
        print("Generating skys...")

        try:
            skys = sky_init(eph, self.fov)
        except ConnectTimeout as e:
            self.signal_error(f"Connection timeout error. {e}")
        else:
            print("Skys generated.")
            self.thread.prog = (30, "Generated skys...")
            #self.signal_progress.emit((30, "Generated skys..."))
            print("Processing skys...")

        try:
            sky_process(skys, self.fov)
        except IndexError as e:
            self.signal_error.emit(f"Server Error: Vizier query result empty. Try again later. {e}")
        else:
            print("Skys processed.")
            self.thread.prog = (35, "Processed skys...")
            #self.signal_progress.emit((35, "Processed skys..."))
            self.send_mosaic(skys)
            self.flagging(skys)
            self.signal_dates.emit([sky.date.value for sky in skys])
            self.skys = skys


    def flagging(self, skys: list):
        
        print("Flagging bright objects...")
        self.thread.prog = (40, "Flagging bright objects...")
        #self.signal_progress.emit((40, "Flagging bright objects..."))

        b_flag = list(map(lambda x: x.flag_bright(), skys))
        
        print("Flagging objects within 0.5 arcmin...")
        self.thread.prog = (45, "Flagging objects within 0.5 arcmin...")
        #self.signal_progress.emit((45, "Flagging objects within 0.5 arcmin..."))
        dist_flag = list(map(lambda x: x.flag_dist(0.5 * u.arcmin), skys))

        # We prepare an empty string to fill it with the brightness flags.
        b_notice = f""

        for item in b_flag:
            b_notice += f'There is a {item["mag"]:.3f} mag source within \
{item["dist"].to_string(unit=u.arcmin)} of the target on {item["date"]}\n'

        # Empty string to fill with distance info.
        dist_notice = f""

        # Filling empty string with information about distances.
        for item in dist_flag:
            dist_notice += f'There are {item["flagged"]} sources within \
{item["thresh"]} of the target on {item["date"]}\n'

        self.signal_flags.emit(b_notice, dist_notice)

    def get_best(self):
        pass

    def send_mosaic(self, skys: list):

        '''
        Takes all of the generated Sky objects and sends them to the frontend,
        along with the optimal WCS and the final array created for plotting
        the image.

        ----------
        Parameters
        ----------

        skys: list. Contains Sky objects.
        '''

        sky_hdus = [sky.hdu for sky in skys] # Storing the PrimaryHDU objects of each sky FITS
        wcs_out, shape_out = find_optimal_celestial_wcs(sky_hdus, frame='icrs') 
        # Creating an optimal WCS and shape for the final image
        
        array, footprint = reproject_and_coadd(sky_hdus,
                                        wcs_out, shape_out=shape_out,
                                        reproject_function=reproject_interp)
        
        mose = [skys, wcs_out, array]

        print("Sending skys to front end...")
        self.thread.prog = (50, "Sending skys to front end...")
        #self.signal_progress.emit((50, "Sending skys to front end..."))
        self.signal_plot.emit(mose)

    def send_skyfov(self, date):

        sky = list(filter(lambda x: (x.date.value == date), self.skys))

        self.signal_skyfov.emit(sky[0].coords.ra.value, 
                                sky[0].coords.dec.value, self.fov)


















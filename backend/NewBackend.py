from backend.worker import Worker
from backend.tools import parallactic_angle
from astropy.coordinates import SkyCoord
import astropy.units as u
from PyQt5.QtCore import pyqtSignal, QObject

class Backend(QObject):
    '''
    Sends the products from the frontend to the backend.
    '''
    signal_error = pyqtSignal(str)
    signal_plot = pyqtSignal(object, object, object)
    signal_splot = pyqtSignal(object, float, object, object)
    signal_error = pyqtSignal(str)
    signal_progress = pyqtSignal(int, str)
    signal_flags = pyqtSignal(list, str)
    finished = pyqtSignal()
    signal_best = pyqtSignal(str)
    signal_pangle = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.worker = None 

    def start_worker(self, data):
        self.worker = Worker(data)
        # self.worker.finished.connect(self.task_finished)
        self.worker.signal_error.connect(self.send_error)
        self.worker.signal_plot.connect(self.send_plot)
        self.worker.signal_splot.connect(self.send_splot)
        self.worker.signal_progress.connect(self.send_progress)
        self.worker.signal_flags.connect(self.send_flags)
        self.worker.signal_best.connect(self.send_best)
        self.worker.signal_send_pa.connect(self.calculate_pa)
        self.worker.start()

    def send_plot(self, skys, wcs, data):
        self.signal_plot.emit(skys, wcs, data)

    def send_splot(self, coords, fov, wcs, data):
        self.signal_splot.emit(coords, fov, wcs, data)

    def calculate_pa(self, ra, dec, time):
        if dec == 'null':
            c = SkyCoord.from_name(ra)
            p = parallactic_angle(c.ra.to_string(u.hour), 
                                  c.dec.to_string(u.deg), time)
            self.signal_pangle.emit(p)
        else:
            p = parallactic_angle(ra, dec, time)
            self.signal_pangle.emit(p)

    def send_flags(self, content, mag):
        self.signal_flags.emit(content, mag)

    def send_best(self, best_dates):
        self.signal_best.emit(best_dates)

    def send_progress(self, prog, message):
        self.signal_progress.emit(prog, message)

    def send_error(self, error):
        self.signal_error.emit(error)

    def stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
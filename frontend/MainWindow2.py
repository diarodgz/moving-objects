import sys
import os
from PyQt5.QtCore import pyqtSignal, Qt, QThread
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QDialog,
    QRadioButton,
    QProgressBar,
    QButtonGroup,
    QSlider,
    QListWidget,
    QScrollBar,
    QTableWidget,
    QTableWidgetItem
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import Slider, Button
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.visualization.wcsaxes import add_scalebar, Quadrangle
from matplotlib.patches import FancyArrowPatch, Rectangle
from astropy.visualization import (MinMaxInterval, SqrtStretch, AsinhStretch,
                                   ImageNormalize, LogStretch, simple_norm)
import astropy.units as u
import yaml
import matplotlib.transforms as transforms

config_path = os.path.join('settings', 'config.yml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

class MoThread(QThread):
    result_ready = pyqtSignal()

    def __init_(self, backend):
        super().__init__()
        self.backend = backend

    def run(self):
        pass

class MainWindow(QMainWindow):

    '''
    Class in charge of everything to do with the GUI
    aspect of the program. Very minimal tasks besides organizing GUI
    and preparing inputs to communicate to the backend via signals.
    '''
    signal_valid_input = pyqtSignal(dict)
    signal_thread = pyqtSignal(str)
    signal_pa = pyqtSignal(str, str)
    signal_date = pyqtSignal(str)

    def __init__(self, backend):
        super().__init__()
        self.single_img = False
        self.backend = backend
        self.initialize_gui()

    def initialize_gui(self):
        # Initializing all of the gui widgets.

        self.setWindowTitle("Moving Objects")
        self.setGeometry(100, 100, 1000, 700)

        self.central_widget = QWidget()

        self.title = QLabel("Moving Object Tool", self)
        self.title.setStyleSheet("font: bold 30px")

        self.from_label = QLabel('Start Date - Time', self)
        self.end_label = QLabel('End Date - Time', self)
        self.step_label = QLabel('Step', self)
        # self.num_label = QLabel('N. Results', self)
        # self.rotation =  QLabel('Rotation', self)
        self.scale_label = QLabel('Time Scale', self)
        self.inst_label = QLabel('Instrument', self)

        self.ra_label = QLabel('RA', self)
        self.dec_label = QLabel('DEC', self)


        # Instrument scroll menu
        self.inst_cbox = QComboBox()
        self.instruments = [
            key for key in config['INSTRUMENT'].keys()
        ]

        self.inst_cbox.addItems(self.instruments)

        # Catalog scroll menu
        self.cat_label = QLabel('Catalog', self)

        self.cat_cbox = QComboBox()
        self.cats= [
            key for key in config['CATALOG'].keys()
        ]

        self.cat_cbox.addItems(self.cats)

        # HIPS Survey scroll menu
        self.hips_label = QLabel('HIPS Survey', self)
        self.hips = [
            key for key in config['HIPS_SURVEY'].keys()
        ]
        self.hips_cbox = QComboBox()
        self.hips_cbox.addItems(self.hips)
        self.hips_cbox.setCurrentIndex(1)

        # Step scroll menu.
        self.step_cbox = QComboBox()
        self.steps = ["s", "min", "h", "d"]
        self.step_cbox.addItems(self.steps)
        self.step_cbox.setCurrentIndex(1)

        self.results_label = QLabel('RESULTS', self)
        self.results_label.setStyleSheet(
            'font: bold 20px'
        )

        self.rot_label = QLabel('Rotation (deg)', self)
        #self.bright_label = QLabel('Brightest objects:', self)
        #self.brightest_label = QLabel('', self)

        #self.nearby_label = QLabel('Sources nearby:', self)
        #self.dist_label = QLabel('', self)


        self.time_dot1 = QLabel(':', self)
        self.time_dot2 = QLabel(':', self)
        self.time_dot3 = QLabel(':', self)
        self.time_dot4 = QLabel(':', self)

        self.query_labels = [
            self.from_label,
            self.end_label,
            self.scale_label,
            self.step_label,
            self.rot_label
        ]
        
        
        # Target identifier buttons.
        self.targ_button = QRadioButton('Target ID', self)
        self.targ_button.clicked.connect(self.clicked_target)

        self.coord_button = QRadioButton('Coordinates',  self)
        self.coord_button.clicked.connect(self.clicked_coord)

        self.ob_button = QRadioButton('OB ID', self)
        self.ob_button.clicked.connect(self.clicked_ob)

        self.target_inp = QLineEdit(self)
        self.target_inp.setPlaceholderText("Moving Object ID, e.g. 'Ceres', '3'")
        self.target_inp.setFixedWidth(250)

        self.ob_id =  QLineEdit(self)
        self.ob_id.setPlaceholderText("OB ID number, e.g. 3677342")

        self.from_inp = QLineEdit(self)
        self.from_inp.setPlaceholderText('e.g. YYYY-MM-DD')
        self.from_inp.setFixedWidth(125)
        self.from_inp.setInputMask('0000-00-00;X')

        self.step_inp = QLineEdit(self)
        self.step_inp.setPlaceholderText("e.g. 10s, 10min, 1h, 7d")
        self.step_inp.setFixedWidth(150)

        self.end_inp = QLineEdit(self)
        self.end_inp.setPlaceholderText('e.g. YYYY-MM-DD')
        self.end_inp.setFixedWidth(125)
        self.end_inp.setInputMask('0000-00-00;X')

        #self.num_inp = QLineEdit(self)
        #self.num_inp.setPlaceholderText('N. Results, e.g. 1,..,N.')
        #self.num_inp.setFixedWidth(150)

        # Rotation input and parallactic angle calculation button
        self.rot_inp = QLineEdit(self)
        self.rot_inp.setText('0')
        self.rot_inp.setFixedWidth(150)

        # Calculate PA Button
        self.calc_button = QPushButton('Calculate PA', self)
        self.calc_button.clicked.connect(self.calculate_pa)

        # self.time_inp

        # Start times inputs.

        self.h_inps = QLineEdit(self)
        #self.h_inps.setPlaceholderText('00')
        self.h_inps.setFixedWidth(25)
        self.h_inps.setMaxLength(2)
        self.h_inps.setInputMask('99;-')

        self.m_inps = QLineEdit(self)
        #self.m_inps.setPlaceholderText('00')
        self.m_inps.setFixedWidth(25)
        self.m_inps.setMaxLength(2)
        self.m_inps.setInputMask('99;-')

        self.s_inps = QLineEdit(self)
        #self.s_inps.setPlaceholderText('00')
        self.s_inps.setFixedWidth(25)
        self.s_inps.setMaxLength(2)
        self.s_inps.setInputMask('99;-')

        # End time inputs.
        self.h_inpe = QLineEdit(self)
        #self.h_inpe.setPlaceholderText('00')
        self.h_inpe.setFixedWidth(25)
        self.h_inpe.setMaxLength(2)
        self.h_inpe.setInputMask('99;-')

        self.m_inpe = QLineEdit(self)
        #self.m_inpe.setPlaceholderText('00')
        self.m_inpe.setFixedWidth(25)
        self.m_inpe.setMaxLength(2)
        self.m_inpe.setInputMask('99;-')

        self.s_inpe = QLineEdit(self)
       #self.s_inpe.setPlaceholderText('00')
        self.s_inpe.setFixedWidth(25)
        self.s_inpe.setMaxLength(2)
        self.s_inpe.setInputMask('99;-')


        self.time_s = [
            self.h_inps,
            self.m_inps,
            self.s_inps
        ]

        self.time_e = [
            self.h_inpe,
            self.m_inpe,
            self.s_inpe
        ]

        self.query_inputs = [
            self.target_inp,
            self.from_inp,
            self.end_inp,
            self.step_inp,
            self.rot_inp
        ]

        # RA coord input

        self.h_ra = QLineEdit(self)
        self.h_ra.setFixedWidth(25)
        self.h_ra.setMaxLength(2)
        self.h_ra.setInputMask('99;-')

        self.m_ra = QLineEdit(self)
        self.m_ra.setFixedWidth(25)
        self.m_ra.setMaxLength(2)
        self.m_ra.setInputMask('99;-')

        self.s_ra = QLineEdit(self)
        self.s_ra.setFixedWidth(25)
        self.s_ra.setMaxLength(2)
        self.s_ra.setInputMask('99;-')

        self.ra_input = [
            self.h_ra,
            self.m_ra,
            self.s_ra
        ]

        # DEC coord inputs

        self.d = QLineEdit(self)
        self.d.setFixedWidth(26)
        self.d.setMaxLength(3)
        self.d.setInputMask('###;-')

        self.m_dec = QLineEdit(self)
        self.m_dec.setFixedWidth(25)
        self.m_dec.setMaxLength(2)
        self.m_dec.setInputMask('99;-')

        self.s_dec = QLineEdit(self)
        self.s_dec.setFixedWidth(25)
        self.s_dec.setMaxLength(2)
        self.s_dec.setInputMask('99;-')

        self.dec_input = [
            self.d,
            self.m_dec,
            self.s_dec
        ]

        self.best_seen = QLabel('BEST SEEN:', self) # Label for best dates
        self.best_seen.setStyleSheet('font: bold 15px')

        # Progress bar
        # self.prog_bar = QProgressBar(self)
        self.prog_msg = QLabel('', self)

        self.query_button = QPushButton('Query', self)
        self.query_button.clicked.connect(self.clicked_query)

        self.exit_button = QPushButton('Exit', self)
        self.exit_button.clicked.connect(self.exit)

        # self.fov_button = QPushButton('View Fov', self)
        # self.fov_button.clicked.connect(self.get_coords)

        self.utc_button = QRadioButton('UTC', self)
        self.etc_button = QRadioButton('Other', self)

        self.figure = plt.figure()
        # this is the Canvas Widget that 
        # displays the 'figure'it takes the
        # 'figure' instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        #self.canvas.setFixedSize(700, 500)
  
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = 'Empty'

        self.canvas.mpl_connect('motion_notify_event', self.motion_hover)

        self.target_group = QButtonGroup(self)
        self.target_group.addButton(self.targ_button)
        self.target_group.addButton(self.coord_button)
        self.target_group.addButton(self.ob_button)

        self.time_group = QButtonGroup(self)
        self.time_group.addButton(self.utc_button)
        self.time_group.addButton(self.etc_button)

        # Layout Handling

        self.main_vbox = QVBoxLayout() # Init main layout

        self.title_box = QVBoxLayout() # Init title layout

        # Adding title widgets to the title layout
        self.title_box.addWidget(self.title, alignment=Qt.AlignCenter)
        # self.title_box.addStretch(1)

        # Scrollbox that contains information pertaining to bright and nearby sources
        # self.list_widget = QListWidget(self)

        # self.scrollbar = QScrollBar(self)
        # self.scrollbar.setMaximum(self.list_widget.count())
        # self.scrollbar.sliderMoved.connect(self.list_widget.setCurrentRow)

        # self.list_widget.addItem('Information will go here...')

        # Init layouts for user input
        self.info_vbox1 = QVBoxLayout()
        self.info_vbox2 = QVBoxLayout()
        self.info_vbox3 = QVBoxLayout()
        self.info_vbox4 = QVBoxLayout()
        self.info_vbox5 = QVBoxLayout()
        self.info_vbox6 = QVBoxLayout()


        # Regarding target input buttons
        self.target_hbox = QHBoxLayout()
        self.target_hbox.addWidget(self.targ_button, alignment=Qt.AlignCenter)
        self.target_hbox.addWidget(self.coord_button, alignment=Qt.AlignCenter)
        self.target_hbox.addWidget(self.ob_button, alignment=Qt.AlignCenter)

        # Regarding coordinate input QLineEdits
        self.dot1 = QLabel(':', self)
        self.dot2 = QLabel(':', self)
        self.dot3 = QLabel(':', self)
        self.dot4 = QLabel(':', self)
        
        self.coord_hbox = QHBoxLayout()

        self.ra_hbox = QHBoxLayout()
        self.ra_hbox.addWidget(self.ra_label)

        self.dec_hbox = QHBoxLayout()
        self.dec_hbox.addWidget(self.dec_label)

        for ra, dec in zip(self.ra_input, self.dec_input):
            self.ra_hbox.addWidget(ra)
            self.dec_hbox.addWidget(dec)

            if ra is self.h_ra:    
                self.ra_hbox.addWidget(self.dot1)
            elif ra is self.m_ra:
                self.ra_hbox.addWidget(self.dot2)

            if dec is self.d:    
                self.dec_hbox.addWidget(self.dot3)
            elif dec is self.m_dec:
                self.dec_hbox.addWidget(self.dot4)

        self.coord_hbox.addLayout(self.ra_hbox)
        self.coord_hbox.addLayout(self.dec_hbox)


        # Addding target buttons to infovbox1.
        self.info_vbox1.addLayout(self.target_hbox)

        # Layout for timescale inputs
        self.scale_hbox = QHBoxLayout()

        # Adding scale widgets to scale layout
        self.scale_hbox.addWidget(self.utc_button, alignment=Qt.AlignCenter)
        self.scale_hbox.addWidget(self.etc_button, alignment=Qt.AlignCenter)

        # Init layout for step inputs
        self.step_hbox = QHBoxLayout()

        # Ading widgets to step layout
        self.step_hbox.addWidget(self.step_inp, alignment=Qt.AlignCenter)
        self.step_hbox.addWidget(self.step_cbox, alignment=Qt.AlignCenter)

        #  Adding widgets to user input layout 4.

        self.rot_hbox = QHBoxLayout()
        self.rot_hbox.addWidget(self.rot_inp)
        self.rot_hbox.addWidget(self.calc_button)

        self.info_vbox4.addLayout(self.scale_hbox)
        self.info_vbox4.addLayout(self.step_hbox)
        self.info_vbox4.addLayout(self.rot_hbox)

        for label in self.query_labels[:2]:
            # Takes the first three of the labels and
            # Stores them into VBoxes 1.    
            self.info_vbox1.addWidget(label, alignment=Qt.AlignCenter)
        
        for label in self.query_labels[2:]:
            # Takes the last three of the labels and
            # Stores them into VBoxes 3 
            self.info_vbox3.addWidget(label, alignment=Qt.AlignCenter)

        # Start and end time input layout
        self.time_box1 = QHBoxLayout()
        self.time_box2 = QHBoxLayout()

        # Adding hh:mm:ss layout to start and end input layout.
        for input_s, input_e in zip(self.time_s, self.time_e):
            self.time_box1.addWidget(input_s)
            self.time_box2.addWidget(input_e)

            if input_s is self.h_inps:    
                self.time_box1.addWidget(self.time_dot1)
            elif input_s is self.m_inps:
                self.time_box1.addWidget(self.time_dot2)

            if input_e is self.h_inpe:    
                self.time_box2.addWidget(self.time_dot3)
            elif input_e is self.m_inpe:
                self.time_box2.addWidget(self.time_dot4)

        # Updating vbox 5.

        self.info_vbox5.addWidget(self.inst_label)
        self.info_vbox5.addWidget(self.cat_label)
        # self.info_vbox5.addWidget(self.center_label)
        self.info_vbox5.addWidget(self.hips_label)

        # Updating vbox 6.

        self.info_vbox6.addWidget(self.inst_cbox, alignment=Qt.AlignCenter)
        self.info_vbox6.addWidget(self.cat_cbox, alignment=Qt.AlignCenter)
        # self.info_vbox6.addWidget(self.date_cbox, alignment=Qt.AlignCenter)
        self.info_vbox6.addWidget(self.hips_cbox, alignment=Qt.AlignCenter)

        # Main central box layout init
        self.start_hbox = QHBoxLayout()

        self.start_hbox.addWidget(self.from_inp)
        self.start_hbox.addLayout(self.time_box1)

        self.end_hbox = QHBoxLayout()

        self.end_hbox.addWidget(self.end_inp)
        self.end_hbox.addLayout(self.time_box2)

        # Updating infobox 2
        self.info_vbox2.addWidget(self.target_inp)
        self.info_vbox2.addWidget(self.ob_id)
        self.info_vbox2.addLayout(self.coord_hbox)
        self.info_vbox2.addLayout(self.start_hbox)
        self.info_vbox2.addLayout(self.end_hbox)

        # Center hbox init.
        self.center_hbox = QHBoxLayout()

        # Updating center hbox.
        self.center_hbox.addStretch(1)
        self.center_hbox.addLayout(self.info_vbox1)
        self.center_hbox.addStretch(1)
        self.center_hbox.addLayout(self.info_vbox2)
        self.center_hbox.addStretch(1)
        self.center_hbox.addLayout(self.info_vbox3)
        self.center_hbox.addStretch(1)
        self.center_hbox.addLayout(self.info_vbox4)
        self.center_hbox.addStretch(1)
        self.center_hbox.addLayout(self.info_vbox5)
        self.center_hbox.addStretch(1)
        self.center_hbox.addLayout(self.info_vbox6)
        

        # Adding query and exit buttons.
        self.button_box1 = QHBoxLayout()

        self.button_box1.addStretch(1)
        self.button_box1.addWidget(self.query_button, alignment=Qt.AlignCenter)
        self.button_box1.addWidget(self.exit_button, alignment=Qt.AlignCenter)
        # self.button_box1.addWidget(self.fov_button, alignment=Qt.AlignCenter)
        self.button_box1.addStretch(1)

        # Progress bar layout.
        self.prog_hbox = QHBoxLayout()

        self.prog_hbox.addWidget(self.prog_msg)
        # self.prog_hbox.addWidget(self.prog_bar)
        self.create_table()

        # Mosaic layout.
        plot = QVBoxLayout()
        # adding tool bar to the layout
        plot.addWidget(self.toolbar)
        # adding canvas to the layout
        plot.addWidget(self.canvas)

        plot_info = QVBoxLayout()

        
        plot_info.addLayout(self.prog_hbox)
        plot_info.addWidget(self.results_label, alignment=Qt.AlignCenter)
        plot_info.addWidget(self.best_seen, alignment=Qt.AlignCenter)
        plot_info.addWidget(self.table)
        # plot_info.addWidget(self.list_widget, alignment=Qt.AlignCenter)
        # plot_info.addWidget(self.bright_label, alignment=Qt.AlignCenter)
        #plot_info.addWidget(self.brightest_label, alignment=Qt.AlignCenter)
        #plot_info.addWidget(self.nearby_label, alignment=Qt.AlignCenter)
        #plot_info.addWidget(self.dist_label)

        results = QHBoxLayout()
        results.addLayout(plot)
        results.addLayout(plot_info)

        # Addding to the main box.

        self.main_vbox.addLayout(self.title_box)
        self.main_vbox.addLayout(self.center_hbox)
        self.main_vbox.addLayout(self.button_box1)
        self.main_vbox.addLayout(results)

        self.central_widget.setLayout(self.main_vbox)
        self.setCentralWidget(self.central_widget)

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.hide()
            dec.hide()

        self.ra_label.hide()
        self.dec_label.hide()
        
        self.dot1.hide()
        self.dot2.hide()
        self.dot3.hide()
        self.dot4.hide()

        self.ob_id.hide()

        self.show()


    def clicked_query(self):
        '''
        Response to clicking the query button.
        '''

        if self.targ_button.isChecked():
            inputs = {
                'info': 'targ'
            }

            inputs['id'] = self.target_inp.text()
            inputs['start'] = self.from_inp.text()
            inputs['end'] = self.end_inp.text()


            inputs['time_start'] = [x.text() for x in self.time_s]
            inputs['time_end'] = [x.text() for x in self.time_e]


            inputs['step'] = self.step_inp.text()
            inputs['step_u'] = self.step_cbox.currentText()
            inputs['n_result'] = config['NUM_RESULTS']
            inputs['inst'] = self.inst_cbox.currentText()
            #inputs['rot'] = (self.rot_inp.text())
            inputs['cat'] = (self.cat_cbox.currentText())
            inputs['hips'] = (self.hips_cbox.currentText())

            self.signal_valid_input.emit(inputs)

        elif self.coord_button.isChecked():

            ra = [x.text() for x in self.ra_input]
            dec = [x.text() for x in self.dec_input]

            inputs = {
                'info': 'coords',
                'ra': ra,
                'dec': dec,
                'inst': self.inst_cbox.currentText(),
                'rot': self.rot_inp.text(),
                'cat': self.cat_cbox.currentText(),
                'hips': self.hips_cbox.currentText()
            }

            self.signal_valid_input.emit(inputs)

        else:

            time_start = [x.text() for x in self.time_s]
            time_end = [x.text() for x in self.time_e]

            inputs = {
                'info': 'ob',
                'id': self.ob_id.text(),
                'start_date': self.from_inp.text(),
                'end_date': self.end_inp.text(),
                'start_time': time_start,
                'end_time': time_end,
                'step': self.step_inp.text(),
                'step_u': self.step_cbox.currentText(),
                'n_result': config['NUM_RESULTS'],
                #'rot': (self.rotate_inp.text(), self.rot_u.currentText()),
                'cat': self.cat_cbox.currentText(),
                'hips': self.hips_cbox.currentText()
            }

            self.signal_valid_input.emit(inputs)


    def clicked_ob(self):
        '''
        Response to clicking the OB radio button.
        '''

        self.target_inp.clear()
        self.target_inp.hide()

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.hide()
            dec.hide()

            ra.clear()
            dec.clear()

        self.dot1.hide()
        self.dot2.hide()
        self.dot3.hide()
        self.dot4.hide()

        self.ra_label.hide()
        self.dec_label.hide()

        self.ob_id.show()

        for inputs in self.query_inputs:
            inputs.setEnabled(True)

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.setEnabled(False)
            dec.setEnabled(False)

        for time_s, time_e in zip(self.time_s, self.time_e):
            time_s.setEnabled(True)
            time_e.setEnabled(True)

        for time_s, time_e in zip(self.time_s, self.time_e):
            time_s.setEnabled(True)
            time_e.setEnabled(True)

        self.target_inp.clear()
        self.target_inp.show()

        for inputs in self.query_inputs:

            inputs.show()

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.hide()
            dec.hide()

        for time_s, time_e in zip(self.time_s, self.time_e):
            time_s.show()
            time_e.show()


        self.time_dot1.show()
        self.time_dot2.show()
        self.time_dot3.show()
        self.time_dot4.show()

        for label in self.query_labels:
            label.show()

        self.step_cbox.show()

        self.utc_button.show()
        self.etc_button.show()

        self.best_seen.show()
        self.target_inp.hide()


    def clicked_target(self):
        '''
        Response to clicking the target radio button.
        '''
        
        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.hide()
            dec.hide()

            ra.clear()
            dec.clear()

        self.dot1.hide()
        self.dot2.hide()
        self.dot3.hide()
        self.dot4.hide()

        self.ra_label.hide()
        self.dec_label.hide()

        self.ob_id.hide()

        self.target_inp.show()

        for inputs in self.query_inputs:
            inputs.setEnabled(True)

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.setEnabled(True)
            dec.setEnabled(True)

        for time_s, time_e in zip(self.time_s, self.time_e):
            time_s.setEnabled(True)
            time_e.setEnabled(True)

        self.target_inp.clear()
        self.target_inp.show()

        for inputs in self.query_inputs:

            inputs.show()

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.hide()
            dec.hide()

        for time_s, time_e in zip(self.time_s, self.time_e):
            time_s.show()
            time_e.show()


        self.time_dot1.show()
        self.time_dot2.show()
        self.time_dot3.show()
        self.time_dot4.show()

        for label in self.query_labels:
            label.show()

        self.from_inp.show()
        self.end_inp.show()

        self.step_cbox.show()

        self.utc_button.show()
        self.etc_button.show()

        self.best_seen.show()

        #self.rotate_inp.setEnabled(True)

    def clicked_coord(self):
        '''
        Response to clicking the coordinates radio button.
        '''

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.show()
            dec.show()

        self.dot1.show()
        self.dot2.show()
        self.dot3.show()
        self.dot4.show()

        self.ra_label.show()
        self.dec_label.show()

        self.ob_id.clear()
        self.ob_id.hide()

        self.target_inp.clear()
        self.target_inp.hide()

        for inputs in self.query_inputs:

            inputs.hide()

        for ra, dec in zip(self.ra_input, self.dec_input):
            ra.setEnabled(True)
            dec.setEnabled(True)

        for time_s, time_e in zip(self.time_s, self.time_e):
            time_s.hide()
            time_e.hide()


        self.time_dot1.hide()
        self.time_dot2.hide()
        self.time_dot3.hide()
        self.time_dot4.hide()

        for label in self.query_labels:
            label.hide()

        self.from_inp.hide()
        self.end_inp.hide()

        self.step_cbox.hide()

        self.utc_button.hide()
        self.etc_button.hide()

        self.best_seen.hide()

        self.rot_label.show()
        self.rot_inp.show()


    def update_progbar(self, prog):
        '''
        Updating the progress bar.
        '''

        percent= prog[0]
        display = prog[1]

        # self.prog_bar.setValue(percent)
        self.prog_msg.setText(display)
    
        
    def error(self, msg):
        # Dialogue box appears in case of error.

        dlg = ErrorWindow(msg)
        if dlg.exec():
            pass        


    def plot(self, info):

        '''
        Contains all of the steps necessary to create a plot
        using matpotlib. Takes a list that contains the list
        of skys, the optimal WCS, and the final array for plotting.
        '''

        self.skys = info[0]
        wcs_out = info[1]
        array = info[2]

        # clearing old figure

        self.figure.clear()
        
        # Plotting the mosaic.
        norm = simple_norm(array, 'sqrt', percent=99.)

        self.ax = plt.subplot(projection=wcs_out)

        self.ax.imshow(array, cmap='Greys', origin='lower', norm=norm)
        self.ax.set_xlabel('Right Ascension', fontsize=15)
        self.ax.set_ylabel('Declination', fontsize=15)
        self.ax.grid(color='white', ls='solid', b=True)
        add_scalebar(self.ax, label="1'", length=1 * u.arcmin, 
                     color='black', label_top=True)

        self.annotation = self.ax.annotate(
            text='',
            xy=(0, 0),
            xytext=(7, 7), # distance from x, y
            textcoords='offset points',
            bbox={'boxstyle': 'round', 'fc': 'w'},
            arrowprops={'arrowstyle': '->'},
            xycoords='axes fraction'
        )
        self.annotation.set_visible(False)

        self.targets = []
        self.fovs = []


        for sky in self.skys:
            target = self.ax.plot(sky.coords.ra.value, sky.coords.dec.value, 
                    '+', color='blue', mfc='None', 
                    transform=self.ax.get_transform('world'), 
                    ms=20, mew=0.5) # Center marker
            
            self.targets.append(target[0])

            d = (sky.fov / 2) * u.arcmin
            d_deg = d.to(u.deg).value

            anchor_ra = sky.coords.ra.value - d_deg
            anchor_de = sky.coords.dec.value - d_deg

            q = Quadrangle((anchor_ra, anchor_de)*u.deg, sky.fov*u.arcmin, sky.fov*u.arcmin,
                    edgecolor='red', facecolor='none',
                    transform=self.ax.get_transform('world'), linewidth=0.8, linestyle='-')

            self.fovs.append(q)
            self.ax.add_patch(q)
    
        self.figure.add_subplot(self.ax)

        self.canvas.draw()

        self.update_progbar((100, "Successfully plotted mosaic."))
        print("Succesfully plotted mosaic.")

    def motion_hover(self, event):

        if self.ax != 'Empty' and not self.single_img:
            annotation_visibility = self.annotation.get_visible()
            any_hovered = False  # Flag to track if any target is hovered
            
            if event.inaxes == self.ax:
                for sky, target_obj, q in zip(self.skys, self.targets, self.fovs):  # Loop through each sky, target, and quadrangle
                    is_contained, _ = target_obj.contains(event)
                    if is_contained:
                        # Access the corresponding date
                        hovered_date = sky.date.value

                        # Format the annotation text with the date
                        text_label = f"{hovered_date}"
                        self.annotation.set_text(text_label)
                        
                        # Update annotation position and visibility
                        self.annotation.set_visible(True)

                        # Show the corresponding quadrangle
                        q.set(visible=True)

                        self.canvas.draw_idle()
                        any_hovered = True  # A target is hovered
                    else:
                        # Hide quadrangles not hovered
                        q.set(visible=False)
                
                # If no target is hovered, hide the annotation
                if not any_hovered and annotation_visibility:
                    self.annotation.set_visible(False)
                    self.canvas.draw_idle()

        else:
            pass


    def single_plot(self, coords, fov, wcs, data):
        '''
        Returns None.

        Plots a single image on the canvas.
        '''

        self.single_img = True
        self.figure.clear()

        norm = simple_norm(data, 'sqrt', percent=99.)

        self.ax = plt.subplot(projection=wcs)

        self.ax.imshow(data, cmap='Greys', origin='lower', norm=norm)
        self.ax.set_xlabel('Right Ascension', fontsize=15)
        self.ax.set_ylabel('Declination', fontsize=15)
        self.ax.grid(color='white', ls='solid', b=True)

        

        self.target = self.ax.plot(coords.ra.value, coords.dec.value, '+', color='blue', mfc='None', 
                    transform=self.ax.get_transform('world'), 
                    ms=20, mew=0.5) # Center marker
        
        add_scalebar(self.ax, label="1'", length=1 * u.arcmin, 
                     color='black', label_top=True)
        
        
        
        d = (fov / 2) * u.arcmin
        d_deg = d.to(u.deg).value

        anchor_ra = coords.ra.value - d_deg
        anchor_de = coords.dec.value - d_deg

        if float(self.rot_inp.text()) > 0:
            angle = -float(self.rot_inp.text())
        else:
            angle = float(self.rot_inp.text())

        self.q = Quadrangle((anchor_ra, anchor_de)*u.deg, fov*u.arcmin, fov*u.arcmin,
                    edgecolor='red', facecolor='none',
                    transform=self.ax.get_transform('world'), linewidth=0.8, linestyle='-')
        
        rotation = transforms.Affine2D().rotate_deg_around(coords.ra.value, coords.dec.value, angle)
        self.q.set_transform(rotation + self.ax.get_transform('world'))
        self.ax.add_patch(self.q)
    
        
        self.figure.add_subplot(self.ax)
        self.figure.tight_layout()

        self.canvas.draw()

        self.update_progbar((100, "Succesfully plotted image."))
        print("Succesfully plotted image.")

    def update_angle(self, deg: int):
        '''
        Returns int.

        For FOV rectangle rotation and the 'angle' parameter in 
        'plot_fov'.
        '''

        self.angle = deg


    def update_bestseen(self, best):
        self.best_seen.setText(best)

    def update_flags(self, b_notice: str):
        '''
        Returns None.

        Updates the labels that will hold the flag notices.
        '''
        
        self.brightest_label.setText(b_notice)
        #self.dist_label.setText(dist_notice)

    def create_table(self):

        labels = [
            'mag', 'RA (deg)', 'DEC (deg)', 'd (arcmin)', 'Time'
        ]
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(labels)

    def update_table(self, content, mag):

        self.table.setRowCount(len(content))

        row = 0
        for item in content:
            self.table.setItem(row, 0, QTableWidgetItem(f'{item["mag"]:.3f}'))
            self.table.setItem(row, 1, QTableWidgetItem(f'{item["ra"]}'))
            self.table.setItem(row, 2, QTableWidgetItem(f'{item["dec"]}'))
            self.table.setItem(row, 3, QTableWidgetItem(f'{item["dist"].to(u.arcmin).value:.3f}'))
            self.table.setItem(row, 4, QTableWidgetItem(item['date'].value.rstrip("000").rstrip(".")))
            row += 1

    def calculate_pa(self):

        ra = [x.text() for x in self.ra_input]
        dec = [x.text() for x in self.dec_input]

        submit_ra = f'{ra[0]} {ra[1]} {ra[2]}'
        submit_dec = f'{dec[0]} {dec[1]} {dec[2]}'
        
        self.signal_pa.emit(submit_ra, submit_dec)

    def update_rot(self, angle):
        self.rot_inp.setText(str(angle))


    def exit(self):
        self.close()



class ErrorWindow(QDialog):
    def __init__(self, msg=None):
        super().__init__()
        self.msg = msg
        self.initialize_gui()  

        
    def initialize_gui(self):    
        self.setWindowTitle("Error Window")
        self.setGeometry(450, 300, 70, 100)

        self.error_msg1 = QLabel('ERROR', self)
        self.error_msg1.setStyleSheet("font: bold 30px")

        self.error_msg = QLabel(f"{self.msg}", self)
        self.error_msg.setStyleSheet("font: 20px")

        vbox = QVBoxLayout()
        vbox.addWidget(self.error_msg1, alignment=Qt.AlignCenter)
        vbox.addWidget(self.error_msg, alignment=Qt.AlignCenter)

        self.setLayout(vbox)
        
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    ex = MainWindow()
    sys.exit(app.exec())
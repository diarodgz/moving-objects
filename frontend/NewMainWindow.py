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
    QTableWidgetItem,
    QDateTimeEdit,
    QTabWidget,
    QGridLayout,
    QStyleFactory
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


class MainWindow(QDialog):

    '''
    Class in charge of everything to do with the GUI
    aspect of the program. Very minimal tasks besides organizing GUI
    and preparing inputs to communicate to the backend via signals.
    '''
    signal_valid_input = pyqtSignal(dict)
    signal_thread = pyqtSignal(str)
    signal_pa = pyqtSignal(str, str, str)
    signal_date = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.single_img = False
        self.initialize_gui()

    def initialize_gui(self):
        # Initializing all of the gui widgets.

        self.setWindowTitle("Moving Objects")
        self.setGeometry(100, 100, 1000, 700)
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        QApplication.setPalette(QApplication.style().standardPalette())

        # self.createTopLayout()
        self.createLeftGroupBox()
        self.createMiddleGroupBox()
        self.createRightGroupBox()
        self.createCoordBox1()
        self.createCoordBox2()
        self.createCoordBox3()
        self.createOBBox1()
        self.createOBBox2()
        self.createOBBox3()
        self.createTabBox()
        self.createPlotBox()
        self.createTableBox()
        self.createButtonGroup()

        #self.title = QLabel("Moving Object Tool", self)
        #self.title.setStyleSheet("font: bold 30px")

        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.tab, 0, 0, 1, 3)
        self.mainLayout.addLayout(self.plotBox, 1, 0)
        self.mainLayout.addLayout(self.tableBox, 1, 1)
        self.mainLayout.addLayout(self.button_grid, 2, 1)
        self.mainLayout.setColumnStretch(0, 400)
        self.setLayout(self.mainLayout)

    def createTopLayout(self):
        self.title = QLabel("Moving Object Tool", self)
        self.title.setStyleSheet("font: bold 30px")
        
        self.best_seen = QLabel('', self)

        

    def createLeftGroupBox(self):

        self.leftGroupBox = QHBoxLayout()

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        self.target_label = QLabel('Target ID', self)
        self.target_inp = QLineEdit(self)
        self.target_inp.setPlaceholderText("e.g. 'Ceres', '3'")
        self.target_inp.setFixedWidth(168)

        self.from_label = QLabel('Start', self)
        self.end_label = QLabel('End', self)

        self.datetime_start = QDateTimeEdit(self, calendarPopup=True)
        self.datetime_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.datetime_end = QDateTimeEdit(self, calendarPopup=True)
        self.datetime_end.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        label_vbox.addWidget(self.target_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.from_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.end_label, alignment=Qt.AlignCenter)

        input_vbox.addWidget(self.target_inp, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.datetime_start, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.datetime_end, alignment=Qt.AlignCenter)

        self.leftGroupBox.addLayout(label_vbox)
        self.leftGroupBox.addLayout(input_vbox)

    def createMiddleGroupBox(self):

        self.middleGroupBox = QHBoxLayout()
        
        self.step_label = QLabel('Step', self)
        self.scale_label = QLabel('Time Scale', self)
        self.inst_label = QLabel('Instrument', self)

        self.step_inp = QLineEdit('', self)
        self.step_cbox = QComboBox()
        self.steps = ["s", "min", "h", "d"]
        self.step_cbox.addItems(self.steps)
        self.step_cbox.setCurrentIndex(1)

        self.utc_button = QRadioButton('UTC', self)
        self.ut_button = QRadioButton('UT', self)
        self.lst_button = QRadioButton('LST', self)

        self.time_group = QButtonGroup(self)
        self.time_group.addButton(self.utc_button)
        self.time_group.addButton(self.ut_button)
        self.time_group.addButton(self.lst_button)
        
        self.utc_button.setChecked(True)

        self.rot_label = QLabel('Rotation (deg)', self)
        self.rot_inp = QLineEdit(self)
        self.rot_inp.setText('0')
        self.rot_inp.setFixedWidth(150)

        self.calc_button = QPushButton('Calculate PA', self)
        self.calc_button.clicked.connect(self.calculate_pa)

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        label_vbox.addWidget(self.scale_label)
        label_vbox.addWidget(self.step_label)
        label_vbox.addWidget(self.rot_label)

        buttons = QHBoxLayout()
        buttons.addWidget(self.utc_button)
        buttons.addWidget(self.ut_button)
        buttons.addWidget(self.lst_button)

        step = QHBoxLayout()
        step.addWidget(self.step_inp)
        step.addWidget(self.step_cbox)

        self.rot_hbox = QHBoxLayout()
        self.rot_hbox.addWidget(self.rot_inp)
        self.rot_hbox.addWidget(self.calc_button)

        input_vbox.addLayout(buttons)
        input_vbox.addLayout(step)
        input_vbox.addLayout(self.rot_hbox)
        

        self.middleGroupBox.addLayout(label_vbox)
        self.middleGroupBox.addLayout(input_vbox)

    def createRightGroupBox(self):

        self.rightGroupBox = QHBoxLayout()
        
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

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        label_vbox.addWidget(self.inst_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.cat_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.hips_label, alignment=Qt.AlignCenter)

        input_vbox.addWidget(self.inst_cbox, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.cat_cbox, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.hips_cbox, alignment=Qt.AlignCenter)

        self.rightGroupBox.addLayout(label_vbox)
        self.rightGroupBox.addLayout(input_vbox)

    def createPlotBox(self):

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = 'Empty'
        self.canvas.mpl_connect('motion_notify_event', self.motion_hover)

        self.plotBox = QVBoxLayout()
        self.plotBox.addWidget(self.toolbar)
        self.plotBox.addWidget(self.canvas)

    def createTableBox(self):

        self.tableBox = QHBoxLayout()

        labels = [
            'mag', 'RA (deg)', 'DEC (deg)', 'd (arcmin)', 'Time'
        ]
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(labels)
        self.tableBox.addWidget(self.table)

    def createCoordBox1(self):

        self.ra_label = QLabel('RA', self)
        self.ra = QDateTimeEdit(self, calendarPopup=False)
        self.ra.setDisplayFormat("HH:mm:ss")

        self.dec_label = QLabel('DEC', self)
        #self.dec = QDateTimeEdit(self, calendarPopup=False)
        #self.dec.setDisplayFormat("HH:mm:ss")

        self.dec = QLineEdit(self)
        self.dec.setPlaceholderText('e.g. YYYY-MM-DD')
        #self.dec.setFixedWidth(125)
        self.dec.setInputMask('00:00:00;0')

        self.dec_sign = QLineEdit('', self)
        self.dec_sign.setPlaceholderText('±')
        self.dec_sign.setFixedWidth(15)

        self.name_label = QLabel('Name', self)
        self.name_inp = QLineEdit('', self)
        self.name_inp.setPlaceholderText('e.g. NGC 4755')

        

        self.coord_box1 = QHBoxLayout()

        dec_hbox = QHBoxLayout()
        dec_hbox.addWidget(self.dec_sign)
        dec_hbox.addWidget(self.dec)

        label_vbox = QVBoxLayout()
        label_vbox.addWidget(self.ra_label)
        label_vbox.addWidget(self.dec_label)
        label_vbox.addWidget(self.name_label)

        input_vbox = QVBoxLayout()
        input_vbox.addWidget(self.ra)
        input_vbox.addLayout(dec_hbox)
        input_vbox.addWidget(self.name_inp)

        self.coord_box1.addLayout(label_vbox)
        self.coord_box1.addLayout(input_vbox)

    def createCoordBox2(self):

        self.coord_box2 = QHBoxLayout()
        # self.coord_box2.addLayout(self.rot_hbox)
        self.rot_coords_inp = QLineEdit(self)
        self.rot_coords_inp.setText('0')
        self.rot_coords_label = QLabel('Rotation (deg)', self)

        self.rot_coords_button = QPushButton('Calculate PA')
        self.rot_coords_button.clicked.connect(self.calculate_pa)

        self.time_coords_label = QLabel('Time', self)
        self.time_coords_inp = QDateTimeEdit(self, calendarPopup=False)
        self.time_coords_inp.setDisplayFormat(("yyyy-MM-dd HH:mm:ss"))
        self.time_coords_cbox = QComboBox()

        time_scales = [
            key for key in config['T_SCALE'].keys()
        ]
        self.time_coords_cbox.addItems(time_scales)

        self.rot_coords_hbox = QHBoxLayout()
        self.rot_coords_hbox.addWidget(self.rot_coords_inp)
        self.rot_coords_hbox.addWidget(self.rot_coords_button)

        self.time_coords_hbox = QHBoxLayout()
        self.time_coords_hbox.addWidget(self.time_coords_inp)
        self.time_coords_hbox.addWidget(self.time_coords_cbox)

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        label_vbox.addWidget(self.rot_coords_label)
        label_vbox.addWidget(self.time_coords_label)

        input_vbox.addLayout(self.rot_coords_hbox)
        input_vbox.addLayout(self.time_coords_hbox)

        self.coord_box2.addLayout(label_vbox)
        self.coord_box2.addLayout(input_vbox)

    def createCoordBox3(self):

        self.coord_box3 = QHBoxLayout()
        
        # Instrument scroll menu
        self.inst_coords_label = QLabel('Instrument', self)
        self.inst_coords_cbox = QComboBox()
        instruments = [
            key for key in config['INSTRUMENT'].keys()
        ]

        self.inst_coords_cbox.addItems(instruments)

        # Catalog scroll menu
        self.cat_coords_label = QLabel('Catalog', self)
        self.cat_coords_cbox = QComboBox()
        cats= [
            key for key in config['CATALOG'].keys()
        ]

        self.cat_coords_cbox.addItems(cats)

        # HIPS Survey scroll menu
        self.hips_coords_label = QLabel('HIPS Survey', self)
        hips = [
            key for key in config['HIPS_SURVEY'].keys()
        ]
        self.hips_coords_cbox = QComboBox()
        self.hips_coords_cbox.addItems(hips)
        self.hips_coords_cbox.setCurrentIndex(1)

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        label_vbox.addWidget(self.inst_coords_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.cat_coords_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.hips_coords_label, alignment=Qt.AlignCenter)

        input_vbox.addWidget(self.inst_coords_cbox, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.cat_coords_cbox, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.hips_coords_cbox, alignment=Qt.AlignCenter)

        self.coord_box3.addLayout(label_vbox)
        self.coord_box3.addLayout(input_vbox)

    def createOBBox1(self):
        self.ob_box1 = QHBoxLayout()

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        self.ob_label = QLabel('OB ID', self)
        self.ob_inp = QLineEdit(self)
        # self.ob_inp.setPlaceholderText("e.g. 'Ceres', '3'")
        self.ob_inp.setFixedWidth(168)

        self.from_ob_label = QLabel('Start', self)
        self.end_ob_label = QLabel('End', self)

        self.datetime_ob_start = QDateTimeEdit(self, calendarPopup=True)
        self.datetime_ob_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.datetime_ob_end= QDateTimeEdit(self, calendarPopup=True)
        self.datetime_ob_end.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        label_vbox.addWidget(self.ob_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.from_ob_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.end_ob_label, alignment=Qt.AlignCenter)

        input_vbox.addWidget(self.ob_inp, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.datetime_ob_start, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.datetime_ob_end, alignment=Qt.AlignCenter)

        self.ob_box1.addLayout(label_vbox)
        self.ob_box1.addLayout(input_vbox)

    def createOBBox2(self):
        self.ob_box2 = QHBoxLayout()
        
        self.step_ob_label = QLabel('Step', self)
        self.scale_ob_label = QLabel('Time Scale', self)

        self.step_ob_inp = QLineEdit('', self)
        self.step_ob_cbox = QComboBox()
        self.steps = ["s", "min", "h", "d"]
        self.step_ob_cbox.addItems(self.steps)
        self.step_ob_cbox.setCurrentIndex(1)

        self.utc_ob_button = QRadioButton('UTC', self)
        self.ut_ob_button = QRadioButton('UT', self)
        self.lst_ob_button = QRadioButton('LST', self)

        self.time_ob_group = QButtonGroup(self)
        self.time_ob_group.addButton(self.utc_ob_button)
        self.time_ob_group.addButton(self.ut_ob_button)
        self.time_ob_group.addButton(self.lst_ob_button)

        self.utc_ob_button.setChecked(True)

        self.rot_ob_label = QLabel('Rotation (deg)', self)
        self.rot_ob_inp = QLineEdit(self)
        self.rot_ob_inp.setText('0')
        self.rot_ob_inp.setFixedWidth(150)

        self.calc_button_ob = QPushButton('Calculate PA', self)
        self.calc_button_ob.clicked.connect(self.calculate_pa)

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        label_vbox.addWidget(self.scale_ob_label)
        label_vbox.addWidget(self.step_ob_label)
        label_vbox.addWidget(self.rot_ob_label)

        buttons = QHBoxLayout()
        buttons.addWidget(self.utc_ob_button)
        buttons.addWidget(self.ut_ob_button)
        buttons.addWidget(self.lst_ob_button)

        step = QHBoxLayout()
        step.addWidget(self.step_ob_inp)
        step.addWidget(self.step_ob_cbox)

        self.rot_ob_hbox = QHBoxLayout()
        self.rot_ob_hbox.addWidget(self.rot_ob_inp)
        self.rot_ob_hbox.addWidget(self.calc_button_ob)

        input_vbox.addLayout(buttons)
        input_vbox.addLayout(step)
        input_vbox.addLayout(self.rot_ob_hbox)
        
        self.ob_box2.addLayout(label_vbox)
        self.ob_box2.addLayout(input_vbox)

    def createOBBox3(self):

        self.ob_box3 = QHBoxLayout()
        
        # Instrument scroll menu
        self.inst_ob_label = QLabel('Instrument', self)
        self.inst_ob_cbox = QComboBox()
        instruments = [
            key for key in config['INSTRUMENT'].keys()
        ]

        self.inst_ob_cbox.addItems(instruments)

        # Catalog scroll menu
        self.cat_ob_label = QLabel('Catalog', self)
        self.cat_ob_cbox = QComboBox()
        cats= [
            key for key in config['CATALOG'].keys()
        ]

        self.cat_ob_cbox.addItems(cats)

        # HIPS Survey scroll menu
        self.hips_ob_label = QLabel('HIPS Survey', self)
        hips = [
            key for key in config['HIPS_SURVEY'].keys()
        ]
        self.hips_ob_cbox = QComboBox()
        self.hips_ob_cbox.addItems(hips)
        self.hips_ob_cbox.setCurrentIndex(1)

        label_vbox = QVBoxLayout()
        input_vbox = QVBoxLayout()

        label_vbox.addWidget(self.inst_ob_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.cat_ob_label, alignment=Qt.AlignCenter)
        label_vbox.addWidget(self.hips_ob_label, alignment=Qt.AlignCenter)

        input_vbox.addWidget(self.inst_ob_cbox, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.cat_ob_cbox, alignment=Qt.AlignCenter)
        input_vbox.addWidget(self.hips_ob_cbox, alignment=Qt.AlignCenter)

        self.ob_box3.addLayout(label_vbox)
        self.ob_box3.addLayout(input_vbox)

    def createTabBox(self):
        self.tab = QTabWidget()

        targ_tab = QWidget()
        targ_box = QGridLayout()

        targ_box.addLayout(self.leftGroupBox, 0, 0)
        targ_box.addLayout(self.middleGroupBox, 0, 1)
        targ_box.addLayout(self.rightGroupBox, 0, 2)
        targ_box.setColumnStretch(0, 1)
        #targ_box.setColumnStretch(1, 1)
        targ_box.setColumnStretch(2, 1)
        targ_tab.setLayout(targ_box)
        

        coord_tab = QWidget()
        coord_box = QGridLayout()
        coord_box.addLayout(self.coord_box1, 0, 0)
        coord_box.addLayout(self.coord_box2, 0, 1)
        coord_box.addLayout(self.coord_box3, 0, 2)
        coord_box.setColumnStretch(0, 1)
        #coord_box.setColumnStretch(1, 1)
        coord_box.setColumnStretch(2, 1)
        coord_tab.setLayout(coord_box)

        ob_tab = QWidget()
        ob_box = QGridLayout()
        ob_box.addLayout(self.ob_box1, 0, 0)
        ob_box.addLayout(self.ob_box2, 0, 1)
        ob_box.addLayout(self.ob_box3, 0, 2)
        ob_box.setColumnStretch(0, 1)
        #ob_box.setColumnStretch(1, 1)
        ob_box.setColumnStretch(2, 1)
        ob_tab.setLayout(ob_box)

        self.tab.addTab(targ_tab, "Moving Target")
        self.tab.addTab(ob_tab, "OB ID")
        self.tab.addTab(coord_tab, "Coordinates")

    def createButtonGroup(self):
        self.button_grid = QGridLayout()

        self.query_button = QPushButton('QUERY', self)
        self.query_button.clicked.connect(self.clicked_query)

        self.exit_button = QPushButton('EXIT', self)
        self.exit_button.clicked.connect(self.clicked_exit)

        self.stop_button = QPushButton('CANCEL')

        self.button_grid.addWidget(self.exit_button, 0, 0)
        self.button_grid.addWidget(self.query_button, 0, 4)
        self.button_grid.addWidget(self.stop_button, 0, 5)

    # Creating all of the methods that will send signals to the backend.

    def clicked_query(self):
        '''
        Response to clicking the query button.
        '''

        if self.tab.currentIndex() == 0:
            inputs = {}

            inputs['info'] = 'targ'
            inputs['id'] = self.target_inp.text()
            inputs['start'] = self.datetime_start.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            inputs['end'] = self.datetime_end.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            inputs['t_scale'] = self.time_group.checkedButton().text()
            inputs['step'] = self.step_inp.text()
            inputs['step_u'] = self.step_cbox.currentText()
            inputs['n_result'] = config['NUM_RESULTS']
            inputs['inst'] = self.inst_cbox.currentText()
            #inputs['rot'] = (self.rot_inp.text())
            inputs['cat'] = (self.cat_cbox.currentText())
            inputs['hips'] = (self.hips_cbox.currentText())

            self.signal_valid_input.emit(inputs)
        elif self.tab.currentIndex() == 1:
            inputs = {}

            inputs['info'] = 'ob'
            inputs['id'] = self.ob_inp.text()
            inputs['start'] = self.datetime_ob_start.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            inputs['end'] = self.datetime_ob_end.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            inputs['t_scale'] = self.time_ob_group.checkedButton().text()
            inputs['step'] = self.step_ob_inp.text()
            inputs['step_u'] = self.step_ob_cbox.currentText()
            inputs['n_result'] = config['NUM_RESULTS']
            inputs['inst'] = self.inst_ob_cbox.currentText()
            #inputs['rot'] = (self.rot_ob_inp.text())
            inputs['cat'] = (self.cat_ob_cbox.currentText())
            inputs['hips'] = (self.hips_ob_cbox.currentText())
            
            self.signal_valid_input.emit(inputs)
        else:
            inputs = {}

            inputs['info'] = 'coords'
            inputs['ra'] = self.ra.dateTime().toString("HH:mm:ss")
            inputs['dec'] = self.dec_sign.text() + self.dec.text()
            inputs['name'] = self.name_inp.text()
            inputs['t_scale'] = self.time_coords_cbox.currentText()
            inputs['time'] = self.time_coords_inp.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            inputs['inst'] = self.inst_coords_cbox.currentText()
            inputs['rot'] = (self.rot_coords_inp.text())
            inputs['cat'] = (self.cat_coords_cbox.currentText())
            inputs['hips'] = (self.hips_coords_cbox.currentText())

            self.signal_valid_input.emit(inputs)

    def plot(self, skys, wcs, data):

        '''
        Contains all of the steps necessary to create a plot
        using matpotlib. Takes a list that contains the list
        of skys, the optimal WCS, and the final array for plotting.
        '''

        self.skys = skys

        # clearing old figure

        self.figure.clear()
        
        # Plotting the mosaic.
        norm = simple_norm(data, 'sqrt', percent=99.)

        self.ax = plt.subplot(projection=wcs)

        self.ax.imshow(data, cmap='Greys', origin='lower', norm=norm)
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


        for sky in skys:
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

        # self.update_progbar((100, "Successfully plotted mosaic."))
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

        # self.update_progbar((100, "Succesfully plotted image."))
        print("Succesfully plotted image.")

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
        
        if self.tab.currentIndex() == 0:
            self.signal_pa.emit(self.datetime_start.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
                            self.datetime_end.dateTime().toString("yyyy-MM-dd HH:mm:ss"))
        elif self.tab.currentIndex() == 1:
            self.signal_pa.emit(self.datetime_ob_start.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
                            self.datetime_ob_end.dateTime().toString("yyyy-MM-dd HH:mm:ss"))
        else:
            self.signal_pa.emit(self.ra.dateTime().toString("HH:mm:ss"), self.dec_sign.text() + self.dec.text(), 
                                self.time_coords_inp.dateTime().toString("yyyy-MM-dd HH:mm:ss"))
            
    def update_bestseen(self, best):
        self.best_seen.setText(best)

    def clicked_exit(self):
        self.exit()

    def update_rot(self, angle):

        if self.tab.currentIndex() == 0:
            self.rot_inp.setText(str(angle))
        elif self.tab.currentIndex() == 1:
            self.rot_ob_inp.setText(str(angle))
        else:
            self.rot_coords_inp.setText(str(angle))

    def error(self, msg):
        # Dialogue box appears in case of error.

        dlg = ErrorWindow(msg)
        if dlg.exec():
            pass  

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
    gallery = MainWindow()
    gallery.show()
    sys.exit(app.exec())
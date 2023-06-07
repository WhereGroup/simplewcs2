"""
        Simple WCS 2 - QGIS Plugin
        ---   v0.2   ---
        Basic support for OGC WCS 2.X

        created by Landesvermessung und Geobasisinformation Brandenburg
        email: marcus.mohr@geobasis-bb.de
        licence: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

        Functions are written in mixedCase, see https://docs.qgis.org/testing/en/docs/developers_guide/codingstandards.html
"""

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from .simplewcs_dialog import SimpleWCSDialog
from .resources import *
from .wcs import *
from .coverage import *
from .utils import crsAsOgcUri, switchCrsUriToOpenGis
from qgis.core import QgsApplication, QgsMessageLog, QgsRasterLayer, QgsProject, Qgis, QgsTask, \
    QgsCoordinateReferenceSystem, QgsPointXY, QgsCoordinateTransform
from urllib.error import HTTPError, URLError
from urllib.request import Request
from urllib.parse import urlparse

import os.path, urllib

logheader = 'Simple WCS 2'

class SimpleWCS:


    def __init__(self, iface):
        """
        The constructor!

        :param iface: iface
        """

        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SimpleWCS_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # instance attributes
        self.iface = iface

        self.actions = []
        self.menu = self.tr(u'&Simple WCS 2')
        self.firstStart = None
        self.wcs = ''
        self.acceptedVersions = ['2.1.0', '2.0.1', '2.0.0']

        self.task = None  # task as instance variable so no garbage collector eats it in the wrong moment


    def tr(self, message):
        """
        Returns a translated string
        """

        return QCoreApplication.translate('SimpleWCS', message)


    def add_action(
        self,
        iconPath,
        text,
        callback,
        enabledFlag=True,
        addToMenu=True,
        addToToolbar=True,
        statusTip=None,
        whatsThis=None,
        parent=None):

        """
        Adds plugin icon to toolbar
        """

        icon = QIcon(iconPath)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabledFlag)

        if statusTip is not None:
            action.setStatusTip(statusTip)

        if whatsThis is not None:
            action.setWhatsThis(whatsThis)

        if addToToolbar:
            self.iface.addToolBarIcon(action)

        if addToMenu:
            self.iface.addPluginToRasterMenu(self.menu, action)

        self.actions.append(action)

        return action


    def initGui(self):
        """
        Create the menu entries and toolbar icons inside the QGIS GUI.
        """

        icon_path = ':/plugins/simplewcs/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Simple WCS 2'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.firstStart = True


    def unload(self):
        """
        Removes the plugin menu item and icon from QGIS GUI.
        """

        for action in self.actions:
            self.iface.removePluginRasterMenu(self.menu, action)
            #self.iface.removePluginRasterMenu(self.tr(u'&Simple WCS 2'),action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """
        Run that thing!
        """

        if self.firstStart == True:
            self.firstStart = False
            self.dlg = SimpleWCSDialog()

            self.dlg.cbVersion.addItems(self.acceptedVersions)
            self.dlg.cbVersion.setCurrentIndex(1)

            self.dlg.btnGetCapabilities.clicked.connect(self.getCapabilities)
            self.dlg.btnGetCapabilities.setEnabled(False)

            self.dlg.leUrl.textChanged.connect(self.enableBtnGetCapabilities)

            self.dlg.btnGetCoverage.clicked.connect(self.getCovTask)
            self.dlg.btnGetCoverage.setEnabled(False)

            self.iface.mapCanvas().extentsChanged.connect(self.setExtentLabel)

        self.dlg.show()

        result = self.dlg.exec_()


    def getCapabilities(self):
        self.cleanTabGetCoverage()

        self.wcs = ''

        baseUrl = self.dlg.leUrl.text()

        version = self.dlg.cbVersion.currentText()

        params = {"REQUEST": "GetCapabilities", "SERVICE": "WCS", "Version": version}
        querystring = urllib.parse.urlencode(params)
        url = self.checkUrlSyntax(baseUrl)
        xmlResponse = self.requestXML(url + querystring)

        capabilities = xml.etree.ElementTree.parse(xmlResponse).getroot()
        self.wcs = WCS(capabilities)

        versions = self.wcs.getVersions()

        if version in versions:
            self.setTabGetCoverage(version)
            self.setTabInformation()
            versionsOk = True
        else:
            for c_version in versions:
                # take the first match of accepted versions
                if c_version in self.acceptedVersions:
                    self.setTabGetCoverage(c_version)
                    self.setTabInformation()
                    versionsOk = True
                    break
                else:
                    versionsOk = False

        if versionsOk is False:
            self.logWarnMessage('WCS does not support one of the following Versions: ' + ', '.join(self.acceptedVersions))
            self.openLog()


    def cleanTabGetCoverage(self):

        self.dlg.lblTitle.clear()

        self.dlg.cbCoverage.clear()

        self.dlg.cbCRS.clear()

        self.dlg.cbFormat.clear()

        self.dlg.btnGetCoverage.setEnabled(False)

        self.dlg.lblExtent.clear()


    def setTabGetCoverage(self, version):
        """
        Collects information about the wcs and shows them in GUI
        - supports only tiff at the moment!
        """

        title = self.wcs.getTitle()
        if title is None:
            title = self.tr("Unknown, not communicated by service")
        self.dlg.lblTitle.setText(title)

        self.dlg.lblVersion.setText(version)

        coverages = self.wcs.getCoverageIds()
        for coverage in coverages:
            self.dlg.cbCoverage.addItem(coverage)

        crsx = self.wcs.getCRS()
        for crs in crsx:
            self.dlg.cbCRS.addItem(crs)

        formats = self.wcs.getFormats()
        for format in formats:
            if 'tiff' in format:
                self.dlg.cbFormat.addItem(format)

        if any('tiff' in format for format in formats):
            self.dlg.btnGetCoverage.setEnabled(True)
        else:
            self.dlg.cbFormat.addItem('no tiff available')
            self.dlg.cbFormat.setEnabled(False)

        self.setExtentLabel()

        self.dlg.tabWidget.setCurrentIndex(1)


    def setTabInformation(self):
        provider = self.wcs.getProvider()
        if provider is None:
            provider = self.tr("Unknown, not communicated by service")
        self.dlg.lblProvider.setText(provider)

        fees = self.wcs.getFees()
        if fees is None:
            fees = self.tr("Unknown, not communicated by service")
        self.dlg.lblFees.setText(fees)

        constraints = self.wcs.getConstraints()
        if constraints is None:
            constraints = self.tr("Unknown, not communicated by service")
        self.dlg.lblConstraints.setText(constraints)


    def setExtentLabel(self):
        """
        Collect current extent from mapCanvas and shows it in GUI
        """

        extent = self.iface.mapCanvas().extent().toString()
        coordinates = self.roundExtent(extent)
        extent = str(coordinates[0]) + ', ' + str(coordinates[1]) + ', ' + str(coordinates[2]) + ', ' + str(coordinates[3])
        self.dlg.lblExtent.setText(extent)


    def roundExtent(self, extent):
        extent = extent.split(",")
        extentDump = extent[1].split(" : ")
        coord0 = round(float(extent[0]), 7)
        coord1 = round(float(extentDump[0]), 7)
        coord2 = round(float(extentDump[1]), 7)
        coord3 = round(float(extent[2]), 7)

        coordinates = []
        coordinates.append(coord0)
        coordinates.append(coord1)
        coordinates.append(coord2)
        coordinates.append(coord3)

        return coordinates


    def describeCoverage(self, covId):
        params = {"REQUEST": "DescribeCoverage", "SERVICE": "WCS", "VERSION": "2.0.1", "COVERAGEID": covId}
        querystring = urllib.parse.urlencode(params)

        describeCoverageUrl = self.wcs.getDescribeCoverageUrl()
        url = self.checkUrlSyntax(describeCoverageUrl)
        xmlResponse = self.requestXML(url + querystring)

        describeCoverageRoot = xml.etree.ElementTree.parse(xmlResponse).getroot()
        coverage = Coverage(describeCoverageRoot)

        return coverage


    def getCovTask(self):
        """Create an asynchronous QgsTask and add it to the taskManager."""
        self.getCovProgressBar()

        try:
            url, covId = self.getCovQueryStr()
        except ValueError as e:
            self.logWarnMessage(str(e))
            return

        # task as instance variable so on_finished works
        # ref https://gis.stackexchange.com/a/435487/51035
        # ref https://gis-ops.com/qgis-3-plugin-tutorial-background-processing/
        self.task = QgsTask.fromFunction(
            'Get Coverage', self.getCoverage, url, covId, on_finished=self.addRLayer, flags=QgsTask.CanCancel
        )
        QgsApplication.taskManager().addTask(self.task)

        self.dlg.btnGetCoverage.setEnabled(False)


    def getCoverage(self, task, url, covId):
        self.logInfoMessage('Requested URL: ' + url)

        try:
            file, header = urllib.request.urlretrieve(url)
        except HTTPError as e:
            self.logWarnMessage(str(e))
            self.logWarnMessage(str(e.read().decode()))
            return None
        except URLError as e:
            self.logWarnMessage(str(e))
            self.logWarnMessage(str(e.read().decode()))
            return None

        return {'file': file, 'coverage': covId}


    def addRLayer(self, exception, result=None):
        """
        Add the response layer to MapCanvas
        :param exception: Exception if one was raised in task function
        :param result: dict with "file" (path) and "coverage" as strings, set to None by default
            e.g. {'file': '/tmp/tmpu1igp2d4', 'coverage': 'dwd__Natural_Earth_Map'}
        :return:
        """
        if result:
            rlayer = QgsRasterLayer(result['file'], result['coverage'], 'gdal')
            QgsProject.instance().addMapLayer(rlayer)
        else:
            self.openLog()
            self.logWarnMessage('Error while loading Coverage!')

        self.dlg.btnGetCoverage.setEnabled(True)
        self.iface.messageBar().clearWidgets()
    def getCovQueryStr(self):
        """Returns a query string for an GetCoverage request with the current dialog settings.

        Raises:
            ValueError: If a OGC URI string could not be created for the map CRS
        """
        version = self.dlg.lblVersion.text()

        covId = self.dlg.cbCoverage.currentText()
        coverage = self.describeCoverage(covId)

        #range = coverage.getRange()
        #self.logInfoMessage(str(range))

        # output CRS must be one of the CRS offered by the service (as OGC URI), chosen by the user in the dialog
        outputCrs = self.dlg.cbCRS.currentText()

        # map CRS is our QGIS project/canvas CRS
        mapCrs = QgsProject.instance().crs()
        try:
            mapCrsUri = crsAsOgcUri(mapCrs)
        except:
            raise  # re-raise exception

        # the coverage has a bounding box in its original CRS
        # the subsetting coordinates must correspond to this unless a different subsetting CRS is set
        coverageCrsUri = coverage.getBoundingBoxCrsUri()
        if not coverageCrsUri.startswith("http://www.opengis.net/def/crs/"):
            self.logWarnMessage(f"Trying to adjust {coverageCrsUri} to point to www.opengis.net database")
            coverageCrsUri = switchCrsUriToOpenGis(coverageCrsUri)
        coverageCrs = QgsCoordinateReferenceSystem.fromOgcWmsCrs(coverageCrsUri)

        mapExtent = self.iface.mapCanvas().extent().toString()
        coordinates = self.roundExtent(mapExtent)
        topLeftPoint = QgsPointXY(coordinates[0], coordinates[1])
        bottomRightPoint = QgsPointXY(coordinates[2], coordinates[3])
        if mapCrsUri != coverageCrsUri:
            self.logInfoMessage(f"Transforming extent coordinates from {mapCrsUri} to {coverageCrsUri}")
            destCrs = QgsCoordinateReferenceSystem.fromOgcWmsCrs(coverageCrsUri)
            transformation = QgsCoordinateTransform(mapCrs, destCrs, QgsProject.instance())
            topLeftPoint = transformation.transform(topLeftPoint)
            bottomRightPoint = transformation.transform(bottomRightPoint)

        minX, maxX = sorted([topLeftPoint.x(), bottomRightPoint.x()])
        minY, maxY = sorted([topLeftPoint.y(), bottomRightPoint.y()])

        axisLabel0, axisLabel1 = coverage.getAxisLabels()

        # we need to check if QGIS considers the CRS axes "inverted"
        if coverageCrs.hasAxisInverted():
            # e.g. WGS84 or Gauß-Krüger where "north" (y/lat) comes before "east" (x/lon)
            subset0 = f"{axisLabel0}({minY},{maxY})"
            subset1 = f"{axisLabel1}({minX},{maxX})"
        else:
            # any standard x/y, e/n crs, e. g. UTM
            subset0 = f"{axisLabel0}({minX},{maxX})"
            subset1 = f"{axisLabel1}({minY},{maxY})"

        format = self.dlg.cbFormat.currentText()

        params = [
            ('REQUEST', 'GetCoverage'),
            ('SERVICE', 'WCS'),
            ('VERSION', version),
            ('COVERAGEID', covId),
            ('OUTPUTCRS', outputCrs),
            ('SUBSETTINGCRS', coverageCrsUri),
            ('FORMAT', format),
            ('SUBSET', subset0),
            ('SUBSET', subset1),
        ]

        querystring = urllib.parse.urlencode(params)

        getCoverageUrl = self.wcs.getGetCoverageUrl()
        url = self.checkUrlSyntax(getCoverageUrl)
        url = url + querystring

        return url, covId


    def getCovProgressBar(self):
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        progressMessageBar = self.iface.messageBar().createMessage("GetCoverage Request")
        progressMessageBar.layout().addWidget(self.progress)
        self.iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)


    def requestXML(self, url):
        self.logInfoMessage('Requested URL: ' + url)

        try:
            xmlReponse = urllib.request.urlopen(url)
        except HTTPError as e:
            self.logWarnMessage(str(e))
            self.logWarnMessage(str(e.read().decode()))
            self.openLog()
            return None
        except URLError as e:
            self.logWarnMessage(str(e))
            self.logWarnMessage(str(e.read().decode()))
            self.openLog()
            return None

        return xmlReponse


    def checkUrlSyntax(self, url):
        if '?' in url:
            if url.endswith('?'):
                newUrl = url
            elif url.endswith('&'):
                newUrl = url
            else:
                newUrl = url + '&'
        else:
            newUrl = url + '?'

        return newUrl


    def enableBtnGetCapabilities(self):
        if len(self.dlg.leUrl.text()) > 0:
            self.dlg.btnGetCapabilities.setEnabled(True)


    def logInfoMessage(self, msg):
        QgsMessageLog.logMessage(msg, logheader, Qgis.Info)


    def logWarnMessage(self, msg):
        QgsMessageLog.logMessage(msg, logheader, Qgis.Warning)


    def openLog(self):
        self.iface.mainWindow().findChild(QDockWidget, 'MessageLog').show()

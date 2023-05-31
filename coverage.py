"""
        Simple WCS 2 - QGIS Plugin
        Basic support for OGC WCS 2.X

        created by Landesvermessung und Geobasisinformation Brandenburg
        email: marcus.mohr@geobasis-bb.de
        licence: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
"""

import os.path, urllib, xml.etree.ElementTree

class Coverage:


    def __init__(self, coverage):
        wcs_ns = '{http://www.opengis.net/wcs/2.0}'
        gml_ns = '{http://www.opengis.net/gml/3.2}'
        gmlcov_ns = '{http://www.opengis.net/gmlcov/1.0}'
        swe_ns = '{http://www.opengis.net/swe/2.0}'

        self.coverage = coverage

        self.axisLabels = self.coverage.find(wcs_ns + 'CoverageDescription/' + gml_ns + 'boundedBy/' + gml_ns + 'Envelope').attrib['axisLabels']
        self.axisLabels = self.axisLabels.split(" ")

        self.range = []
        coverageDescription = self.coverage.find(wcs_ns + 'CoverageDescription')
        for field in coverageDescription.findall('.//' + gmlcov_ns + 'rangeType/' + swe_ns + 'DataRecord/' + swe_ns + 'field'):
            name = field.get('name')
            self.range.append(name)


    def getAxisLabels(self):
        return self.axisLabels


    def setAxisLabels(self, axisLabels):
        self.axisLabels = axisLabels


    def getRange(self):
        return self.range


    def setRange(self, range):
        self.range = range

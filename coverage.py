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

        coverageDescription = self.coverage.find(wcs_ns + 'CoverageDescription')

        envelope = coverageDescription.find(gml_ns + 'boundedBy/' + gml_ns + 'Envelope')
        self.boundingBoxCrsUri = envelope.attrib['srsName']
        if "crs-compound" in self.boundingBoxCrsUri:
            raise NotImplementedError(f"Compound CRS are not supported (yet): {self.boundingBoxCrsUri}")
        lowerCorner = [float(v) for v in envelope.find(gml_ns + "lowerCorner").text.split(" ")]
        upperCorner = [float(v) for v in envelope.find(gml_ns + "upperCorner").text.split(" ")]
        self.boundingBox = lowerCorner + upperCorner

        # We only support 2 axes for now  # TODO or can we just ignore non-spatial ones?
        self.axisLabels = envelope.attrib['axisLabels'].split(" ")
        if len(self.axisLabels) > 2:
            raise NotImplementedError(f"More than two axes are not supported (yet): {self.axisLabels}")

        self.range = []
        coverageDescription = self.coverage.find(wcs_ns + 'CoverageDescription')
        for field in coverageDescription.findall('.//' + gmlcov_ns + 'rangeType/' + swe_ns + 'DataRecord/' + swe_ns + 'field'):
            name = field.get('name')
            self.range.append(name)


    def getBoundingBoxCrsUri(self):
        return self.boundingBoxCrsUri


    def getBoundingBox(self):
        return self.boundingBox


    def getAxisLabels(self):
        return self.axisLabels


    def setAxisLabels(self, axisLabels):
        self.axisLabels = axisLabels


    def getRange(self):
        return self.range


    def setRange(self, range):
        self.range = range

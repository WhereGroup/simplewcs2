"""
        Simple WCS 2 - QGIS Plugin
        Basic support for OGC WCS 2.X

        created by Landesvermessung und Geobasisinformation Brandenburg
        email: marcus.mohr@geobasis-bb.de
        licence: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

        Functions are written in mixedCase, see https://docs.qgis.org/testing/en/docs/developers_guide/codingstandards.html
"""


class WCS:


    def __init__(self, capabilities):
        # TODO is it ok that these use .0 versions?
        ows_ns = '{http://www.opengis.net/ows/2.0}'
        wcs_ns = '{http://www.opengis.net/wcs/2.0}'
        crs_ns = '{http://www.opengis.net/wcs/crs/1.0}'  # was overwritten in loop below!
        crs_serviceextension_ns = '{http://www.opengis.net/wcs/service-extension/crs/1.0}'
        xlink_ns = '{http://www.w3.org/1999/xlink}'

        self.capabilities = capabilities

        self.describeCoverageUrl = self.capabilities.find(ows_ns + 'OperationsMetadata/' + ows_ns + 'Operation[@name="DescribeCoverage"]/' + ows_ns + 'DCP/' + ows_ns + 'HTTP/' + ows_ns + 'Get').attrib[xlink_ns + 'href']

        self.getCoverageUrl = self.capabilities.find(ows_ns + 'OperationsMetadata/' + ows_ns + 'Operation[@name="GetCoverage"]/' + ows_ns + 'DCP/' + ows_ns + 'HTTP/' + ows_ns + 'Get').attrib[xlink_ns + 'href']

        self.title = self.capabilities.find(ows_ns + 'ServiceIdentification/' + ows_ns + 'Title')

        self.provider = self.capabilities.find(ows_ns + 'ServiceProvider/' + ows_ns + 'ProviderName')

        self.fees = self.capabilities.find(ows_ns + 'ServiceIdentification/' + ows_ns + 'Fees')

        self.constraints = self.capabilities.find(ows_ns + 'ServiceIdentification/' + ows_ns + 'AccessConstraints')

        self.versions = []
        serviceIdentification = self.capabilities.find(ows_ns + 'ServiceIdentification')
        for version in serviceIdentification.findall('.//' + ows_ns + 'ServiceTypeVersion'):
            self.versions.append(version.text)

        self.crsx = []
        serviceMetadata = self.capabilities.find(wcs_ns + 'ServiceMetadata')
        for crs in serviceMetadata.findall('.//' + wcs_ns + 'Extension/' + crs_ns + 'CrsMetadata/' + crs_ns + 'crsSupported'):
            self.crsx.append(crs.text)

        # in case of wrong crs extension implementation  # TODO wrong or just different? are these specific WCS servers?
        if not self.crsx:
            for crs in serviceMetadata.findall('.//' + wcs_ns + 'Extension/' + crs_serviceextension_ns + 'crsSupported'):
                self.crsx.append(crs.text)

        # let's add another one, from a rasdaman powered WCS we got this
        if not self.crsx:
            for crs in serviceMetadata.findall('.//' + wcs_ns + 'Extension/' + crs_serviceextension_ns + 'CrsMetadata/' + crs_serviceextension_ns + 'crsSupported'):
                self.crsx.append(crs.text)

        self.formats = []
        for format in serviceMetadata.findall('.//' + wcs_ns + 'formatSupported'):
            self.formats.append(format.text)

        self.covIds = []
        contents = self.capabilities.find(wcs_ns + 'Contents')
        for coverage in contents.findall('.//' + wcs_ns + 'CoverageSummary/' + wcs_ns + 'CoverageId'):
            self.covIds.append(coverage.text)


    def getTitle(self):
        if self.title is not None:
            return self.title.text
        else:
            return None


    def setTitle(self, title):
        self.title = title


    def getProvider(self):
        if self.provider is not None:
            return self.provider.text
        else:
            return None


    def setProvider(self, provider):
        self.provider = provider


    def getFees(self):
        if self.fees is not None:
            return self.fees.text
        else:
            return None


    def setFees(self, fees):
        self.fees = fees


    def getConstraints(self):
        if self.constraints is not None:
            return self.constraints.text
        else:
            return None


    def setConstraints(self, constraints):
        self.constraints = constraints


    def getDescribeCoverageUrl(self):
        return self.describeCoverageUrl


    def setDescribeCoverageUrl(self, describeCoverageUrl):
        self.describeCoverageUrl = describeCoverageUrl


    def getGetCoverageUrl(self):
        return self.getCoverageUrl


    def setGetCoverageUrl(self, getCoverageUrl):
        self.getCoverageUrl = getCoverageUrl


    def getVersions(self):
        return self.versions


    def setVersions(self, versions):
        self.versions = versions


    def getCRS(self):
        return self.crsx


    def setCRS(self, crs):
        self.crs = crs


    def getFormats(self):
        return self.formats


    def setFormats(self, formats):
        self.formats = formats


    def getCoverageIds(self):
        return self.covIds


    def setCoverageIds(self, covIds):
        self.covIds = covIds

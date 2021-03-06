__author__ = 'aleaf'

import datetime as dt
import urllib2
import pandas as pd
from shapely.geometry import Point
import GISio


class NWIS:

    urlbase = 'http://waterdata.usgs.gov/nwis/'
    dtypes_dict = {'dv': 'dv?referred_module=sw&site_tp_cd=ST&',
                   'field_measurements': 'measurements?'}

    coordinate_format = 'decimal_degrees' #coordinate_format=decimal_degrees&
    group_key = 'NONE' #group_key=NONE&
    output_format = 'sitefile_output' #format=sitefile_output&
    sitefile_output_format = 'rdb' #sitefile_output_format=rdb&

    now = dt.datetime.now()
    range_selection = 'days' #range_selection=days
    period = 365 #period=365
    begin_date = '1880-01-01' #begin_date=2014-04-14
    end_date = '{:02d}-{:02d}-{:02d}'.format(now.year, now.month, now.day-1) #end_date=2015-04-13


    logscale = 1 #'set_logscale_y=1'
    channel_html_info = 0 #'channel_html_info=0'
    date_format = 'YYYY-MM-DD' #'date_format=YYYY-MM-DD'
    channel_rdb_info = 0 #'channel_rdb_info=0'
    rdb_compression = 'file' #'rdb_compression=file'
    list_of_search_criteria = 'lat_long_bounding_box' #'list_of_search_criteria=lat_long_bounding_box'

    def __init__(self, ll_bbox):
        """Class for retrieving data from NWIS.
        Currently only retrieves data within a specified lat/lon bounding box.

        Parameters
        ----------
        ll_bbox: list of floats
            List containing bounding latitudes and longitudes in decimal degrees, in the following order:
            [northwest longitude, northwest latitude, southeast longitude, southeast latitude]

        see the code for a list of default parameters
        """

        self.ll_bbox = ll_bbox

        self.bbox_url = 'nw_longitude_va={:.3f}&'.format(ll_bbox[0]) +\
                        'nw_latitude_va={:.3f}&'.format(ll_bbox[1]) +\
                        'se_longitude_va={:.3f}&'.format(ll_bbox[2]) +\
                        'se_latitude_va={:.3f}&'.format(ll_bbox[3])

        self.stuff_at_beginning = 'coordinate_format={}&'.format(self.coordinate_format) +\
                                  'group_key={}&'.format(self.group_key) +\
                                  'format={}&'.format(self.output_format) +\
                                  'sitefile_output_format={}&'.format(self.sitefile_output_format)

        self.dv_info = 'range_selection={}&'.format(self.range_selection) +\
                        'period={}&'.format(self.period) +\
                        'begin_date={}&'.format(self.begin_date) +\
                        'end_date={}&'.format(self.end_date)

        self.stuff_at_end = 'date_format={}&'.format(self.date_format) +\
                            'rdb_compression={}&'.format(self.rdb_compression) +\
                            'list_of_search_criteria={}'.format(self.list_of_search_criteria)

    def make_url(self, data_type, attributes):
        """
        Parameters
        ----------
        data_type: str
            'dv' for Daily Values
            'field_measurements' for Field Measurements

        Returns
        -------
        url string
        """
        url = self.urlbase + self.dtypes_dict[data_type]
        url += self.bbox_url
        url += self.stuff_at_beginning
        for a in attributes:
            url += 'column_name=' + a + '&'

        if data_type == 'dv':
            url += self.dv_info

        url += self.stuff_at_end
        return url

    def get_header_length(self, sitefile_text):
        knt = 0
        for line in sitefile_text:
            try:
                int(line.strip().split()[0])
                return knt
            except:
                knt += 1
        return knt

    def get_siteinfo(self, data_type, attributes):
        """Retrieves site information for the bounding box supplied to the NWIS class instance

        Parameters
        ----------
        data_type: str
            'dv' for Daily Values
            'field_measurements' for Field Measurements

        attributes: list of strings
            List of NWIS attributes to include (e.g. 'site_no', 'station_nm', etc.)
            Default sets of attributes for streamflow and groundwater levels data can
            be imported from the attributes.py file (work in progress)

        Returns
        -------
        the contents of an NWIS site information file in a dataframe format
        """

        url = self.make_url(data_type, attributes)
        sitefile_text = urllib2.urlopen(url).readlines()
        skiprows = self.get_header_length(sitefile_text)
        df = pd.read_csv(url, sep='\t', skiprows=skiprows, header=None, names=attributes)
        return df

    def write_shp(self, df, shpname='NWIS_export.shp'):
        """Write a shapefile of points from NWIS site file

        Parameters
        ----------
        df: dataframe
            dataframe of site info, must have dec_long_va and dec_lat_va columns with lon/lat in DD

        shpname: string
            Name for output shapefile

        Notes
        -----
        NAD83 is assumed for dec_long_va and dec_lat_va.
        If some entries are in NAD27, a difference of ~5 to >15m will result for WI
        (see http://en.wikipedia.org/wiki/North_American_Datum#/media/File:Datum_Shift_Between_NAD27_and_NAD83.png)
        """
        shpdf = df.copy()
        shpdf['geometry'] = [Point(r.dec_long_va, r.dec_lat_va) for i, r in shpdf.iterrows()]
        GISio.df2shp(shpdf, shpname, epsg=4269)
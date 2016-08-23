# jmag_bokeh_if.py -> a nicer bokeh interface
# here's how it works: a figure factory
# and a CSV parser object are injected into
# the grapher object; the grapher object
# then produces ready-to-go Bokeh graphs
# to place on your page. Client programs
# only need to specify the CSV corresponding
# to each graph, and optionally pass
# non-default graph parameters to the figure
# factory. This reduces the client program to
# a GUI and figuring out what to plot.
import pandas
from datetime import datetime
from io import StringIO
from bokeh.plotting import figure
from glob import glob
from numpy.fft import fft, fftfreq, fftshift
from math import sqrt
from functools import reduce
from collections import deque
import multiprocessing as mp

def dt_parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
def mp_concat(x, y):
    return '\n'.join([x, y])
def mp_magn(x):
    return sqrt(x.real**2 + x.imag**2)

p = mp.Pool(processes=8)

#from bokeh.palettes import Spectral9

colors = ["#008080", "#8B0000", "#006400", "#2F4F4F",
          "#800000", "#FF00FF", "#4B0082", "#191970",
          "#808000", "#696969", "#0000FF", "#FF4500"]

# for convenience -> specify your data directory here
# !! this should be an absolute path so we don't get
# IOErrors in CSV_Reader.get_header()
data_dir = '/data/'

# On the fence about whether this
# should be a class or just
# a single method with sane defaults.
class Figure_Factory:
    def __init__(self, **kwargs):
        """
        Constructor. Pass parameters for the graph here.
        """
        # This is a decent way of setting graph defaults if
        # there are none specified. These values are all fairly sane.
        # default values are overridden if specified at instantiation.
        kwargs['plot_height'] = kwargs.get('plot_height', 600)
        kwargs['plot_width']  = kwargs.get('plot_width', 600)
        kwargs['tools']       = kwargs.get('tools', 'pan,wheel_zoom,box_zoom,reset')
        kwargs['x_axis_type'] = kwargs.get('x_axis_type', 'datetime')
        kwargs['webgl'] = kwargs.get('webgl', False)
        self.kwargs = kwargs

    def gen_figure(self):
        """
        Get a new figure.
        """
        return figure(**self.kwargs)

# Data_Cooker objects can be injected
# into Grapher or CSV_Reader objects
# to process DataFrames between
# processing and graphing. They are
# expected to take an old Pandas
# DataFrame object and create a new one
# from it. The only important method
# (for now) is apply(). This parent class
# is a nop.
class Data_Cooker:
    def __init__(self, df=None):
        """
        Constructor.
        df is a dataframe object, and can be
        supplied either at construction time
        or when method apply() is invoked.
        """
        self.df = df
    def apply(self, df=None):
        """
        apply() cooks the data.
        In the base class, it's a nop.
        In derived classes, this performs
        a mapping from a Pandas DataFrame
        to a Pandas DataFrame object; the
        result is used by CSV_Reader if
        cooking is enabled.
        """
        if df is not None:
            self.df = df
        return self.df
    def get_last_df(self):
        return self.df

# Apply the fast Fourier transform
# to incoming data. Extends Data_Cooker
# and overrides its apply() method.
# An FFT_Cooker object may be injected
# into a Grapher object, specifying
# 'Freq' as the independent variable,
# to display spectra of incoming data.
class FFT_Cooker(Data_Cooker):
    def apply(self, df=None, indep_var='Time'):
        if df is not None:
            self.df = df
        new_df = {}
        a, b = self.df[indep_var][0], self.df[indep_var][len(self.df[indep_var])-1]
        for key in self.df:
            if key == indep_var:
                continue
            new_df[key] = fft(self.df[key])
            new_df[key] = p.map(mp_magn, new_df[key])

        # avg time between samples
        # assumes uniform sampling
        dt = (b-a).total_seconds()
        dt /= len(self.df[indep_var])

        # get list of frequencies from the fft
        # new_df['Freq'] = fftfreq(len(self.df[key]), dt)
        new_df['Freq'] = fftshift(fftfreq(len(self.df[key]), dt))

        #
        new_df = pandas.DataFrame.from_dict(new_df).sort_values('Freq')
        #new_df = new_df[abs(new_df.Freq) > 0.4]

        self.df = new_df
        return new_df

# magnitudes for fib/fob
# expect 'mag' as dep variable,
# and 'Time' as indep. Expects keys
# Bx, By, and Bz to be existent in raw
# DataFrame.
class Magnitude_Cooker(Data_Cooker):
    def apply(self, df=None, indep_var='Time'):
        """
        Take the magnitude of the magnetic field
        vector; (x,y,z)-components given by
        B(x,y,z) keys into the dataframe.
        """
        if df is not None:
            self.df = df
        new_df = {}
        new_df[indep_var] = self.df[indep_var]
        new_df['mag'] = []
        i = 0
        while i < len(self.df['Bx']):
            # |v| = sqrt(vx^2 + vy^2 + vz^2)
            new_df['mag'].append(
                     sqrt( self.df['Bx'][i]**2
                         + self.df['By'][i]**2
                         + self.df['Bz'][i]**2))
            i += 1
        new_df = pandas.DataFrame.from_dict(new_df).sort_values(indep_var)
        self.df = new_df
        return new_df

class Natural_Unit_Cooker(Data_Cooker):
    def __init__(self, factors, df=None):
        """
        Constructor.
        factors is a list of conversion factors to multiply
        the raw data by. This assumes that there is a linear
        relationship between raw data and data in natural units.
        """
        self.df = df
        self.factors = factors
    def apply(self, df=None, indep_var='Time'):
        """
        Multiply through by conversion factors
        """
        new_df = {}
        if df is not None:
            self.df = df
        for key in self.df:
            if key not in self.factors:
                new_df[key] = self.df[key]
                continue
            new_df[key] = map(lambda x: x*self.factors[key], self.df[key])
        new_df = pandas.DataFrame.from_dict(new_df).sort_values(indep_var)
        self.df = new_df
        return new_df

class CSV_Reader:
    def __init__(self, fname, num_dp=1000, data_cooker=None, indep_var='Time'):
        """
        Constructor method.
            fname       : file name to read
            num_dp      : number of data points to display
            data_cooker : An object of class Data_Cooker,
                          which optionally post-processes
                          DataFrames after parsing.
        """
	self.fname = fname
        self.num_dp = num_dp
        self.data_cooker = data_cooker
        self.cook_data = False
        if data_cooker is not None:
            self.cook_data = True
        self.indep_var = indep_var

        self.header = None
        self.dp_count = 0

    def set_fname(self, fname):
        """
        Setter method for fnam
        """
        self.fname = fname
        # purge stale cached info
        self.header = None
        self.dp_count = 0

    def set_num_dp(self, num_dp):
        """
        Setter method for num_dp
        """
        self.num_dp = num_dp

    def blocks(self, f, sz=16384):
        while True:
            b = f.read(sz)
            if not b:
                break
            yield b

    def count_lines_blockwise(self, f):
        return sum(bl.count('\n') for bl in self.blocks(f))

    def get_header(self):
        """
        Get the active header from the CSV.
        If the header would be included in
        a tail of the file, returns '' instead;
        returning another value would cause an error.
        This is the newer, faster version.
                    n   tottime percall cumtime percall
        BLOCKWISE:  210 0.000   0.000   0.001   0.000
            NAIVE:  144 0.000   0.000   0.003   0.000
        Note the 3x speedup after moving to a blockwise
        read cumtime, despite blockwise having n=210.
        Estimated 4.4x speedup of this function.
        """
        if self.header is not None and self.dp_count > self.num_dp:
            return self.header

        # either no header or insufficient data points to return one;
        # this triggers recalculation of dp_count, and gets the header
        # if we don't have it cached already.
        with open(self.fname, 'r') as f:
            if self.header is None:
                self.header = f.readline()
                f.seek(0)
            self.dp_count = self.count_lines_blockwise(f)

        if self.dp_count > self.num_dp:
            return self.header
        return ''

    def tail(self):
        """
        Tail the file; takes num_dp lines from the bottom.
        Parsing with deque over tailer gives a significant
        speedup; serving stale FIB data, I got the following:
                       n      tottime  percall  cumtime  percall
        TAILER TAILER: 206    0.007    0.000    2.456    0.012
        DEQUE TAILER:  755    0.183    0.000    1.114    0.001
        tottime measures total time in the function /not including/
        subcalls; cumtime gives the actuall call-to-return latency.
        Disregard the tottime increase; of *course* we get a higher
        number, because we do less in our subcalls with deque tail().
        Please note that these are cumulative over all calls, where
        n=206 for libtailer tail(), and n=755 for deque tail().
        Notice the order-of-magnitude improvement in cumtime percall,
        which gives the best measure of actual performance. Even
        with 3.7x as many calls, deque tail() runs 2.2x as fast.
        I estimate an 8.1x speedup of this function with this change.
        """
        with open(self.fname, 'r') as f:
            q = deque(f, self.num_dp)
        # this is not worth parallelizing
        return reduce(mp_concat, q)

    def get_dataframe(self):
        """
        Returns the tail of the file as a parsed Pandas dataframe object
        """
        csv = self.get_header() + self.tail()
        df = pandas.read_csv(StringIO(unicode(csv)))
        try:
            df['Time'] = p.map(dt_parse, df['Time'])
        except KeyError:
            pass

        # optionally cook data
        if self.data_cooker is not None and self.cook_data:
            df = self.data_cooker.apply(df)

        return df.sort_values(self.indep_var)

    def on_change(self, attr, old, new):
        self.cook_data = not self.cook_data

class Grapher:
    def __init__(self, csv_reader=None, pattern=None, figure_factory=None, key_groups=None, indep_var='Time', cooker=None):
        """
        Constructor.
            csv_reader      : an object of class CSV_Reader,
                              or a string giving the path to a CSV
            pattern         : Grapher can check for a new file according
                              to a glob pattern specified here every
                              time update_graphs() is called. This specifies
                              that glob pattern.
            figure_factory  : an object of class Figure_Factory;
                              if this is None, then defaults are assumed
            key_groups      : a list of lists of strings;
                              each string should be from the
                              CSV header / a working dataframe
                              key. Each list of these keys
                              will be graphed together;
                              a list of graphs corresponding
                              to the list of lists is returned
                              by method make_new_graphs()
            indep_var       : variable to use on the x-axis.
            cooker          : ask the CSV_Reader to do post-processing
                              on Pandas DataFrames according to the
                              .apply() method in the instance
        """
        self.active_lines = {}
        if figure_factory is None:
            self.figure_factory = Figure_Factory()
        else:
            self.figure_factory = figure_factory
        if type(csv_reader) is str:
            self.csv_reader = CSV_Reader(csv_reader, data_cooker=cooker, indep_var=indep_var)
            self.pattern = None
        elif csv_reader is not None: # just assume it's a valid CSV object
            self.csv_reader = csv_reader
            self.pattern = None
        elif pattern is not None:
            self.pattern = pattern
            self.csv_reader = CSV_Reader(get_latest_file(pattern), data_cooker=cooker, indep_var=indep_var)
        else:
            raise ValueError("Need a CSV_Reader object, a path to a CSV, or *at least* a glob pattern to search for")
        if key_groups is None:
            # default to a single key group, i.e. only one graph
            self.key_groups = [csv_reader.get_header().split(',')]
        else:
            self.key_groups = key_groups
        self.indep_var = indep_var
        self.cooker = cooker

    def get_csv_reader(self):
        return self.csv_reader

    def make_new_graphs(self):
        """
        Creates an entirely new graph.
        !! This function is appropriate for
        setting members of the layout object
        directly; this WILL trigger a page refresh,
        which is slow. AVOID THIS METHOD.
        But you should call it at least once to
        actually make the graph. Do as I do, not as I say.
        """
        # the old lines don't matter and get tossed out
        # hope the GC is feeling performant today
        self.active_lines = {}
        figures = []
        #p = self.figure_factory.gen_figure()
        df = self.csv_reader.get_dataframe()
        for key_group in self.key_groups:
            i = 0
            figures.append(self.figure_factory.gen_figure())
            for x in key_group:
                if x == self.indep_var:
                    continue
                # storing the line renderer objects will allow us to update the
                # lines without triggering a page redraw
                self.active_lines[x] = figures[-1].line(df[self.indep_var], df[x], legend=x,
                                                        color=colors[i], line_width=1.5
                )
                i += 1
        return figures

    def update_graphs(self):
        """
        Tail the watched file and redraw graphs
        without triggering a page redraw.
        """
        if self.pattern is not None:
            self.csv_reader.set_fname(get_latest_file(self.pattern))

        df = self.csv_reader.get_dataframe()
        for key in self.active_lines:
            if key == self.indep_var:
                continue
            self.active_lines[key].data_source.data['x'] = df[self.indep_var]
            self.active_lines[key].data_source.data['y'] = df[key]

# find most-recently-produced
# CSV in the directory
def get_latest_csv(pattern):
   return max(glob(pattern))

def get_latest_file(pattern):
    return max(glob(data_dir + pattern))

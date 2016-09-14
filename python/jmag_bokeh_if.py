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
from bokeh.models.tools import WheelZoomTool
from glob import glob
from numpy.fft import rfft, rfftfreq
from math import sqrt
#from functools import reduce
from collections import deque
#import multiprocessing as mp

def dt_parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
def mp_concat(x, y):
    return '\n'.join([x, y])
def mp_magn(x):
    return sqrt(x.real**2 + x.imag**2)

#p = mp.Pool(processes=1)

colors = ["#008080", "#8B0000", "#006400", "#2F4F4F",
          "#800000", "#FF00FF", "#4B0082", "#191970",
          "#808000", "#696969", "#0000FF", "#FF4500"]

# for convenience -> specify your data directory here
# !! this should be an absolute path so we don't get
# IOErrors in CSV_Reader.get_header()
data_dir = '/data/'

def default_figure(kwargs):
    """
    default figure callback
    """
    print("default_figure(): kwargs={}".format(kwargs))
    if type(kwargs) != dict:
        print("default_figure(): kwargs is not dict!")
    kwargs['plot_height'] = kwargs.get('plot_height', 600)
    kwargs['plot_width']  = kwargs.get('plot_width', 600)
    kwargs['tools']       = kwargs.get('tools', 'box_zoom,pan,save,reset')
    kwargs['x_axis_type'] = kwargs.get('x_axis_type', 'datetime')
    #kwargs['webgl']       = kwargs.get('webgl', False)
    p = figure(**kwargs)
    p.add_tools(WheelZoomTool(dimensions=['height']))
    return p

# Data_Cooker objects can be injected
# into Grapher or CSV_Reader objects
# to process DataFrames between
# processing and graphing. They are
# expected to take an old Pandas
# DataFrame object and create a new one
# from it. The only important method
# (for now) is apply(). This parent class
# is a nop. -----------------------------
# This is a class because we want the
# ability to store state, even though
# these don't do anything particularly
# unusual.

# data cookers are deprecated; use the
# dfmap interface instead
# pre_dfmap -> applies to all key groups
# post_dfmap -> associative array; only cooks associated key group
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
        n = len(self.df[indep_var])
        a, b = self.df[indep_var][0], self.df[indep_var][n-1]
        for key in self.df:
            if key == indep_var:
                continue
            new_df[key] = rfft(self.df[key])
            new_df[key] = list(map(mp_magn, new_df[key]))
            new_df[key] = list(map(lambda x: 2*x/n, new_df[key]))

        # avg time between samples
        # assumes uniform sampling
        dt = (b-a).total_seconds()
        dt /= n

        # get list of frequencies from the fft
        # new_df['Freq'] = fftfreq(len(self.df[key]), dt)
        new_df['Freq'] = rfftfreq(n, dt)

        #
        new_df = pandas.DataFrame.from_dict(new_df)#.sort_values('Freq')
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
        new_df = pandas.DataFrame.from_dict(new_df)#.sort_values(indep_var)
        self.df = new_df
        return new_df

class Natural_Unit_Cooker(Data_Cooker):
    def __init__(self, factors, df=None):
        """
        Constructor.
        factors is a dict of conversion factors to multiply
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
            new_df[key] = list(map(lambda x: self.factors[key][0]+x*self.factors[key][1], self.df[key]))
        new_df = pandas.DataFrame.from_dict(new_df)#.sort_values(indep_var)
        self.df = new_df
        return new_df

class CSV_Reader:
    def __init__(self, fname, num_dp=1024, data_cooker=None, indep_var='Time'):
        """
        Constructor method.
            fname       : file name to read
            num_dp      : number of data points to display
            data_cooker : cooks data (e.g. fft)
            indep_var   : the file's independent variable
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
        Setter method for fname
        """
        self.fname = fname
        # purge stale cached info
        self.header = None
        self.dp_count = 0

    def set_num_dp(self, num_dp):
        """
        Setter method for num_dp.
        """
        self.num_dp = num_dp

    def blocks(self, f, sz=16384):
        # generator reads 16kb blocks
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
        """
        with open(self.fname, 'r') as f:
            q = deque(f, self.num_dp)
        return "".join(q)

    def get_dataframe(self):
        """
        Returns the tail of the file as a parsed Pandas dataframe object
        """
        csv = self.get_header() + self.tail()
        if len(csv) > 0:
            df = pandas.read_csv(StringIO(str(csv)))
        else:
            df = pandas.DataFrame()
        try:
            # ISO 8601 datetime string -> Python datetime object
            df['Time'] = list(map(dt_parse, df['Time']))
        except KeyError:
            pass
        except TypeError:
            print(df['Time'])

        # optionally cook data
        if self.data_cooker is not None and self.cook_data:
            df = self.data_cooker.apply(df)

        return df#.sort_values(self.indep_var)

    def datafmt(self, fmt):
        if(fmt=="raw"):
            self.cook_data = False
        else:
            self.cook_data = True

class Grapher:
    def __init__(self, csv_reader=None, pattern=None, figure_opts=None,
                 key_groups=None, indep_var='Time', cooker=None,
                 dfmap = None, cook_data = False):
        """
        Constructor.
            csv_reader      : an object of class CSV_Reader,
                              or a string giving the path to a CSV
            pattern         : Grapher can check for a new file according
                              to a glob pattern specified here every
                              time update_graphs() is called. This specifies
                              that glob pattern.
            figure_cb       : callback to generate a figure;
                              there is a sane default here.
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
            dfmap           : dfmap can be a function, a list of functions,
                              or a list of lists of functions. If it's a
                              function, when data is to be cooked, this
                              function will do the cooking. If it's a
                              list of functions, the dataframe used by
                              each key group will be generated by the
                              associated function in dfmap (implying
                              len(dfmap) == len(key_groups)).
                              If it's a list of lists of functions,
                              the first list is applied to the dataframe
                              in order; then, the second list is used
                              to generate each key group's dataframe.
                              The dfmap interface obsoletes the
                              Data_Cooker interface.
            cook_data       : Boolean to enable/disable data cooking.
        """
        self.active_lines = {}
        self.figure_opts  = figure_opts
        print("Have figure opts: {}".format(figure_opts))
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
        self.dfmap = dfmap
        self.indep_var = indep_var
        self.cooker = cooker

    def get_figure_opts(self, idx):
        """
        Get figure options. Either
        pass an array of figure opts
        or use one set of options.
        """
        print("get_figure_opts(): idx={}, self.figure_opts={}".format(idx, self.figure_opts))
        if self.figure_opts is None:
            return dict()
        if type(self.figure_opts) == list:
            if self.figure_opts[idx] is not None:
                return self.figure_opts[idx]
            return dict()
        return self.figure_opts


    def get_csv_reader(self):
        return self.csv_reader

    def make_new_graphs(self):
        """
        Creates a new set of graphs.
        """
        # the old lines don't matter and get tossed out
        # hope the GC is feeling performant today
        print("make_new_graphs()")
        self.active_lines = {}
        figures = []
        j = 0
        raw_df = self.csv_reader.get_dataframe()
        dfs = self.cook(raw_df)
        print("Have dataframe for key groups {}".format(self.key_groups))
        for key_group, df in zip(self.key_groups, dfs):
            i = 0
            figures.append(default_figure(self.get_figure_opts(j)))
            for x in key_group:
                if x == self.indep_var:
                    continue
                # storing the line renderer objects will allow us to update the
                # lines without triggering a page redraw
                self.active_lines[x] = figures[-1].line(df[self.indep_var], df[x], legend=x,
                                                        color=colors[i], line_width=1.5)

                i += 1
            j += 1
        return figures

    def update_graphs(self, datafmt=None, highlight=None, samples=None):
        """
        Tail the watched file and redraw graphs
        without triggering a page redraw.
        """
        if self.pattern is not None:
            self.csv_reader.set_fname(get_latest_file(self.pattern))

        if datafmt:
            self.csv_reader.datafmt(datafmt)

        if samples:
            try:
                self.csv_reader.set_num_dp(int(samples))
            except:
                pass

        raw_df = self.csv_reader.get_dataframe()
        dfs = self.cook(raw_df)

        if highlight:
            if highlight == "All":
                for l, c in zip(self.active_lines.values(), colors):
                    l.glyph.line_color = c
            else:
                for key, l in self.active_lines.items():
                    if highlight in key:
                        l.glyph.line_color = colors[1]
                    else:
                        l.glyph.line_color = colors[0]

        for key, df in zip(self.active_lines, dfs):
            if key == self.indep_var:
                continue
            self.active_lines[key].data_source.data['x'] = df[self.indep_var]
            self.active_lines[key].data_source.data['y'] = df[key]

    def cook(self, df):
        # --- don't cook data if we're not asked to
        if not self.cook_data:
            return [df for i in self.key_groups]

        # --- dfmap is one function; apply it
        if callable(self.dfmap):
            df = self.dfmap(df)
            return [df for i in self.key_groups]

        # --- dfmap is a list of functions; each function
        #     is associated with one key group
        if type(self.dfmap) == list:
            ret = []
            for fn in filter(callable, self.dfmap):
                if callable(fn):
                    ret.append(fn(df))
                else:
                    ret.append(df)
            return ret
        # --- dfmap is a list of lists of functions; len(dfmap) = 2.
        #     The first list contains functions to apply in sequence.
        #     The second list contains functions that are applied on a
        #     per-keygroup basis.
        if type(self.dfmap) == list and type(self.dfmap[0]) == list:
            if len(self.dfmap != 2):
                raise TypeError("if dfmap is a list of lists, it must have len 2")
            for fn in filter(callable, self.dfmap[0]):
                df = fn(df)
            ret = []
            for fn in filter(callable, self.dfmap[1]):
                ret.append(df)
            return ret
        raise TypeError("dfmap is incorrectly structured")


# find most-recently-produced
# CSV in the directory
def get_latest_csv(pattern):
   return max(glob(pattern))

def get_latest_file(pattern):
    return max(glob(data_dir + pattern))

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
from io import StringIO
from bokeh.plotting import figure
from bokeh.models.tools import WheelZoomTool
from bokeh.models import Legend, ColumnDataSource
from glob import glob
import numpy as np
from numpy.fft import rfft, rfftfreq
from math import sqrt
#from functools import reduce
from collections import deque
#import multiprocessing as mp
#from profilehooks import profile
import ciso8601
#import itertools

def mp_concat(x, y):
    return '\n'.join([x, y])
def mp_magn(x):
    return sqrt(x.real**2 + x.imag**2)

#p = mp.Pool(processes=1)

_colors = ["#008080", "#8B0000", "#006400", "#2F4F4F",
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
    kwargs['plot_height'] = kwargs.get('plot_height', 500)
    kwargs['plot_width']  = kwargs.get('plot_width', 600)
    kwargs['tools']       = kwargs.get('tools', 'box_zoom,pan,save,reset')
    #kwargs['x_axis_type'] = kwargs.get('x_axis_type', 'datetime')
    #kwargs['webgl']       = kwargs.get('webgl', False)
    p = figure(**kwargs)
    p.add_tools(WheelZoomTool(dimensions=['height']))
    return p


# dfmap -> fft incoming data
#@profile
def dfmap_fft(df, indep_var='Time'):
    if df is not None:
        df = df
    new_df = {}
    n = len(df[indep_var])
    a, b = df[indep_var][0], df[indep_var][n-1]
    for key in df:
        if key == indep_var:
            continue
        new_df[key] = rfft(df[key])
        new_df[key] = list(map(np.absolute, new_df[key]))
        new_df[key] = list(map(lambda x: 2*x/n, new_df[key]))

    # avg time between samples
    # assumes uniform sampling
    dt = (b-a) / n
    #dt = (b-a).total_seconds() / n

    # get list of frequencies from the fft
    # new_df['Freq'] = fftfreq(len(self.df[key]), dt)
    new_df['Freq'] = rfftfreq(n, dt)

    #
    new_df = pandas.DataFrame.from_dict(new_df)#.sort_values('Freq')
    #new_df = new_df[abs(new_df.Freq) > 0.4]

    return new_df

# magnitudes for fib/fob
# expect 'mag' as dep variable,
# and 'Time' as indep. Expects keys
# Bx, By, and Bz to be existent in raw
# DataFrame.
def dfmap_magnitude(df, indep_var='Time'):
        """
        Take the magnitude of the magnetic field
        vector; (x,y,z)-components given by
        B(x,y,z) keys into the dataframe.
        """
        new_df = {}
        new_df[indep_var] = df[indep_var]
        new_df['mag'] = []
        i = 0
        while i < len(df['Bx']):
            # |v| = sqrt(vx^2 + vy^2 + vz^2)
            new_df['mag'].append(
                     sqrt( df['Bx'][i]**2
                         + df['By'][i]**2
                         + df['Bz'][i]**2))
            i += 1
        new_df = pandas.DataFrame.from_dict(new_df)#.sort_values(indep_var)
        return new_df

#@profile
def dfmap_zeromean(df, indep_var='Time'):
    """
    Remove mean value of df.
    """
    new_df = df.drop(indep_var, 1)
    new_df = new_df - new_df.mean()
    new_df[indep_var] = df[indep_var]
    return new_df

class dfmap_genmap:

    def __init__(self, mappings):
        self.mappings = mappings

    #@profile
    def apply(self, df, indep_var='Time'):
        new_df = {}
        for key in df:
            if key not in self.mappings:
                new_df[key] = df[key]
                continue
            new_df[key] = list(map(self.mappings[key], df[key]))
        return pandas.DataFrame.from_dict(new_df)


class CSV_Reader:
    def __init__(self, fname=None, pattern=None, num_dp=1024, indep_var='Time', relative_time=True):
        """
        Constructor method.
            fname       : file name to read
            num_dp      : number of data points to display
            indep_var   : the file's independent variable
        """
        self.fname = fname
        self.pattern = pattern
        if pattern is not None:
            self.fname = get_latest_file(pattern)
        self.num_dp = num_dp
        self.indep_var = indep_var

        self.header = None
        self.dp_count = 0
        self._rt = relative_time
        #self.which_tailer = itertools.cycle([0, 1])

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

    # def _blocks(self, f, sz=16384):
    #     # generator reads 16kb blocks
    #     while True:
    #         b = f.read(sz)
    #         if not b:
    #             break
    #         yield b
    #
    # def _count_lines_blockwise(self, f):
    #     return sum(bl.count('\n') for bl in self._blocks(f))

    #@profile
    def get_header(self):
        """
        Get the active header from the CSV.
        If the header would be included in
        a tail of the file, returns '' instead;
        returning another value would cause an error.
        """
        if self.header is not None:
            return self.header

        # either no header or insufficient data points to return one;
        # this triggers recalculation of dp_count, and gets the header
        # if we don't have it cached already.
        with open(self.fname, 'r') as f:
            if self.header is None:
                self.header = f.readline()
                f.seek(0)

        return self.header

    #@profile
    #def _tail(self):
    #    """
    #    Tail the file; takes num_dp lines from the bottom.
    #    """
    #    with open(self.fname, 'r') as f:
    #        q = deque(f, self.num_dp)
    #    return "".join(q)

    #@profile
    #def _tail2(self):
    def tail(self, sz=65536):
        with open(self.fname, 'r') as f:
            f.seek(0, 2)
            fsize = f.tell()
            f.seek(max(fsize-sz, 0), 0)
            q = deque(f, self.num_dp+1)
            while (len(q) < self.num_dp+1) and (fsize > sz):
                sz *= 2
                f.seek(max(fsize-sz, 0), 0)
                q = deque(f, self.num_dp+1)
        if len(q) > 0:
            q.popleft()
        return "".join(q)

    #def tail(self):
    #    n = self.which_tailer.__next__()
    #    print("_tail{}()".format(n+1))
    #    return [
    #        self._tail(),
    #        self._tail2()
    #    ][n]

    def _relative_time(self, df):
        if self.indep_var == 'Time':
            df[self.indep_var] = (df[self.indep_var] - max(df[self.indep_var]))/np.timedelta64(1, 's')
        return df

    #@profile
    def get_dataframe(self):
        """
        Returns the tail of the file as a parsed Pandas dataframe object
        """
        head = self.get_header()
        tail = self.tail()

        if len(head) > 0 and tail.count('\n') > 1:
            df = pandas.read_csv(StringIO(str(head+tail)))
        else:
            df = pandas.DataFrame()

        try:
            # ISO 8601 datetime string -> Python datetime object
            df['Time'] = list(map(ciso8601.parse_datetime, df['Time']))
        except KeyError:
            pass
        except TypeError:
            print(df['Time'])
        if self._rt:
            return self._relative_time(df)
        else:
            return df

class Grapher:

    def __init__(self, figure_opts=None, key_group=None, indep_var='Time',
                 df=None, colors=None):
        """
        Constructor.
            key_group       : a list of lists of strings;
                              each string should be from the
                              CSV header / a working dataframe
                              key. Each list of these keys
                              will be graphed together;
                              a list of graphs corresponding
                              to the list of lists is returned
                              by method make_new_graphs()
            indep_var       : variable to use on the x-axis. Can
                              be a single value or per-keygroup.
        """
        self.active_lines = {}
        self.figure_opts  = figure_opts
        self.key_group = key_group
        self.indep_var = indep_var
        self.source = ColumnDataSource(data=df)
        self.colors = None
        if colors is None:
            self.colors = _colors
        else:
            self.colors = colors
    def get_figure_opts(self):
        """
        Get figure options. Either
        pass an array of figure opts
        or use one set of options.
        """
        if self.figure_opts is None:
            return dict()
        return self.figure_opts

    #@profile
    def make_new_graph(self):
        """
        Creates a new set of graphs.
        """
        self.active_lines = {}
        legend_strings = []
        figure = default_figure(self.get_figure_opts())

        for y, i in zip(self.key_group, range(len(self.key_group))):
            print("make_new_graph(): plotting {}".format(y))

            if y == self.indep_var:
                print("make_new_graph(): y={} is the indep var".format(y))
                continue

            print("make_new_graph(): y={} is a dep var".format(y))

            # storing the line renderer objects will allow us to update the
            # lines without triggering a page redraw
            line = figure.line(self.indep_var, y, source=self.source,
                    color=self.colors[i], line_width=1.5)
            self.active_lines[y] = line
            legend_strings.append((y, [line]))

        l = Legend(legends=legend_strings, location=(0, 0))
        figure.add_layout(l, 'right')
        return figure

    #@profile
    def update_graph(self, df, highlight=None):
        """
        Tail the watched file and redraw graphs
        without triggering a page redraw.
        """

        print("update_graph(): highlight={}".format(highlight))
        self.source.data = ColumnDataSource.from_df(df)

        if highlight is not None:
                for key, l in self.active_lines.items():
                    if key in highlight:
                        l.glyph.line_alpha = 1
                    else:
                        l.glyph.line_alpha = 0.2

# find most-recently-produced
# CSV in the directory
def get_latest_csv(pattern):
   return max(glob(pattern))

def get_latest_file(pattern):
    return max(glob(data_dir + pattern))

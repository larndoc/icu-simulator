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
import tailer
from StringIO import StringIO
from bokeh.plotting import figure
from glob import glob
from numpy.fft import fft, fftfreq
from math import sqrt

# graph color sequence; we have _way_ more than we need
colors = ["#FFFF00","#1CE6FF","#FF34FF","#FF4A46","#008941",
          "#006FA6","#A30059","#FFDBE5","#7A4900","#0000A6",
          "#63FFAC","#B79762","#004D43","#8FB0FF","#997D87",
          "#5A0007","#809693","#FEFFE6","#1B4400","#4FC601",
          "#3B5DFF","#4A3B53","#FF2F80","#61615A","#BA0900",
          "#6B7900","#00C2A0","#FFAA92","#FF90C9","#B903AA",
          "#D16100","#DDEFFF","#000035","#7B4F4B","#A1C299",
          "#300018","#0AA6D8","#013349","#00846F","#372101",
          "#FFB500","#C2FFED","#A079BF","#CC0744","#C0B9B2",
          "#C2FF99","#001E09","#00489C","#6F0062","#0CBD66",
          "#EEC3FF","#456D75","#B77B68","#7A87A1","#788D66",
          "#885578","#FAD09F","#FF8A9A","#D157A0","#BEC459",
          "#456648","#0086ED","#886F4C","#34362D","#B4A8BD",
          "#00A6AA","#452C2C","#636375","#A3C8C9","#FF913F",
          "#938A81","#575329","#00FECF","#B05B6F","#8CD0FF",
          "#3B9700","#04F757","#C8A1A1","#1E6E00","#7900D7",
          "#A77500","#6367A9","#A05837","#6B002C","#772600",
          "#D790FF","#9B9700","#549E79","#FFF69F","#201625",
          "#72418F","#BC23FF","#99ADC0","#3A2465","#922329",
          "#5B4534","#FDE8DC","#404E55","#0089A3","#CB7E98",
          "#A4E804","#324E72","#6A3A4C","#83AB58","#001C1E"]

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
        kwargs['tools']       = kwargs.get('tools', 'xpan,ypan,xwheel_zoom,'
                                           +'xbox_zoom,ybox_zoom,reset')
        kwargs['x_axis_type'] = kwargs.get('x_axis_type', 'datetime')
        self.kwargs = kwargs

    def gen_figure(self):
        """
        Get a new figure.
        """
        p = figure(**self.kwargs)
        return p

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
        self.df = df
    def apply(self, df=None):
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
# WE EXPECT TIME TO BE AN INDEPENDENT
# VARIABLE HERE, though this is trivially
# generalized (TODO).
class FFT_Cooker(Data_Cooker):
    def apply(self, df=None):
        if df is not None:
            self.df = df
        new_df = {}
        a, b = self.df['Time'][0], self.df['Time'][len(self.df['Time'])-1]
        for key in self.df:
            if key == 'Time':
                continue
            new_df[key] = fft(self.df[key])
            new_df[key] = map(lambda x: sqrt(x.real**2 + x.imag**2), new_df[key])
        new_df['Freq'] = fftfreq(len(self.df[key]),
                                  (b-a).total_seconds()
                                  / len(self.df['Time']))
        new_df = pandas.DataFrame.from_dict(new_df).sort_values('Freq')
        new_df = new_df[abs(new_df.Freq) > 1]
        self.df = new_df
        return new_df

class CSV_Reader:
    def __init__(self, fname, num_dp=1000, data_cooker=None):
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

    def set_fname(self, fname):
        """
        Setter method for fnam
        """
        self.fname = fname

    def set_num_dp(self, num_dp):
        """
        Setter method for num_dp
        """
        self.num_dp = num_dp

    def get_header(self):
        """
        Get the active header from the CSV.
        If the header would be included in
        a tail of the file, returns '' instead;
        returning another value would cause an error.
        """
        f = open(self.fname, 'r')
        lines = f.readlines()
        ret = ''
        if len(lines) > self.num_dp:
            ret = lines[0]
        f.close()
        return ret

    def tail(self):
        """
        Tail the file; takes num_dp lines from the bottom
        """
        return reduce(lambda x, y: x + '\n' + y,
                      tailer.tail(open(self.fname), self.num_dp)
        )

    def get_dataframe(self):
        """
        Returns the tail of the file as a parsed Pandas dataframe object
        """
        df = pandas.read_csv(
                StringIO(
                    self.get_header()
                    + self.tail()
                )
        )
        try:
            df['Time'] = map(lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f"), df['Time'])
        except KeyError:
            pass

        # optionally cook data
        if self.data_cooker is not None:
            df = self.data_cooker.apply(df)

        return df

class Grapher:
    def __init__(self, csv_reader, figure_factory=None, key_groups=None, indep_var='Time', cooker=None):
        """
        Constructor.
            csv_reader      : an object of class CSV_Reader,
                              or a string giving the path to a CSV
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
            self.csv_reader = CSV_Reader(csv_reader, data_cooker=cooker)
        else:
            self.csv_reader = csv_reader
        if key_groups is None:
            # default to a single key group, i.e. only one graph
            self.key_groups = [csv_reader.get_header().split(',')]
        else:
            self.key_groups = key_groups
        self.indep_var = indep_var
        self.cooker = cooker

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
                                                        color=colors[i]
                )
                i += 1
        return figures

    def update_graphs(self):
        """
        Tail the watched file and redraw graphs
        without triggering a page redraw.
        """
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

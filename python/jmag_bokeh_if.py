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
        kwargs['x_axis_type'] = kwargs.get('x_axis_type', 'datetiem')
        self.kwargs = kwargs

    def gen_figure(self):
        """
        Get a new figure.
        """
        p = figure(self.kwargs)
        return p


class CSV_Reader:
    def __init__(self, fname, num_dp=1000):
        """
        Constructor method.
            fname   : file name to read
            num_dp  : number of data points to display
        """
        self.fname = fname
        self.num_dp = num_dp

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
        df['Time'] = map(lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S:%f"), df['Time'])
        return df


# TODO: this grapher object is convenient,
# but is incapable of creating many plots
# from one CSV. This needs to be fixed.
# Idea is to pass a list of lists of header
# tags (which are also keys to pandas DataFrame
# objects); each list of tags will become a
# separate graph. The list of graphs will
# be returned from a method of this class,
# to be stored in some layout object for display.
class Grapher:
    def __init__(self, figure_factory, csv_parser):
        """
        Constructor.
            figure_factory  : an object of class Figure_Factory
            csv_reader      : an object of class CSV_Reader
        """
        # !! in earlier TODO, active_lines can remain the same.
        # we can remain agnostic to /which/ plot each line is,
        # as long as we actually update the data source
        # corresponding to the correct line
        self.active_lines = {}
        self.figure_factory = figure_factory
        self.csv_parser = csv_parser

    def make_new_graph(self):
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
        p = self.figure_factory.gen_figure()
        df = self.csv_parser.get_dataframe()
        i = 0
        for x in df:
            # TODO: time data is not the only independent variable!
            # handle frequency plots as well
            if x == 'Time':
                continue
            # storing the line renderer objects will allow us to update the
            # lines without triggering a page redraw
            self.active_lines[x] = p.line(df['Time'], df[x], legend=x,
                    color=colors[i]
            )

    def update_graph(self):
        """
        Tail the watched file and redraw graphs
        without triggering a page redraw.
        """
        df = self.csv_parser.get_dataframe()
        for key in self.active_lines:
            self.active_lines[key].data_source.data['x'] = df['Time']
            self.active_lines[key].data_source.data['y'] = df[key]

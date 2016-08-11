import pandas as pd
from glob import glob

from bokeh.layouts import layout, widgetbox
from bokeh.models import Select, Div
from bokeh.plotting import curdoc, figure

from StringIO import StringIO

import tailer

# new thing: use tailer to get latest data from the csv;
# grab header and pack into pandas dataframe

N = 1000

# TODO: timestamp on-the-fly
from datetime import datetime

colors = ['red', 'blue', 'green', 'maroon', 'indigo', 'black',
        'goldenrod', 'mediumslateblue', 'olivedrab', 'saddlebrown',
        'yellowgreen', 'orangered', 'orange', 'limegreen',
        'blueviolet', 'darkblue']

desc = Div(text=open('desc.html', 'r').read(), width=1000)
csvs = glob('./data/*.csv')
#print csvs

csv_select = Select(title="File to view", value=csvs[0], options=csvs)

# selected CSV from widget determines which parsed CSV to use
# dialog maps directly to index into parsed_csvs
controls = [csv_select]

for control in controls:
    control.on_change('value', lambda attr, old, new: update_new_file())

inputs = widgetbox(*controls, width=600)

def create_figure():
    p = figure(plot_height = 600, plot_width = 600,
            tools = "xpan,xwheel_zoom,xbox_zoom,reset",
            x_axis_type="datetime"
    )
    return p

def get_active_header():
    f = open(csv_select.value, 'r')
    lines = f.readlines()
    ret = ""
    # this linecount happens because if len(lines)<=N,
    # we end up with Pandas processing two headers,
    # and then the graphing gets fucked up.
    if len(lines) > N:
        ret = lines[0]
    f.close()
    return ret

def tail_active_file():
    return reduce(lambda x, y: x + '\n' + y, tailer.tail(open(csv_select.value), N))

def get_active_df():
    # get an active dataframe from the tail of the csv; need header for column info
    active_df = pd.read_csv(StringIO(get_active_header() + tail_active_file()))
    # fix times in the timeseries
    active_df['Time'] = map(lambda s:
                            datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f"),
                            active_df['Time'])
    return active_df

lines={}

def graph_from_active_tail():
    global lines
    lines = {}
    print "graph_from_active_tail()"
    # create a new figure and populate with
    # current tail of file w/o following it
    p = create_figure()
    df = get_active_df()
    i = 0
    for x in df:
        if x == 'Time':
            continue
        print "graphing {}".format(x)
        lines[x] = p.line(df['Time'], df[x], legend=x, color=colors[i])
        i += 1
    return p

def update_new_file():
    l.children[1].children[1] = graph_from_active_tail()

def update_graph():
    df = get_active_df()
    for key in lines:
        lines[key].data_source.data["y"] = df[key]
        lines[key].data_source.data["x"] = df['Time']

l = layout([[desc],[inputs, graph_from_active_tail()]])

curdoc().add_root(l)
curdoc().add_periodic_callback(update_graph, 300)
curdoc().title = "Live view"

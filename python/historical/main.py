import pandas as pd
from glob import glob

#from multiprocessing import Pool

from bokeh.layouts import layout, widgetbox
from bokeh.models import Select, Div#, RadioButtonGroup
from bokeh.plotting import curdoc, figure

from datetime import datetime

from profilehooks import profile

colors = ['red', 'blue', 'green', 'maroon', 'indigo', 'black',
        'goldenrod', 'mediumslateblue', 'olivedrab', 'saddlebrown',
        'yellowgreen', 'orangered', 'orange', 'limegreen',
        'blueviolet', 'darkblue']

desc = Div(text=open('desc.html', 'r').read(), width=1000)
csvs = glob('./data/*.csv')
#pool = Pool(8)

@profile
def resolve_time(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")

# plot options
plot = figure(
    plot_height=600,
    plot_width=600,
    tools="xpan,ypan,wheel_zoom,xbox_zoom,ybox_zoom,reset",
    x_axis_type='datetime',
    y_axis_location="left"
    )
plot.x_range.follow = 'end'
#plot.x_range.follow_interval = 100
#plot.x_range.range_padding = 0

csv_select = Select(title="File to view", value=csvs[0], options=csvs)

controls = [csv_select]

for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = widgetbox(*controls, width=600)
l = layout([[desc],
            [inputs, plot]])

@profile
def create_figure():
    p = figure(plot_height = 600, plot_width = 600,
            tools = "xpan,xwheel_zoom,xbox_zoom,ybox_zoom,reset",
            x_axis_type="datetime"
    )
    return p

@profile
def graph_csv():
    p = create_figure()
    csv = pd.read_csv(csv_select.value, engine='c')
    csv['Time'] = map(resolve_time, csv['Time'])
    i=0
    for key in csv:
        if key == 'Time':
            continue
        p.line(x=csv['Time'], y=csv[key], legend=key, color = colors[i])
        i+=1
    return p

@profile
def update():
    l.children[1].children[1] = graph_csv()

update()

curdoc().add_root(l)
curdoc().title = "Historical view"

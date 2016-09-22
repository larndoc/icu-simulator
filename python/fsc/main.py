from bokeh.plotting import curdoc
from bokeh.layouts import layout, widgetbox, gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif
from bokeh.models.widgets import Select, TextInput, Div, CheckboxButtonGroup
import traceback

desc = Div(text="<h1>J-MAG FSC Science monitor</h1><p>Shows the science data from the FEE, which is 1 magnetic field scalar and a status byte.</p>", width=800)

#hselect = Select(title="Highlight", value="All", options=["All"]+vectors+status)
rselect = CheckboxButtonGroup(labels=["convert", "0-mean"])
nslider = TextInput(title="Samples", value="1024")

nat_unit = jbif.dfmap_genmap({'Sci_Data': lambda x: x * 0.002026557922})

ds = jbif.CSV_Reader(pattern="FSC_Sci*.csv")
df = ds.get_dataframe()
dF = jbif.dfmap_fft(df)

gt = jbif.Grapher(df=df, indep_var = 'Time', key_group = ['Sci_Data'])
gf = jbif.Grapher(df=dF, indep_var = 'Freq', key_group = ['Sci_Data'],
                  figure_opts = {'x_axis_type':'linear'})
gs = jbif.Grapher(df=df, indep_var = 'Time', key_group = ['Sensor_Laser', 'Laser_Micro', 'Zeeman'], figure_opts={'plot_height': 200})


def _update():
    ds.set_num_dp(int(nslider.value))
    df = ds.get_dataframe()
    if 0 in rselect.active:
        df = nat_unit.apply(df)
    if 1 in rselect.active:
        df = jbif.dfmap_zeromean(df)
    gt.update_graph(df)
    gf.update_graph(jbif.dfmap_fft(df, indep_var='Time'))
    gs.update_graph(df)

def update():
    try:
        _update()
    except Exception as e:
        print(e)
        print(traceback.format_exc())

box = widgetbox(rselect, nslider,  sizing_mode='fixed')
grid = gridplot([[gt.make_new_graph(), gf.make_new_graph()],
                 [gs.make_new_graph(), None]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(update, 500)
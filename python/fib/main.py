from bokeh.plotting import curdoc
from bokeh.layouts import layout, widgetbox, gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif
from bokeh.models.widgets import Select, TextInput, Div, CheckboxButtonGroup

desc = Div(text="<h1>J-MAG FIB Science monitor</h1><p>Shows the science data from the FEE, which are 3 magnetic field vectors and a status byte.</p>", width=800)

vectors = ['Bx', 'By', 'Bz']
status = ['Status']

hselect = Select(title="Highlight", value="All", options=["All"]+vectors+status)
rselect = CheckboxButtonGroup(labels=["convert", "0-mean"])
nslider = TextInput(title="Samples", value="1024")

nat_unit = jbif.dfmap_genmap({'Bx': lambda x: x * 0.002026557922,
                              'By': lambda x: x * 0.002026557922,
                              'Bz': lambda x: x * 0.002026557922})

ds = jbif.CSV_Reader(pattern='FIB_Sci*.csv')
df = ds.get_dataframe()
dF = jbif.dfmap_fft(df)

gt = jbif.Grapher(df=df, indep_var = 'Time', key_group = ['Bx', 'By', 'Bz'])
gf = jbif.Grapher(df=dF, indep_var = 'Freq', key_group = ['Bx', 'By', 'Bz'])
gs = jbif.Grapher(df=df, indep_var = 'Time', key_group = ['Status'])


def update():
    df = ds.get_dataframe()
    if 0 in rselect.active:
        df = nat_unit.apply(df)
    if 1 in rselect.active:
        df = jbif.dfmap_zeromean(df)
    gt.update_graph(df)
    gf.update_graph(jbif.dfmap_fft(df))
    gs.update_graph(df)

hselect.on_change('value', lambda attr, old, new: map(lambda x: x.update_graph(x.ds, highlight=new),
                                                      [gt, gf, gs]))
nslider.on_change('value', lambda attr, old, new: ds.set_num_dp(int(new)))

box = widgetbox(hselect, rselect, nslider,  sizing_mode='fixed')
grid = gridplot([[gt.make_new_graph(), gf.make_new_graph()],
                 [gs.make_new_graph(), None]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(update, 500)

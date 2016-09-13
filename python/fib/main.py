from bokeh.plotting import curdoc
from bokeh.layouts import column, layout, widgetbox, gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif
from bokeh.models.widgets import Select, TextInput, Div

desc = Div(text="<h1>J-MAG FIB Science monitor</h1><p>Shows the science data from the FEE, which are 3 magnetic field vectors and a status byte.</p>", width=800)

vectors = ['Bx', 'By', 'Bz']
status = ['Status']

hselect = Select(title="Highlight", value="All", options=["All"]+vectors+status)
rselect = Select(title="Units", value="converted", options=["raw", "converted"])
nslider = TextInput(title="Samples", value="1024")

nuc_dc = jbif.Natural_Unit_Cooker({  'Bx' : [0, 0.002026557922],
                                     'By' : [0, 0.002026557922],
                                     'Bz' : [0, 0.002026557922],
                                     'Status' : [0, 1]})

#mag_dc = jbif.Magnitude_Cooker()
fft_dc = jbif.FFT_Cooker()
ts = jbif.Grapher(pattern="FIB_Sci*.csv", key_groups=[vectors, status], cooker=nuc_dc, figure_opts = [None, {'plot_height': 200}])
sp = jbif.Grapher(pattern="FIB_Sci*.csv", cooker=fft_dc, indep_var='Freq', key_groups=[vectors], figure_opts={'x_axis_type':'linear'})
#mg = jbif.Grapher(pattern="FIB_Sci*.csv", cooker=mag_dc, key_groups=[['mag']])
tg = ts.make_new_graphs()
fg = sp.make_new_graphs()

rselect.on_change('value', lambda attr, old, new: ts.update_graphs(datafmt=new))
hselect.on_change('value', lambda attr, old, new: ts.update_graphs(highlight=new))
nslider.on_change('value', lambda attr, old, new: ts.update_graphs(samples=new))

box = widgetbox(hselect, rselect, nslider,  sizing_mode='fixed')
grid = gridplot([[tg[0], fg[0]], [tg[1], None]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(ts.update_graphs, 250)
curdoc().add_periodic_callback(sp.update_graphs, 500)

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

nat_unit = jbif.dfmap_genmap({'Bx': lambda x: x * 0.002026557922,
                              'By': lambda x: x * 0.002026557922,
                              'Bz': lambda x: x * 0.002026557922})

g = jbif.Grapher(pattern = "FIB_Sci*.csv",
             key_groups  = [vectors, vectors, status],
             dfmap       = ([nat_unit.apply], [None, jbif.dfmap_fft, None]),
             indep_var   = ['Time', 'Freq', 'Time'],
             figure_opts = [None, {'x_axis_type':'linear'}, {'plot_height':200}])

graphs = g.make_new_graphs()
print("len(graphs)={}".format(len(graphs)))

rselect.on_change('value', lambda attr, old, new: g.update_graphs(datafmt=new))
hselect.on_change('value', lambda attr, old, new: g.update_graphs(highlight=new))
nslider.on_change('value', lambda attr, old, new: g.update_graphs(samples=new))

box = widgetbox(hselect, rselect, nslider,  sizing_mode='fixed')
grid = gridplot([[graphs[0], graphs[1]], [graphs[2], None]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(g.update_graphs, 250)

import jmag_bokeh_if as jbif
from bokeh.layouts import column
from bokeh.plotting import curdoc

fc = jbif.FFT_Cooker()
ff = jbif.Figure_Factory(x_axis_type='linear')

grapher = jbif.Grapher("fakedata.csv", key_groups=[['x','y'],['z']], cooker=fc, indep_var='Freq', figure_factory=ff)
figures = grapher.make_new_graphs()
curdoc().add_root(column(figures[0], figures[1]))
curdoc().add_periodic_callback(grapher.update_graphs, 500)

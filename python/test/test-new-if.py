import jmag_bokeh_if as jbif
from bokeh.layouts import column
from bokeh.plotting import curdoc

grapher = jbif.Grapher("fakedata.csv", key_groups=[['x','y'],['z']])
figures = grapher.make_new_graphs()
curdoc().add_root(column(figures[0], figures[1]))
curdoc().add_periodic_callback(grapher.update_graphs, 50)

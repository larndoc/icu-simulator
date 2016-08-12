import jmag_bokeh_if as jbif
from bokeh.layouts import column
from bokeh.io import output_file, show

output_file("test.html")
grapher = jbif.Grapher("test.csv", key_groups=[['x','y'],['z']])
figures = grapher.make_new_graphs()
print len(figures)
print type(figures)
print type(figures[0])
show(column(figures[0], figures[1]))

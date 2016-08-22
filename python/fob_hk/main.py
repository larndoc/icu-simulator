from bokeh.plotting import curdoc
from bokeh.layouts import column
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif

g = jbif.Grapher(jbif.get_latest_csv(jbif.data_dir + "FOB_HK*.csv"),
            indep_var='Time',
            key_groups = [['FOB']]
    )

l = column(*g.make_new_graphs())

curdoc().add_root(l)
curdoc().add_periodic_callback(g.update_graphs, 100)

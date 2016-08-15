from .. import jmag_bokeh_if as jbif
from bokeh.plotting import curdoc
from bokeh.layouts import row

g = jbif.Grapher(jbif.get_latest_csv("data/PCU_HK*.csv"), indep_var='Time',
            key_groups = [['I_FIB' ,'I_FOB' ,'I_FSC' ,'I_P3V3',
                           'I_FIBH','I_FOBH','I_FSCH','I_P1V8'],
                          ['V_P2V4','V_P3V3','V_P12V','V_P8V' ,
                           'V_N8V' ,'V_P5V' ,'V_N5V'],
                          ['Temp']]
    )

l = row(*g.make_new_graphs())

curdoc().add_root(l)
curdoc().add_periodic_callback(g.update_graphs, 100)

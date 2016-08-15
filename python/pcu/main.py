from bokeh.plotting import curdoc
from bokeh.layouts import column
from bokeh.models.widgets import Toggle
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif

nuc_dc = jbif.Natural_Unit_Cooker({  'Temp' : 0.118480,     'V_P2V4' : 0.805664e-3,
                                   'V_P3V3' : 1.067505e-3,   'V_N8V' : 2.607327e-3,
                                    'V_P5V' : 1.611328e-3,   'V_N5V' : 1.614557e-3,
                                   'V_P12V' : 3.886665e-3,   'V_P8V' : 2.584172e-3,
                                    'I_FIB' : 0.1611328e-3,  'I_FOB' : 0.1611328e-3,
                                   'I_P3V3' : 0.1611328e-3, 'I_FIBH' : 0.1611328e-3,
                                   'I_FOBH' : 0.1611328e-3, 'I_P1V8' : 0.1611328e-3,
                                   'I_FSCH' : 0,             'I_FSC' : 0}) # FSC TODO

g = jbif.Grapher(jbif.get_latest_csv("data/PCU_HK*.csv"), indep_var='Time',
            key_groups = [['I_P3V3', 'I_FIB', 'I_FOB', 'I_FSC',
                           'I_FIBH','I_FOBH','I_FSCH','I_P1V8'],
                          ['V_P2V4','V_P3V3','V_P12V','V_P8V' ,
                           'V_N8V' ,'V_P5V' ,'V_N5V'],
                          ['Temp']],
            cooker = nuc_dc
    )

#to_cook_or_not_to_cook.on_change('value', lambda attr, old, new: g.get_csv_reader().on_change)

l = column(*g.make_new_graphs())

curdoc().add_root(l)
curdoc().add_periodic_callback(g.update_graphs, 100)

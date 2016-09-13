from bokeh.plotting import curdoc
from bokeh.layouts import column, layout, widgetbox, gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif
from bokeh.models import Div
from bokeh.models.widgets import Select, Slider

desc = Div(text="<h1>J-MAG PCU HK monitor</h1><p>Shows the HK information from the PCU, which are voltages, currents and temperature(s). <br/>Values are shown in raw ADC counts.</p>", width=800)

voltages = ['V_P2V4', 'V_P3V3', 'V_P12V', 'V_P8V', 'V_N8V', 'V_P5V', 'V_N5V']
currents = ['I_P1V8', 'I_P3V3', 'I_FIB', 'I_FIBH', 'I_FOB', 'I_FOBH', 'I_FSC', 'I_FSCH']
temps = ['Temp']

hselect = Select(title="Highlight", value="All", options=["All"]+voltages+currents+temps)
rselect = Select(title="Units", value="converted", options=["raw", "converted"])
nslider = Slider(title="Samples", start=256, end=16384, value=1024, step=128)

nuc_dc = jbif.Natural_Unit_Cooker({  'Temp' : [-273.15, 0.118480],
                                     'V_P2V4' : [0 ,0.805664e-3],
                                     'V_P3V3' : [0 ,1.067505e-3],
                                     'V_N8V' : [0 ,2.607327e-3],
                                     'V_P5V' : [0 ,1.611328e-3],
                                     'V_N5V' : [0, 1.614557e-3],
                                     'V_P12V' : [0, 3.886665e-3],
                                     'V_P8V' : [0, 2.584172e-3],
                                     'I_FIB' : [0, 0.1611328e-3],
                                     'I_FOB' : [0, 0.1611328e-3],
                                     'I_P3V3' : [0, 0.1611328e-3], 
                                     'I_FIBH' : [0, 0.1611328e-3],
                                     'I_FOBH' : [0, 0.1611328e-3],
                                     'I_P1V8' : [0, 0.1611328e-3],
                                     'I_FSCH' : [0, 0.1611328e-3],
                                     'I_FSC' : [0, 0.1611328e-3]})

g = jbif.Grapher(pattern="PCU_HK*.csv",
            indep_var='Time',
            figure_opts=[None, None, {'plot_height': 200}],
            key_groups = [voltages, currents, temps],
            cooker = nuc_dc
    )

#to_cook_or_not_to_cook.on_change('value', lambda attr, old, new: g.get_csv_reader().on_change)

elems = g.make_new_graphs()

rselect.on_change('value', lambda attr, old, new: g.update_graphs(datafmt=new))
hselect.on_change('value', lambda attr, old, new: g.update_graphs(highlight=new))
nslider.on_change('value', lambda attr, old, new: g.update_graphs(samples=new))

box = widgetbox(hselect, rselect, nslider, sizing_mode='fixed')
grid = gridplot([[elems[0], elems[1]], [elems[2], None]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(g.update_graphs, 500)

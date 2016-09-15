from bokeh.plotting import curdoc
from bokeh.layouts import column, layout, widgetbox, gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif
from bokeh.models import Div
from bokeh.models.widgets import Select, Slider, CheckboxButtonGroup, TextInput

desc = Div(text="<h1>J-MAG PCU HK monitor</h1><p>Shows the HK information from the PCU, which are voltages, currents and temperature(s). <br/>Values are shown in raw ADC counts.</p>", width=800)

voltages = ['V_P2V4', 'V_P3V3', 'V_P12V', 'V_P8V', 'V_N8V', 'V_P5V', 'V_N5V']
currents = ['I_P1V8', 'I_P3V3', 'I_FIB', 'I_FIBH', 'I_FOB', 'I_FOBH', 'I_FSC', 'I_FSCH']
temps = ['Temp']

hselect = Select(title="Highlight", value="All", options=["All"]+voltages+currents+temps)
rselect = CheckboxButtonGroup(labels=["convert", "0-mean"])
nslider = TextInput(title="Samples", value="1024")

nat_unit = jbif.dfmap_genmap({'Temp': lambda x: x * 0.118480 - 273.15,
                              'V_P2V4' : lambda x: x * 0.805664e-3,
                              'V_P3V3' : lambda x: x * 1.067505e-3,
                              'V_N8V' : lambda x: x * 2.607327e-3,
                              'V_P5V' : lambda x: x * 1.611328e-3,
                              'V_N5V' : lambda x: x * 1.614557e-3,
                              'V_P12V' : lambda x: x * 3.886665e-3,
                              'V_P8V' : lambda x: x * 2.584172e-3,
                              'I_FIB' : lambda x: x * 0.1611328e-3,
                              'I_FOB' : lambda x: x * 0.1611328e-3,
                              'I_P3V3' : lambda x: x * 0.1611328e-3,
                              'I_FIBH' : lambda x: x * 0.1611328e-3,
                              'I_FOBH' : lambda x: x * 0.1611328e-3,
                              'I_P1V8' : lambda x: x * 0.1611328e-3,
                              'I_FSCH' : lambda x: x * 0.1611328e-3,
                              'I_FSC' : lambda x: x * 0.1611328e-3})

g = jbif.Grapher(pattern="PCU_HK*.csv",
            indep_var='Time',
            figure_opts=[None, None, {'plot_height': 200}],
            key_groups = [voltages, currents, temps],
            dfmap=nat_unit.apply,
            cook_data=False
    )

#to_cook_or_not_to_cook.on_change('value', lambda attr, old, new: g.get_csv_reader().on_change)

def data_processing_checker(new):
    print("changing cooking", new)
    if 0 in new:
        g.cook_data(True)
    else:
        g.cook_data(False)

elems = g.make_new_graphs()

rselect.on_click(data_processing_checker)
hselect.on_change('value', lambda attr, old, new: g.update_graphs(highlight=new))
nslider.on_change('value', lambda attr, old, new: g.update_graphs(samples=new))

box = widgetbox(hselect, rselect, nslider, sizing_mode='fixed')
grid = gridplot([[elems[0], elems[1]], [elems[2], None]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(g.update_graphs, 500)

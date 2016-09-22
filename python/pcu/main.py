from bokeh.plotting import curdoc
from bokeh.layouts import layout, widgetbox, gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif
from bokeh.models.widgets import Select, TextInput, Div, CheckboxButtonGroup
import traceback

desc = Div(text="<h1>J-MAG PCU HK monitor</h1><p>Shows the HK information from the PCU, which are voltages, currents and temperature(s). <br/>Values are shown in raw ADC counts.</p>", width=800)

voltages = ['V_P2V4', 'V_P3V3', 'V_P12V', 'V_P8V', 'V_N8V', 'V_P5V', 'V_N5V']
currents = ['I_P1V8', 'I_P3V3', 'I_FIB', 'I_FIBH', 'I_FOB', 'I_FOBH', 'I_FSC', 'I_FSCH']
temps = ['Temp']

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

ds1 = jbif.CSV_Reader(pattern="PCU_HK*.csv")
df = ds1.get_dataframe()
gs = []
gs.append(jbif.Grapher(df=df, indep_var = 'Time', key_group = voltages))
gs.append(jbif.Grapher(df=df, indep_var = 'Time', key_group = currents))
gs.append(jbif.Grapher(df=df, indep_var = 'Time', key_group = temps, figure_opts={'plot_height': 200}))

ds2 = jbif.CSV_Reader(pattern="PIF_HK*.csv")
df = ds2.get_dataframe()
gs.append(jbif.Grapher(df=df, indep_var = 'Time', key_group = ["I1", "I2"], figure_opts={'plot_height': 200}))

def _update():
    ds1.set_num_dp(int(nslider.value))
    ds2.set_num_dp(int(nslider.value))

    df = ds1.get_dataframe()
    if 0 in rselect.active:
        df = nat_unit.apply(df)
    if 1 in rselect.active:
        df = jbif.dfmap_zeromean(df)

    gs[0].update_graph(df)
    gs[1].update_graph(df)
    gs[2].update_graph(df)

    df = ds2.get_dataframe()
    gs[3].update_graph(df)

def update():
    try:
        _update()
    except Exception as e:
        print(e)
        print(traceback.format_exc())

box = widgetbox(rselect, nslider,  sizing_mode='fixed')
grid = gridplot([[gs[0].make_new_graph(), gs[1].make_new_graph()],
                 [gs[2].make_new_graph(), gs[3].make_new_graph()]])

l = layout([desc], [box, grid])

curdoc().add_root(l)
curdoc().add_periodic_callback(update, 500)

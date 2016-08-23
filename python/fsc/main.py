from bokeh.plotting import curdoc
from bokeh.layouts  import gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif

fft_dc = jbif.FFT_Cooker()
ff     = jbif.Figure_Factory(x_axis_type='linear')

ts = jbif.Grapher(jbif.get_latest_csv(jbif.data_dir + "FSC_SCI_*.csv"), key_groups=[['Sensor_Laser'], ['Laser_Micro'], ['Zeeman'], ['Sci_Data']])
sp = jbif.Grapher(jbif.get_latest_csv(jbif.data_dir + "FSC_SCI_*.csv"), cooker=fft_dc, indep_var='Freq', key_groups=[['Sci_Data']], figure_factory=ff)

timeseries = ts.make_new_graphs()
spectra    = sp.make_new_graphs()

l = gridplot(
       [[timeseries[3], spectra[0]],
        [timeseries[0], None],
        [timeseries[1], None],
        [timeseries[2], None]]
        )

curdoc().add_root(l)
curdoc().add_periodic_callback(ts.update_graphs, 100)
curdoc().add_periodic_callback(sp.update_graphs, 500)

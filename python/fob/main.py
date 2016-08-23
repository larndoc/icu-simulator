from bokeh.plotting import curdoc
from bokeh.layouts  import gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif

# TODO: this is the exact same thing as FIB,
# except apparently there's a different parameter
# I should be tracking instead. Altering the code
# to follow this parameter is left as an exercise
# to the reader.

mag_dc = jbif.Magnitude_Cooker()
fft_dc = jbif.FFT_Cooker()
ff     = jbif.Figure_Factory(x_axis_type='linear')

ts = jbif.Grapher(jbif.get_latest_csv(jbif.data_dir + "FIB*.csv"), key_groups=[['Bx'], ['By'], ['Bz'], ['Status']])
sp = jbif.Grapher(jbif.get_latest_csv(jbif.data_dir + "FIB*.csv"), cooker=fft_dc, indep_var='Freq', key_groups=[['Bx'], ['By'], ['Bz']], figure_factory=ff)
mg = jbif.Grapher(jbif.get_latest_csv(jbif.data_dir + "FIB*.csv"), cooker=mag_dc, key_groups=[['mag']])

timeseries = ts.make_new_graphs()
spectra    = sp.make_new_graphs()
magnitude  = mg.make_new_graphs()

l = gridplot(
       [[timeseries[0], spectra[0]],
        [timeseries[1], spectra[1]],
        [timeseries[2], spectra[2]],
        [magnitude[0] , timeseries[3]]]
        )

curdoc().add_root(l)
curdoc().add_periodic_callback(ts.update_graphs, 100)
curdoc().add_periodic_callback(sp.update_graphs, 500)
curdoc().add_periodic_callback(mg.update_graphs, 100)

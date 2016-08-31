from bokeh.plotting import curdoc
from bokeh.layouts  import gridplot
import sys
sys.path.append("..")
import jmag_bokeh_if as jbif

mag_dc = jbif.Magnitude_Cooker()
fft_dc = jbif.FFT_Cooker()

ts = jbif.Grapher(pattern="FIB_Sci*.csv", key_groups=[['Bx'], ['By'], ['Bz'], ['Status']],
        figure_opts=[{'plot_width':1000, 'plot_height':1000},
                     {'plot_width':600 , 'plot_height':600 },
                     None,
                     None])
sp = jbif.Grapher(pattern="FIB_Sci*.csv", cooker=fft_dc, indep_var='Freq', key_groups=[['Bx'], ['By'], ['Bz']], figure_opts={'x_axis_type':'linear'})
mg = jbif.Grapher(pattern="FIB_Sci*.csv", cooker=mag_dc, key_groups=[['mag']])

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

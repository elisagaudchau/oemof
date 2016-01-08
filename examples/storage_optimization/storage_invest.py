# -*- coding: utf-8 -*-

"""
General description:
---------------------

The example models the following energy system:

                input/output  bgas     bel
                     |          |        |       |
                     |          |        |       |
 wind(FixedSource)   |------------------>|       |
                     |          |        |       |
 pv(FixedSource)     |------------------>|       |
                     |          |        |       |
 rgas(Commodity)     |--------->|        |       |
                     |          |        |       |
 demand(Sink)        |<------------------|       |
                     |          |        |       |
                     |          |        |       |
 pp_gas(Transformer) |<---------|        |       |
                     |------------------>|       |
                     |          |        |       |
 storage(Storage)    |<------------------|       |
                     |------------------>|       |


"""

###############################################################################
# imports
###############################################################################
import matplotlib.pyplot as plt
import pandas as pd

# import solph module to create/process optimization model instance
from oemof.solph import predefined_objectives as predefined_objectives

# Outputlib
from oemof.outputlib import to_pandas as tpd

# import oemof base classes to create energy system objects
from oemof.core import energy_system as es
from oemof.core.network.entities import Bus
from oemof.core.network.entities.components import sinks as sink
from oemof.core.network.entities.components import sources as source
from oemof.core.network.entities.components import transformers as transformer


###############################################################################
# read data from csv file
###############################################################################

data = pd.read_csv("storage_invest.csv", sep=",")
timesteps = [t for t in range(8760)]

###############################################################################
# initialize the energy system
###############################################################################

simulation = es.Simulation(
    timesteps=timesteps, stream_solver_output=True, solver='glpk',
    objective_options={'function': predefined_objectives.minimize_cost})

energysystem = es.EnergySystem(year=2016, simulation=simulation)

###############################################################################
# set optimzation options for storage components
###############################################################################

transformer.Storage.optimization_options.update({'investment': True})

###############################################################################
# Create oemof objetc
###############################################################################

# create bus
bgas = Bus(uid="bgas",
           type="gas",
           price=70,
           balanced=True,
           excess=False)

# create electricity bus
bel = Bus(uid="bel",
          type="el",
          excess=True)

# create commodity object for gas resource
rgas = source.Commodity(uid='rgas',
                        outputs=[bgas],
                        sum_out_limit=194397000)

# create fixed source object for wind
wind = source.FixedSource(uid="wind",
                          outputs=[bel],
                          val=data['wind'],
                          out_max=[1000000],
                          add_out_limit=0,
                          capex=1000,
                          opex_fix=20,
                          lifetime=25,
                          crf=0.08)

# create fixed source object for pv
pv = source.FixedSource(uid="pv",
                        outputs=[bel],
                        val=data['pv'],
                        out_max=[582000],
                        add_out_limit=0,
                        capex=900,
                        opex_fix=15,
                        lifetime=25,
                        crf=0.08)

# create simple sink object for demand
demand = sink.Simple(uid="demand", inputs=[bel], val=data['demand_el'])

# create simple transformer object for gas powerplant
pp_gas = transformer.Simple(uid='pp_gas',
                            inputs=[bgas], outputs=[bel],
                            opex_var=50, out_max=[10e10], eta=[0.58])

# create storage transformer object for storage
storage = transformer.Storage(uid='sto_simple',
                              inputs=[bel],
                              outputs=[bel],
                              eta_in=1,
                              eta_out=0.8,
                              cap_loss=0.00,
                              opex_fix=35,
                              opex_var=10e10,
                              capex=1000,
                              cap_max=0,
                              cap_initial=0,
                              c_rate_in=1/6,
                              c_rate_out=1/6)

###############################################################################
# Optimise the energy system and plot the results
###############################################################################

# If you dumped the energysystem once, you can skip the optimisation wtih '#'
# and use the restore method.
energysystem.optimize()

# energysystem.dump()
# energysystem.restore()

# Creation of a multi-indexed pandas dataframe
es_df = tpd.EnergySystemDataFrame(energy_system=energysystem,
                                  idx_start_date="2016-01-01 00:00:00",
                                  ixd_date_freq="H")
es_df.data_frame.describe

# Plotting line plots
es_df.plot_bus(bus_uid="bel", bus_type="el", type="input",
               date_from="2016-01-01 00:00:00",
               date_to="2016-01-31 00:00:00",
               title="January 2016", xlabel="Power in MW",
               ylabel="Date", tick_distance=24*7)

es_df.plot_bus(bus_uid="bgas", bus_type="gas", type="output",
               date_from="2016-01-01 00:00:00",
               date_to="2016-12-31 00:00:00",
               title="Year 2016", xlabel="Outflow in MW",
               ylabel="Date", tick_distance=24*7*4*3)

plt.show()

# Plotting a combined stacked plot
fig = plt.figure(figsize=(24, 14))
plt.rc('legend', **{'fontsize': 19})
ax = fig.add_subplot(1, 1, 1)

es_df.stackplot(bus_uid="bel", bus_type="el", ax=ax,
                date_from="2016-06-01 00:00:00",
                date_to="2016-06-8 00:00:00",
                title="Electricity bus",
                ylabel="Power in MW", xlabel="Date",
                linewidth=4,
                tick_distance=24)

plt.show()

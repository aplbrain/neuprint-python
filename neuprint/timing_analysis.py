"""
Functions for performing spicedbased electrical simulation of a neuron given
its synapses and skeleton using a simple linear passive model.

This tool depends on the installation of nspice.

Delay modeling and spice parsing adapted from code  by Louis K. Scheffer.

Author: Stephen Plaza
"""

from .utils import tqdm
from .client import default_client
from .queries import fetch_synapse_connections
from scipy.spatial import cKDTree
import numpy as np
import pandas as pd
import math
import sys
import os

"""
Axon resistance.
"""
Ra_LOW = 0.4
Ra_MED=1.2
Ra_HIGH=4.0

"""
Membrane resistance.
"""
Rm_LOW = 0.2
Rm_MED=0.8
Rm_HIGH=3.11

class TimingResult:
    def __init__(self, bodyid, delay_matrix, amplitude_matrix, neuron_io, symmetric=False):
        """
        Timing rseult constructor.

        Provides methods for parsing timing results.
        
        Args:

            bodyid (int):
                Segment id for neuron
       
            delay_matrix (dataframe):
                nxm matric of source to sink (if source set == sink set,
                the data can be used to cluster the provided io into different domains.
       
            neuron_io (dataframe):
                synapse information: location, ispre, brain region
        """
        self.bodyid = bodyid
        self.delay_matrix = delay_matrix
        self.amplitude_matrix = amplitude_matrix
        self.neuron_io = neuron_io
        self.symmetric = symmetric
           
        """
        sources = set(delay_matrix.index.to_list())
        sinks = set(delay_matrix.columns.values())
        if sources == sinks:
            self.symmetric = True
        """

    def compute_region_delay_matrix(self):
        """
        Generate delay and amplitude matrix based on primary brain regions.

        Averages the delay and amplitude between the sources and sinks of the
        timing results.

        Returns:
            (dataframe, dataframe) for the delay and amplitude from brain region to brain region.
        """
    
        # determine row and column names
        inrois = set(self.neuron_io[self.neuron_io["io"] == "in"]["roi"].to_list())
        outrois = set(self.neuron_io[self.neuron_io["io"] == "out"]["roi"].to_list())
        
        inrois = list(inrois)
        outrois = list(outrois)

        inrois.sort()
        outrois.sort()
        
        delay_matrix = np.zeros((len(inrois), len(outrois)))
        amp_matrix = np.zeros((len(inrois), len(outrois)))

        roi_count = {}
        roi_delays = {}
        roi_amps = {}

        roi2index_in = {}
        roi2index_out = {}
        for idx, roi in enumerate(inrois):
            roi2index_in[roi] = idx
        for idx, roi in enumerate(outrois):
            roi2index_out[roi] = idx
        
        # roi info
        for drive, row in self.delay_matrix.iterrows():
            inroi = self.neuron_io[self.neuron_io["swcid"] == drive].iloc[0]["roi"]
            for out, val in row.items(): 
                outroi = self.neuron_io[self.neuron_io["swcid"] == out].iloc[0]["roi"]
                if (inroi, outroi) not in roi_delays:
                    roi_delays[(inroi, outroi)] = 0
                    roi_count[(inroi, outroi)] = 0
                roi_delays[(inroi, outroi)] += val
                roi_count[(inroi, outroi)] += 1

        # calculate average
        for drive, row in self.amplitude_matrix.iterrows():
            inroi = self.neuron_io[self.neuron_io["swcid"] == drive].iloc[0]["roi"]
            for out, val in row.items(): 
                outroi = self.neuron_io[self.neuron_io["swcid"] == out].iloc[0]["roi"]
                if (inroi, outroi) not in roi_amps:
                    roi_amps[(inroi, outroi)] = 0
                roi_amps[(inroi, outroi)] += val
        
        for key, val in roi_count.items():
            roi_in, roi_out = key
            idx1 = roi2index_in[roi_in]
            idx2 = roi2index_out[roi_out]
            delay_matrix[idx1, idx2] = roi_delays[key] / val
            amp_matrix[idx1, idx2] = roi_amps[key] / val
       
        # return dataframes
        return pd.DataFrame(delay_matrix, index=inrois, columns=outrois), pd.DataFrame(amp_matrix, index=inrois, columns=outrois) 


    def plot_response_from_region(self, brain_region, filename=None):
        """
        Show neuron response to brain regions based on inputs from a given region.

        Args:

            brain_region (str):
                Source brain region.
            filename (str):
                Optionally save plot to designated file
        """

        # matplot for amplitude and delay
        
        # filter sample brain region inputs
        inputs = self.neuron_io[(self.neuron_io["roi"] == brain_region) & (self.neuron_io["io"] == "in")]["swcid"].to_list()
        delay_matrix_sub = self.delay_matrix[self.delay_matrix.index.isin(inputs)]
        delay_matrix_sub = self.delay_matrix[self.delay_matrix.index.isin(inputs)]
        outrois = set(self.neuron_io[self.neuron_io["io"] == "out"]["roi"].to_list())

        delay_amp_region = []

        for drive, row in delay_matrix_sub.iterrows():
            row2 = self.amplitude_matrix.loc[drive]
            for out, val in row.items(): 
                outroi = self.neuron_io[self.neuron_io["swcid"] == out].iloc[0]["roi"]
                amp = row2[out] 
                delay_amp_region.append([val, amp, outroi])

        plot_df = pd.DataFrame(delay_amp_region, columns=["delay", "amp", "region"])
        
        # create plot
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        for region in plot_df["region"].unique():
            tdata = plot_df[plot_df["region"] == region] 
            ax.scatter(tdata["delay"].to_list(), tdata["amp"].to_list(), c=[np.random.rand(3,)], label=region)
        ax.legend()
        plt.xlabel("delay (ms)")
        plt.ylabel("amplitude (mV)")

        # only show graph interactively if in a notebook 
        import ipykernel.iostream
        if isinstance(sys.stdout, ipykernel.iostream.OutStream):
            plt.show()

        if filename is not None:
            plt.savefig(filename)

    def estimate_neuron_domains(self, num_components=0, show_plot=False, plot_file=None):
        """ ** TODO **
        Estimate the domains based on timing estimates.

        Note: only works for symmetric sink and source simulation.

        Args:
            num_components (int):
                number of cluster domains (0 means to auto choose based on kmeans silhouette)
            show_plot (bool):
                show scatter plot of delay to different region (from synapse IO)
            plot_file (str):
                save plot to file as png
        
        Returns:
            (dataframe, dataframe) input and output connection summary split by domain,
            neuron_io indicating component partition
        """
        
        # TODO
        # build KD tree and associate synapses with each point after the cluster
        # potentially add ROI and #matches for each point in plot
        # kd tree match needed to export the neuron io table
        pass            

class NeuronModel:
    def __init__(self, bodyid, Ra=Ra_MED, Rm=Rm_MED, Cm=1e-2, client=None):
        """
        Neuron model constructor.

        Create model of a neuron which can be simulated.
        in different ways.

        Args:

            bodyid (int):
                Segment id for neuron.
            Ra (float):
                axon resistance (e.g., 0.4, 1.2, or 4.0)
            Rm (float):
                membrane resistance (e.g., 0.2, 0.8, or 3.11)
            Cm (float):
                membrane capacitance (should not very too much between neurons)
        """
        self.bodyid = bodyid
       

        with tqdm(total=100) as pbar: 
            # retrieve healed skeleton
            if client is None:
                client = default_client()
            pbar.set_description("fetching skeleton")
            self.skeleton_df = client.fetch_skeleton(bodyid, heal=True)
            #print("Fetched skeleton")
            pbar.update(20)

            # extract inputs and outputs
            pbar.set_description("fetching output connections")
            outputs = fetch_synapse_connections(bodyid, client=client)
            pbar.update(35)
            pbar.set_description("fetching input connections")
            inputs = fetch_synapse_connections(None, bodyid, client=client)
            pbar.update(35)
            pbar.set_description("creating spice model")
            #print("Fetched synapse connections")

            # combine into one dataframe

            inputs["type"] = ["post"]*len(inputs)
            inputs = inputs[["type", "x_post", "y_post", "z_post", "roi_post", "bodyId_pre" ]].rename(columns={"x_post": "x", "y_post": "y", "z_post": "z", "roi_post": "roi", "bodyId_pre": "partner"})
            inputs["roi"].replace(np.nan, "none", inplace=True)
            
            input_pins = inputs[["roi"]].copy()
            input_pins["coords"] = list(zip(inputs["x"], inputs["y"], inputs["z"]))
            input_pins["io"] = ["in"]*len(inputs)

            outputs["type"] = ["pre"]*len(outputs)
            outputs = outputs[["x_pre", "y_pre", "z_pre", "roi_pre", "bodyId_post" ]].rename(columns={"x_pre": "x", "y_pre": "y", "z_pre": "z", "roi_pre": "roi", "bodyId_post": "partner"})
            outputs["roi"].replace(np.nan, "none", inplace=True)
            
            output_pins = outputs[["roi"]].copy()
            output_pins["coords"] = list(zip(outputs["x"], outputs["y"], outputs["z"]))
            output_pins["io"] = ["out"]*len(outputs)

            self.neuron_conn_info = pd.concat([inputs, outputs]).reset_index(drop=True)
            self.io_pins = pd.concat([input_pins, output_pins]).reset_index(drop=True)
            self.Ra = Ra 
            self.Rm = Rm
            self.Cm = 1e-2 # farads per square meeter

            # associate node with each input and output (this will be subsampled later)
            # build kdtree
            tree = cKDTree(list(zip(self.skeleton_df["x"], self.skeleton_df["y"], self.skeleton_df["z"])))
            # apply
            self.io_pins["swcid"] = self.io_pins["coords"].apply(lambda x: tree.query(x)[1]+1)
                

            # get voxelSize (8e-9) assume nanometers
            self.resolution = client.fetch_custom("MATCH (m :Meta) RETURN m.voxelSize").iloc[0][0][0] * 1e-9

            def build_spice_model():
                #F is the indefinite integral of the area of a cone going from radius r1 to r2 over length L
                def F(x, r1, r2, L):
                    return 2.0*math.pi*(r1*x + (r2-r1)*x**2/(2*L))

                #G is the indefinite integral of the resistance of a cone going from radius r1 to r2 over length L
                def G(x, r1, r2, L):
                    if (r1 != r2):
                        return -(1.0/math.pi) * (L/(r2-r1) * 1.0/(r1 + (r2-r1)*x/L))
                    else:
                        return (1.0/math.pi) * (1.0/r1**2) * x

                # build model
                cs = [0.0] * len(self.skeleton_df)
                rg = [1e30]* len(self.skeleton_df)
                rs = [[0, 0, 1.0] for i in range(len(self.skeleton_df))]   # N-1 Rs, first has none.  node, node, value
              
                for idx, fromrow in  self.skeleton_df.iterrows():
                    if idx == 0:
                        continue
                
                    # only one root, should be first entry
                    assert(fromrow["link"] != -1)

                    # row number = link - 1
                    parent = int(fromrow["link"]-1)
                    torow = self.skeleton_df.iloc[parent]
              
                    # compute axonal resistance
                    L = math.sqrt((fromrow["x"] - torow["x"])**2 + (fromrow["y"] - torow["y"])**2 + (fromrow["z"] - torow["z"])**2) * self.resolution

                    if L == 0:
                        print("L=0 - should not happen")
                        L = 1.0e-9   # set to 1 nm

                    r1 = fromrow["radius"] * self.resolution
                    r2 = torow["radius"] * self.resolution

                    # axonal resistance
                    res = (G(L, r1, r2, L) - G(0, r1, r2, L)) * self.Ra
                    
                    # compute membrane resistance both to and from
                    area_from = F(L/2, r1, r2, L) - F(  0, r1, r2, L)   # Half of segment
                    c_from = area_from * self.Cm
                    rg_from = self.Rm / area_from
                    area_to   = F(L,   r1, r2, L) - F(L/2, r1, r2, L)   # other half
                    c_to   = area_to * self.Cm
                    rg_to = self.Rm / area_to
                    cs[idx] += c_from
                    rg[idx] = rg[idx] * rg_from / (rg[idx] + rg_from)  # in parallel
                    cs[parent] += c_to
                    rg[parent] = rg[parent] * rg_to / (rg[parent] + rg_to)  # in parallel
                    rs[idx][0] = idx
                    rs[idx][1] = parent
                    rs[idx][2] = res
                for i in range(len(cs)):
                    cs[i] = cs[i] * 1000.0  # Convert millisec responses to seconds, to make moments numerically better

                # write-out model string
                modelstr = ""
                for i in range(len(cs)):
                    modelstr += f"C{i+1} {i+1} 0 {cs[i]}\n" # grounded C
                    modelstr += f"RG{i+1} {i+1} 0 {rg[i]}\n" # grounded R membrane resistance
                    assert(rg[i] > 0)
                    if i > 0:
                        modelstr += f"R{i+1} {rs[i][0]+1} {rs[i][1]+1} {rs[i][2]}\n" # axonal resistance
                        assert(rs[i][2] > 0)

                return modelstr 
            
            self.spice_model = build_spice_model()
            pbar.update(10)
            pbar.set_description("built model")
            #print("Built model")

    def _runspice(self, drive, unique_outs):
        """
        Run spice injecting current for a given input and return response for all outputs.
        
        Note: drive and unique_outs should be swc node ids for an input and output.
        
        Args:
        
            drive (int):
                id for input
            unique_outs (list):
                ids for outputs
        
        Returns:

            Dataframe (output ids, delay, amplitude)
        """
 
        # apply current at the specified input location
        drive_str = f"RDRIVE {drive} {len(self.skeleton_df)+1} 10000000000\n" # 0.1 ns conductance
        drive_str += f"V1 {len(self.skeleton_df)+1} 0 EXP(0 60.0 0.1 0.1 1.1 1.0 40)\n"
        drive_str += ".tran 0.1 40\n" # work from 0-10 ms (try 40)
 
        # call command line spice simulator and write to temporary file
        from tempfile import mkstemp
        from subprocess import Popen, PIPE, DEVNULL

        fd, path = mkstemp()

        # run ngspice
        p = Popen(["ngspice", "-b", "-r", path], stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        data = self.spice_model + drive_str
        p.stdin.write(data.encode())
        p.stdin.close()
        p.wait()

        """Read ngspice binary raw files. Return tuple of the data, and the
        plot metadata. The dtype of the data contains field names. This is
        not very robust yet, and only supports ngspice.
        
        # Example header of raw file
        # Title: rc band pass example circuit
        # Date: Sun Feb 21 11:29:14  2016
        # Plotname: AC Analysis
        # Flags: complex
        # No. Variables: 3
        # No. Points: 41
        # Variables:
        #         0       frequency       frequency       grid=3
        #         1       v(out)  voltage
        #         2       v(in)   voltage
        # Binary:
        """
        sim_results = None
        BSIZE_SP = 512 # Max size of a line of data; we don't want to read the
                        # whole file to find a line, in case file does not have
                        # expected structure.
        MDATA_LIST = [b'title', b'date', b'plotname', b'flags', b'no. variables', b'no. points', b'dimensions', b'command', b'option']
        with os.fdopen(fd, 'rb') as fp:
            plot = {}
            count = 0
            arrs = []
            plots = []
            while (True):
                try:
                    mdata = fp.readline(BSIZE_SP).split(b':', maxsplit=1)
                except:
                    raise RuntimeError("cannot parse spice output")
                if len(mdata) == 2:
                    if mdata[0].lower() in MDATA_LIST:
                        plot[mdata[0].lower()] = mdata[1].strip()
                    if mdata[0].lower() == b'variables':
                        nvars = int(plot[b'no. variables'])
                        npoints = int(plot[b'no. points'])
                        plot['varnames'] = []
                        plot['varunits'] = []
                        for varn in range(nvars):
                            varspec = (fp.readline(BSIZE_SP).strip()
                                       .decode('ascii').split())
                            assert(varn == int(varspec[0]))
                            plot['varnames'].append(varspec[1])
                            plot['varunits'].append(varspec[2])
                    if mdata[0].lower() == b'binary':
                        rowdtype = np.dtype({'names': plot['varnames'],
                                             'formats': [np.complex_ if b'complex'
                                                         in plot[b'flags']
                                                         else np.float_]*nvars})
                        # We should have all the metadata by now
                        arrs.append(np.fromfile(fp, dtype=rowdtype, count=npoints))
                        plots.append(plot)
                        fp.readline() # Read to the end of line
                else:
                    break

            # only one analysis
            sim_results = arrs[0]
        # delete file
        os.unlink(path)
        
        times = [0.0] * len(sim_results)
        # for each output (based on skeleton compartment id),
        # determine the delay to the max voltage and the width
        out_results = [] 
        
        for i in range(len(sim_results)):
            times[i] = sim_results[i]["time"]
            # parse out delay and amplitdue responses
        volts = [0.0] * len(sim_results)
        
        for idx in range(len(unique_outs)):
            # compartment id
            j = unique_outs[idx] 
            
            for i in range(len(sim_results)):
                volts[i] = sim_results[i][j]
            
            #Now find max voltage, time at max voltag, 
            maxv = 0.0
            maxt = -1
            for i in range(1,len(volts)-1):
                if volts[i-1] < volts[i] and volts[i] > volts[i+1]:
                    #interpolate to find max
                    v1 = volts[i-1] - volts[i]  #relative value at t1 (negative)
                    v2 = volts[i+1] - volts[i]  #same for t2
                    x1 = times[i-1] - times[i]
                    x2 = times[i+1] - times[i]
                    a = (v1 - v2*x1/x2)/(x1**2 - x1*x2)
                    b = (v1 - a*x1**2)/x1
                    deltax = -b/(2*a)
                    maxv = volts[i]
                    maxt = times[i] + deltax
                    break     # should be only one peak.
            assert(maxt >= 0)
          
            maxt -= 1.1   # subtract the peak time of the input 
            for i in range(len(volts)):
                if volts[i] > maxv/2:
                    break
            for k in reversed(range(len(volts))):
                if volts[k] > maxv/2:
                    break
            out_results.append([j, maxt, maxv, times[k] - times[i]])
            assert(maxt <= 20)

        return pd.DataFrame(out_results, columns=["comp id", "delay", "maxv", "width"]) 


    def simulate(self, max_per_region=10):
        """Simulate passive model based on neuron inputs and outputs.

        Args:
            
            max_per_region (int): 
                maxinum number of inputs per primary ROI to sample (0 means all)

        Returns:
            
            TimingResult (contains input/output delay matrix)
        """
      
    
        # only grab unique skel comp id rows and randomize data
        unique_io = self.io_pins.drop_duplicates(subset=["swcid"]).sample(frac=1).reset_index(drop=True)
        
        # grab top max_per region per input and all ouputs
        drive_list = []
        unique_outs = []

        # number of drives per input
        rcounter = {}
        for idx, row in unique_io.iterrows():
            if row["io"] == "out":
                unique_outs.append(row["swcid"])
            else:
                if row["roi"] not in rcounter:
                    rcounter[row["roi"]] = 0
                if max_per_region > 0 and rcounter[row["roi"]] == max_per_region:
                    continue
                rcounter[row["roi"]] += 1
                drive_list.append(row["swcid"])

        # simulate each drive (provide progress bar)
        delay_data = []
        amp_data = []
        for drive in tqdm(drive_list):
            # run simulation
            sim_results = self._runspice(drive, unique_outs)
            
            delay_data.append(sim_results["delay"].to_list())
            amp_data.append(sim_results["maxv"].to_list())

        delay_df = pd.DataFrame(delay_data, columns=unique_outs, index=drive_list) 
        amp_df = pd.DataFrame(amp_data, columns=unique_outs, index=drive_list) 

        # return simulation results
        return TimingResult(self.bodyid, delay_df, amp_df, self.io_pins, False) #self.neuron_conn_info, False)


    def estimate_intra_neuron_delay(self, num_points=100):
        """Simulate delay between random parts of a neuron.

        This function produces a delay matrix for a set of points
        determined by pre or post-synaptic sites.  The result
        is a square distance matrix which can be clustered to
        determine isopotential regions.  The points where current
        are injected do not represent real neural mechanisms
        and in practice random points could be chosen for simulation.
        Synapse location are chosen for convenience and to ensure
        proper weighting on 'important' parts of the neuron.

        Args:

            num_points(int):
                number of points to simulate.
        
        Returns:
            
            TimingResult (contains input/output delay matrix)
        """
        pass
        # TODO




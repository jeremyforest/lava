# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
# See: https://spdx.org/licenses/

from lava.magma.core.process.process import AbstractProcess
from lava.magma.core.process.variable import Var
from lava.magma.core.process.ports.ports import InPort, OutPort, RefPort


class Monitor(AbstractProcess):
    """
    Monitor process to probe/monitor a given variable of a process

    Monitor process is initialized without any Ports and Vars. The InPorts,
    RefPorts and Vars are created dynamically, as the Monitor process is
    used to probe OutPorts and Vars of other processes. For this purpose,
    Monitor process has probe(..) function, which as arguments takes the
    target Var or OutPorts and number of time steps we want to monitor given
    process.

    Attributes
    ----------
    data : dict
        Dictionary that is populated by monitoring data once get_data(..)
        method is called, has the following structure:
        data
          __monitored_process_name
             __monitored_var_or_out_port_name

    proc_params: dict
        Process parameters that will be transferred to the corresponding
        ProcessModel. It is populated with the names of dynamically
        created port and var names of Monitor process, to be carried to its
        ProcessModel. It is a dictionary of the following structure:
          "RefPorts": names of RefPorts created to monitor target Vars
          "VarsData1": names of Vars created to store data from target Vars
          "InPorts": names of InPorts created to monitor target OutPorts
          "VarsData2": names of Vars created to store data from target OutPorts
          "n_ref_ports": number of created RefPorts, also monitored Vars
          "n_in_ports": number of created InPorts, also monitored OutPorts

    target_names: dict
        The names of the targeted Processes and Vars/OutPorts to be monitored.
        This is used in get_data(..) method to access the target names
        corresponding to data-storing Vars of Monitor process during readout
        phase. This dict has the follwoing sturcture:
            key: name of the data-storing Vars, i.e. VarsData1 and VarsData2
            value: [monitored_process_name, monitored_var_or_out_port_name]

    Methods
    -------
    post_init()
        Create one prototypical RefPort, InPort and two Vars. This ensure
        coherence and one-to-one correspondence between Monitor process and
        ProcessModel in terms LavaPyTypes and Ports/Vars. These prototypical
        ports can later be updated inside probe(..) method.

    probe(target, num_steps)
        Probe the given target for num_step time steps, where target can be
        a Var or OutPort of some process.

    get_data()
        Fetch the monitoring data from the Vars of Monitor process that
        collected it during the run from probed process, puts into dict form
        for easier access by user
    """

    def __init__(self, **kwargs):
        """
        Initializes the attributes and run post().
        """
        super().__init__(**kwargs)

        self.data = {}

        self.proc_params["RefPorts"] = []
        self.proc_params["VarsData1"] = []
        self.proc_params["InPorts"] = []
        self.proc_params["VarsData2"] = []
        self.proc_params["n_ref_ports"] = 0
        self.proc_params["n_in_ports"] = 0

        self.target_names = {}

        self.post_init()

    def post_init(self):
        """
        Create one prototypical RefPort, InPort and two Vars. This ensure
        coherence and one-to-one correspondence between Monitor process and
        ProcessModel in terms LavaPyTypes and Ports/Vars. These prototypical
        ports can later be updated inside probe(..) method.
        Note: This is separated from constructor, because once
        multi-variable monitoring is enabled, this method will be deprecated.
        """

        # Create names for prototypical Ports/Vars to be created in Monitor
        # process for probing purposes.
        self.new_ref_port_name = "ref_port_" + \
                                 str(self.proc_params["n_ref_ports"])
        self.new_var_read_name = "var_read_" + \
                                 str(self.proc_params["n_ref_ports"])
        self.new_in_port_name = "in_port_" + \
                                str(self.proc_params["n_in_ports"])
        self.new_out_read_name = "out_read_" + \
                                 str(self.proc_params["n_in_ports"])

        # Create and set new Refport and corresponding Var to store data
        setattr(self, self.new_ref_port_name, RefPort(shape=(1,)))
        setattr(self, self.new_var_read_name, Var(shape=(1,), init=0))

        # Create and set new InPort and corresponding Var to store data
        setattr(self, self.new_in_port_name, InPort(shape=(1,)))
        setattr(self, self.new_out_read_name, Var(shape=(1,), init=0))

        # Register new created Vars/Ports
        attrs = self._find_attr_by_type(RefPort)
        self._init_proc_member_obj(attrs)
        self.ref_ports.add_members(attrs)

        attrs = self._find_attr_by_type(Var)
        self._init_proc_member_obj(attrs)
        self.vars.add_members(attrs)

        attrs = self._find_attr_by_type(InPort)
        self._init_proc_member_obj(attrs)
        self.in_ports.add_members(attrs)

    def probe(self, target, num_steps):
        """
        Probe the given target for num_step time steps, where target can be
        a Var or OutPort of some process.

        Parameters
        ----------
        target : Var or OutPort
            a Var or OutPort of some process to be monitored.
        num_steps: int
            The number of steps the target Var/OutPort should be monitored.
        """

        # Create names for Ports/Vars to be created in Monitor process for
        # probing purposes. Names are given incrementally each time probe(..)
        # method is called.
        self.new_ref_port_name = "ref_port_" + \
                                 str(self.proc_params["n_ref_ports"])
        self.new_var_read_name = "var_read_" + \
                                 str(self.proc_params["n_ref_ports"])
        self.new_in_port_name = "in_port_" + \
                                str(self.proc_params["n_in_ports"])
        self.new_out_read_name = "out_read_" + \
                                 str(self.proc_params["n_in_ports"])

        # Create and set new Refport and corresponding Var to store data
        setattr(self, self.new_ref_port_name, RefPort(shape=target.shape))
        setattr(self, self.new_var_read_name, Var(shape=(target.shape[0],
                                                         num_steps), init=0))

        # Create and set new InPort and corresponding Var to store data
        setattr(self, self.new_in_port_name, InPort(shape=target.shape))
        setattr(self, self.new_out_read_name, Var(shape=(target.shape[0],
                                                         num_steps), init=0))

        # Add the names of new RefPort and Var_read name to proc_params dict
        self.proc_params["RefPorts"].append(self.new_ref_port_name)
        self.proc_params["VarsData1"].append(self.new_var_read_name)

        # Add the names of new RefPort and Var_read name to proc_params dict
        self.proc_params["InPorts"].append(self.new_in_port_name)
        self.proc_params["VarsData2"].append(self.new_out_read_name)

        # Register new created Vars/Ports
        attrs = self._find_attr_by_type(RefPort)
        self._init_proc_member_obj(attrs)
        self.ref_ports.add_members(attrs)

        attrs = self._find_attr_by_type(Var)
        self._init_proc_member_obj(attrs)
        self.vars.add_members(attrs)

        attrs = self._find_attr_by_type(InPort)
        self._init_proc_member_obj(attrs)
        self.in_ports.add_members(attrs)

        # If target to be monitored is a Var
        if isinstance(target, Var):

            # Update id for the next use of probe(..) method
            self.proc_params["n_ref_ports"] += 1

            # Connect newly created Refport to the var to be monitored
            getattr(self, self.new_ref_port_name).connect_var(target)

            # Add the name of probed Var and its process to the target_names
            self.target_names[self.new_var_read_name] = [target.process.name,
                                                         target.name]
        # If target to be monitored is an OutPort
        elif isinstance(target, OutPort):

            # Update id for the next use of probe(..) method
            self.proc_params["n_in_ports"] += 1

            # Connect newly created InPort from the OutPort to be monitored
            getattr(self, self.new_in_port_name).connect_from(target)

            # Add the name of probed OutPort and its process to the target_names
            self.target_names[self.new_out_read_name] = [target.process.name,
                                                         target.name]

        # If target is an InPort raise a Type error, as monitoring InPorts is
        # not supported yet
        else:
            raise TypeError("Non-supported probe target: type {}"
                            .format(target))

        # Create corresponding dict keys for monitored Var/OutPort and its
        # process
        self.data[str(target.process.name)] = {}
        self.data[str(target.process.name)][str(target.name)] = 0

        return

    def get_data(self):
        """
        Fetch the monitoring data from the Vars of Monitor process that
        collected it during the run from probed process, puts into dict form
        for easier access by user.

        Returns
        -------
        data : dict
            Data dictionary collected by Monitor Process
        """

        # Fetch data-storing Vars for OutPort monitoring
        for i in range(self.proc_params["n_in_ports"]):
            data_var_name = self.proc_params["VarsData2"][i]
            data_var = getattr(self, data_var_name)
            target_name = self.target_names[data_var_name]

            self.data[target_name[0]][target_name[1]] = data_var.get()

        # Fetch data-storing Vars for Var monitoring
        for i in range(self.proc_params["n_ref_ports"]):
            data_var_name = self.proc_params["VarsData1"][i]
            data_var = getattr(self, data_var_name)
            target_name = self.target_names[data_var_name]

            self.data[target_name[0]][target_name[1]] = data_var.get()

        return self.data

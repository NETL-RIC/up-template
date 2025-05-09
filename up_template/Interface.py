#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Interface.py
#
##############################################################################
# REQUIRED MODULES
##############################################################################
# Standard libraries
import glob
import logging
import os
import re
import sys

# Third-party packages (install from GitHub)
from netlolca import NetlOlca

# User libraries (defined here)
from up_template.NetlOlcaReport import NetlOlcaReport
from up_template.NetlOlcaReport import CALC_DIR
from up_template.NetlOlcaReport import DATA_DIR
from up_template.NetlOlcaReport import OUTPUT_DIR


##############################################################################
# MODULE DOCUMENTATION
##############################################################################
__doc__ = """This module contains the class and function definitions for
running the menu-driven interface for the Jupyter Notebook unit process
template.

Last edited:
    2024-11-01
"""
__all__ = [
    "Interface",
    "dir_has_json",
    "find_excel_files",
    "find_json_files",
    "print_messages",
    "get_logger",
]


##############################################################################
# CLASSES
##############################################################################
class Interface(object):
    """A menu-driven interface class for the Jupyter Notebook unit process
    template.

    Attributes
    ----------
    _hidden_state : int
        For tracking the state-based machine. 0 = good; -1 = bad
    calc_dir : str
        The folder where calculation workbooks are saved.
    h_pattern : re.Pattern
        For regular expression matching user's help request.
    is_okay : bool
        Tracks the "okay" state of the Interface class.
    is_running : bool
        Tracks the "running" state of the Interface class.
    logger : logging.Logger
        A class logger.
    output_dir : str
        The folder path to where reports are generated.
    params : dict
        The master dictionary of menu options.
    process_code : str
        The Basic Process code (or user's option).
    process_types : dict
        A dictionary of processes types and their two-character abbreviations.
    product_sys_uid : str
        The universally unique identifier of the  user's selected unit process.
    rd : NetlOlcaReport
        An instance of NetlOlcaReport class (handles report generation).
    work_dir : str
        The directory path to the data folder for JSON-LD and YAML files.
    work_file : str
        The file path to the user's selected JSON-LD file.

    Examples
    --------
    >>> mc = Interface()
    >>> mc.run()
    ---------------------------
    MAIN MENU: Select an option
    ---------------------------
     1 ..... connect to JSON-LD
     2 ..... connect to openLCA
     q ..... quit
    (h for help) > 1
    ---------------------------------
    CONNECTION MENU: Select an option
    ---------------------------------
    1a ..... change data directory (default "data")
    1b ..... select JSON-LD file from data directory
     m ..... main menu
     q ..... quit
    (h for help) > 1b
    -------------------
    Select project file
    -------------------
    1 ... alkaline_electrolysis.zip
    2 ... aluminum_single_system.zip
    choose file > 2
    You entered '2', is this correct (y/n)? y
    ----------------------------
    Select product system for UP
    ----------------------------
    Product system (1 entries):
     1 ... Aluminum, production mix, shape casted
    choose product system > 1
    You entered '1', is this correct (y/n)? y
    Data fetched successfully.
    Success!
    (h for help) > q
    Exiting...
    """
    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # Class Initialization
    # ////////////////////////////////////////////////////////////////////////
    def __init__(self):
        self.logger = logging.getLogger("Interface")
        self.is_okay = True
        self.is_running = False
        self._hidden_state = 0
        self.json_set = []
        self.calc_set = []
        self.calc_dir = CALC_DIR
        self.calc_file = ""
        self.work_dir = DATA_DIR
        self.work_file = ""
        self.output_dir = OUTPUT_DIR
        self.product_sys_uid = ""
        # New container w/ NetlOlca
        self.rd = NetlOlcaReport(NetlOlca())

        # Help string regular expression matching pattern
        self.h_pattern = re.compile("^h(elp)?\\(([a-z|0-9]{1,2})\\)")

        # Parameter options
        self.params = {
            '1': {
                'name': 'CONNECT TO JSON-LD',
                'text': 'connect to JSON-LD',
                'type': 'option',
                'show': True,
                'func': self.connect_json,
                'dump': None,
                'help': ('Connect to a JSON-LD file in your data directory.')
                },
            '1a': {
                'name': 'SET DIRECTORY',
                'text': 'change data directory (default "%s")' % self.work_dir,
                'type': 'connection_json',
                'show': True,
                'func': self.assign_working_dir,
                'dump': self.get_working_dir,
                'help': ('Type the path to the folder on you computer where your '
                         'openLCA JSON-LD zip files are located.')},
            '1b': {
                'name': 'OPEN JSON-LD FILE',
                'text': 'select JSON-LD file from data directory',
                'type': 'connection_json',
                'show': True,
                'func': self.assign_project_file,
                'dump': self.get_project_file,
                'help': 'Connect to an openLCA project using a JSON-LD zip file.'},
            '2': {
                'name': 'CONNECT TO OPENLCA',
                'text': 'connect to openLCA',
                'type': 'option',
                'show': True,
                'func': self.connect_olca,
                'dump': None,
                'help': ('Connect to an openLCA database (e.g., using IPC service)')
                },
            '2a': {
                'name': 'SET IPC SERVER PORT',
                'text': 'define the server port number',
                'type': 'connection_olca',
                'show': True,
                'func': self.assign_server_port,
                'dump': self.get_server_port,
                'help': 'Set port number for openLCA IPC/GDT server.'},
            '2b': {
                'name': 'OPEN IPC SERVER',
                'text': 'connect to openLCA server',
                'type': 'connection_olca',
                'show': True,
                'func': self.open_server,
                'dump': None,
                'help': 'Connect to an openLCA project using IPC server.'},
            '3': {
                'name': 'REVIEW DATA',
                'text': 'review data',
                'type': 'option',
                'show': False,      # toggle after connect
                'func': self.query,
                'dump': None,
                'help': 'Open the review data menu.'},
            '3a': {
                'name': 'DESCRIPTION',
                'text': 'review process description',
                'type': 'query',
                'show': True,
                'func': self.query_description,
                'dump': None,
                'help': 'Show the unit process description.'},
            '3b': {
                'name': 'DOCUMENTATION',
                'text': 'review process documentation',
                'type': 'query',
                'show': True,
                'func': self.query_documentation,
                'dump': None,
                'help': 'Show the unit process documentation.'},
            '3c': {
                'name': 'CATEGORY',
                'text': 'review process category',
                'type': 'query',
                'show': True,
                'func': self.query_category,
                'dump': None,
                'help': 'Show the unit process category.'},
            '3d': {
                'name': 'FLOW',
                'text': 'review process flows',
                'type': 'query',
                'show': True,
                'func': self.query_flows,
                'dump': None,
                'help': 'Show the unit process input/output flows.'},
            '4':{
                'name': 'GENERATE REPORT',
                'text': 'generate report',
                'type': 'option',
                'show': False,       # Toggle after connect
                'func': self.handle_report_generation,
                'dump': None,
                'help': 'Generate a detailed report of the current process.'},
            '4a':{
                'name': 'DISPLAY REPORT',
                'text': 'Display a draft of the report template',
                'type': 'report',
                'show': True,
                'func': self.print_report,
                'dump': None,
                'help': 'Show the generated report on screen.'},
            '4b':{
                'name': 'WRITE REPORT',
                'text': 'Write report template to file',
                'type': 'report',
                'show': True,
                'func': self.save_report,
                'dump': None,
                'help': ('Writes the report as a plain text file in markdown '
                         'format')},
            '4c':{
                'name': 'READ REPORT',
                'text': 'Read report template from file',
                'type': 'report',
                'show': True,
                'func': self.read_report,
                'dump': None,
                'help': ('Read existing plain text report')},
            '5':{
                'name': 'PUBLISH REPORT',
                'text': 'publish report',
                'type': 'option',
                'show': False,       # Toggle after connect
                'func': self.handle_report_publication,
                'dump': None,
                'help': ('Publish report to a file format (e.g., .docx, '
                         '.pdf, or .html).')},
            '5a':{
                'name': 'TO PDF',
                'text': 'publish report as .pdf',
                'type': 'publish',
                'show': True,
                'func': self.rd.convert_to_pdf,
                'dump': None,
                'help': ('Convert the markdown report to published document '
                         'format.')},
            '5b':{
                'name': 'TO WORD',
                'text': 'publish report as .docx',
                'type': 'publish',
                'show': True,
                'func': self.rd.convert_to_word,
                'dump': None,
                'help': ('Convert the markdown report to Microsoft Word '
                         'format.')},
            '5c':{
                'name': 'TO HTML',
                'text': 'publish report as .html',
                'type': 'publish',
                'show': True,
                'func': self.rd.convert_to_html,
                'dump': None,
                'help': ('Convert the markdown report to hypertext markup '
                         'language format.')},
            '6':{
                'name': 'PROCESS TYPE',
                'text': 'choose process type',
                'type': 'option',
                'show': False,
                'func': self.add_process_type,
                'dump': None,
                'help': ('Select the proper process type (e.g., .EP, MP, BP, '
                        'IP, EC, TP, RP).')},
            '7':{
                'name': 'CALCULATION WORKBOOK',
                'text': 'choose calculation workbook',
                'type': 'option',
                'show': False,
                'func': self.assign_calculation_file,
                'dump': None,
                'help': (
                    'Select an auxillary Excel workbook with supplemental '
                    'calculations to add to your report.')},
            'q': {
                'name': 'QUIT',
                'text': 'quit',
                'type': 'option',
                'show': False,
                'func': self.quit,
                'dump': None,
                'help': 'Use this command any time to exit the program.'},
            'h': {
                'name': 'HELP',
                'text': '',
                'type': 'option',
                'show': False,
                'func': None,
                'dump': None,
                'help': 'Displays the help message for a given option.'},
            'm':{
                'name': 'MAIN MENU',
                'text': 'main menu',
                'type': 'option',
                'show': False,
                'func': self.show_options,
                'dump': None,
                'help': ('Open the main menu.')},
            'o':{
                'name': 'OTHER OPTIONS',
                'text': 'other options',
                'type': 'option',
                'show': False,       # Toggle after connect
                'func': self.show_misc,
                'dump': None,
                'help': ('Open the other options menu (e.g., for editing and '
                         'changing product systems).')},
            'e': {
                'name': 'EDIT PROCESS',
                'text': 'edit process',
                'type': 'misc',
                'show': True,
                'func': self.edit,
                'dump': None,
                'help': 'Open edit menu. Only available for JSON-LD.'},
            'e1': {
                'name': 'ADD ACTOR',
                'text': 'add new person or organization',
                'type': 'edit',
                'show': True,
                'func': self.add_actor,
                'dump': None,
                'help': 'Add actor to openLCA project.'},
            'e2': {
                'name': 'EDIT REVIEWER',
                'text': 'edit reviewer',
                'type': 'edit',
                'show': True,
                'func': self.edit_reviewer,
                'dump': None,
                'help': 'Edit reviewer name in the process documentation.'},
            'p': {
                'name': 'CHANGE UNIT PROCESS',
                'text': 'select product system',
                'type': 'misc',
                'show': True,
                'func': self.assign_product_system,
                'dump': None,
                'help': ('Select the product system that represents the unit '
                         'process to review and report.')},
        }

    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # Class Property Definitions
    # ////////////////////////////////////////////////////////////////////////
    @property
    def netl(self):
        """A shortcut property to NetlOlcaReport class's NetlOlca instance."""
        return self.rd.netlolca

    @property
    def num_files(self):
        """Count of JSON-LD files found in working directory.

        Returns
        -------
        int
        """
        return len(self.json_set)

    @property
    def num_workbooks(self):
        """Number of Excel workbooks found in calculations directory."""
        return len(self.calc_set)

    @property
    def process_code(self):
        """Reference process type code as defined in the old DS/DF files.

        Parameters
        ----------
        str
            A two-letter parameter code.

        Returns
        -------
        str
        """
        return self.rd.process_code

    @process_code.setter
    def process_code(self, val):
        # Error handling provided in func:`set_process_type`
        self.rd.process_code = val

    @property
    def process_types(self):
        """The list of process type codes to choose from.

        The list if based on the drop-down options in the old DS file.

        Returns
        -------
        list
        """
        return self.rd.process_types

    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # Class Function Definitions
    # ////////////////////////////////////////////////////////////////////////
    def add_actor(self):
        """Request and assign new Actor to openLCA project.
        """
        self.request("Select actor")
        is_done = False
        while not is_done:
            is_done = self.prompt_new_actor()

    def add_process_type(self, val=None):
        """Request and assign the process type code.

        Parameters
        ----------
        val : str, optional
            Two-character process type code, by default None

        Returns
        -------
        bool
            Whether the assignment completed successfully or NoneType.
        """
        if val is not None:
            return self.set_process_type(val)

        self.request("Select process type")
        is_done = False
        while not is_done:
            is_done = self.prompt_process_type()
        self.show_options()

    def add_to_project(self, o_class):
        """Add a root entity to openLCA project.

        Parameters
        ----------
        o_class : olca_schema.*
            A root entity object with a UUID.

        Returns
        -------
        bool
            True for success.
        """
        return self.netl.add(o_class, self.netl.out_file)

    def assign_product_system(self, val=None):
        """Request and assign product system UUID.

        This UUID is the basis for the unit process that is being developed.
        See instructions in the Jupyter Notebook template for more details.

        Parameters
        ----------
        val : str, optional
            Product system UUID, by default None

        Returns
        -------
        bool/NoneType
            Bool is returned when a value is given (success of assignment);
            otherwise, a series of prompts lead to assigning the product
            system UUID.
        """
        if val is not None:
            return self.set_product_system(val)
        else:
            self.request("Select product system for UP")
            is_done = False
            while not is_done:
                is_done = self.prompt_product_system()

    def assign_calculation_file(self, val=None):
        """Request and/or assign the calculation workbook file path."""
        if val is not None:
            return self.set_calc_file(val)
        else:
            self.request("Select calculation workbook")
            is_done = False
            while not is_done:
                is_done = self.prompt_calculation_file()
            self.show_options()

    def assign_project_file(self, val=None):
        """Request and assign a JSON-LD project file.

        The sequence of methods that carry out the opening of a project file
        includes the following.

        1.  `assign_project_file`, runs `prompt_project_file` until done.
        2.  `prompt_project_file`, reads working directory for JSON-LD files
            and prompts user to make a selection; if selection is correct,
            sends user selection to `set_project_file`. Successful
            assignment triggers `assign_product_system`.
        3.  `set_project_file`, attempts to assign user selection to this
            class's attribute via `open_file`.
        4.  `open_file`, calls NetlOlca member's open and read methods for
            given JSON-LD file.

        Parameters
        ----------
        val : str, optional
            File path to JSON-LD, by default None

        Returns
        -------
        bool/NoneType
            Bool is returned when a value is given (success of assignment);
            otherwise, a series of prompts lead to assigning the project file.
        """
        if val is not None:
            return self.open_file(val)
        else:
            self.request("Select project file")
            is_done = False
            while not is_done:
                is_done = self.prompt_project_file()
            self.make_param_visible('1', False)
            self.make_param_visible('2', False)
            self.make_param_visible('3', True)
            self.make_param_visible('4', True)
            self.make_param_visible('5', True)
            self.make_param_visible('6', True)
            self.make_param_visible('7', True)
            self.make_param_visible('o', True)
            self.show_options()

    def assign_server_port(self, val=None):
        """Request and assign IPC server port number for openLCA.

        Parameters
        ----------
        val : int, optional
            Port number, by default None

        Returns
        -------
        bool/NoneType
            Bool is returned when a value is given (success of assignment);
            otherwise, a series of prompts lead to assigning the port number.
        """
        if val is not None:
            return self.set_server_port(val)
        else:
            self.request("Enter port number for IPC server")
            is_done = False
            while not is_done:
                is_done = self.prompt_server_port()

    def assign_working_dir(self, val=None):
        """Request and assign the working directory.

        Parameters
        ----------
        val : str, optional
            The folder path to a working directory.

        Returns
        -------
        bool/NoneType
            Bool is returned when a value is given (success of assignment);
            otherwise, a series of prompts lead to assigning
            a working directory.
        """
        if val is not None:
            return self.set_working_dir(val)
        else:
            self.request("Enter the directory with project files")
            is_done = False
            while not is_done:
                is_done = self.prompt_working_dir()

    def check_ans(self, val):
        """Request a confirmation on user input.

        Parameters
        ----------
        val : str
            The user's answer to a prompt.

        Returns
        -------
        bool
            The user's confirmation of their answer.
        """
        prompt = "You entered '%s', is this correct (y/n)? " % (val)
        ans = input(prompt)
        if ans.lower() == 'y' or ans.lower() == 'yes':
            return True
        else:
            return False

    def check_val(self, val):
        """Check user answer for the quit and skip options.

        An empty string assumes no setting.

        Parameters
        ----------
        val : str
            User response

        Returns
        --------
        bool
            Whether quit or skip option was entered.
        """
        if val.lower() == 'q' or val.lower() == 'quit':
            is_done = True
            self.quit()
        elif val.isspace() or val == '':
            # Skip parameter setting
            is_done = True
        else:
            is_done = False

        return is_done

    def connect_json(self):
        """Display JSON-LD connection menu.
        """
        # Read working directory for JSON-LD files
        _ = self.set_working_dir(self.work_dir)

        self.request("CONNECTION MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'connection_json' and to_show:
                self.print_menu_option(arg)
        self.print_menu_option('m')
        self.print_menu_option('q')

    def connect_olca(self):
        """Display openLCA connection menu.
        """
        self.request("CONNECTION MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'connection_olca' and to_show:
                self.print_menu_option(arg)
        self.print_menu_option('m')
        self.print_menu_option('q')

    def do_next(self):
        """Check user response for next processing step."""

        ans = input("(h for help) > ")

        # Catch non-argument quit keywords:
        if ans.lower() in ['exit', 'quit']:
            self.quit()
        elif ans.lower().startswith('h'):
            self.help(ans)
        elif ans.lower() in self.params:
            # Execute the corresponding function from the params dictionary
            self.params[ans]['func']()
        else:
            print("Invalid option.")
            self.show_options()  # Show options again for invalid input

    def edit(self):
        """Display edit menu.
        """
        self.request("EDIT MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'edit' and to_show:
                self.print_menu_option(arg)
        self.print_menu_option('m')
        self.print_menu_option('q')

    def edit_reviewer(self, val=None):
        """Edit reference process reviewer in the process documentation.

        Parameters
        ----------
        val : str, optional
            An actor universally unique ID, by default None

        Returns
        -------
        bool/NoneType
            If val is not None, returns bool to show success; otherwise,
            prompts user to select reviewer and returns nothing.
        """
        if val is not None:
            return self.set_reviewer(val)
        else:
            self.request("Select reviewer")
            is_done = False
            while not is_done:
                is_done = self.prompt_reviewer()

    def get_project_file(self, key):
        """Return command line argument and value for project file.

        Parameters
        ----------
        key : str
            Parameter key.

        Returns
        -------
        str
            A formatted key-value pair.
        """
        line = "-{} {}".format(key, self.work_file)
        return line

    def get_server_port(self, key):
        """Return command line argument for server port number.

        Parameters
        ----------
        key : str
            Parameter key.

        Returns
        -------
        str
            A formatted key-value pair.
        """
        line = "-{} {}".format(key, self.netl.port)
        return line

    def get_working_dir(self, key):
        """Return the command line argument for the current working directory

        Parameters
        ----------
        key : str
            Parameter key.

        Returns
        -------
        str
            A formatted key-value pair.
        """
        line = "-{} {}".format(key, self.work_dir)
        return line

    def handle_report_generation(self):
        """Display report menu."""
        self.request("REPORT MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'report' and to_show:
                self.print_menu_option(arg)
        self.print_menu_option('m')
        self.print_menu_option('q')

    def handle_report_publication(self):
        """Display publication menu.

        If pandoc app is not found, these options will be hidden.
        """
        # Check if pandoc is installed
        pandoc_required = False
        if not self.rd.pandoc_installed():
            print(
                "Pandoc is not installed. "
                "Reports in PDF, Word, or HTML format cannot be generated.")
            user_decision = input(
                "Would you like to continue anyway? (y/n): ").strip().lower()
            # Exit the method if the user decides not to continue
            if user_decision.lower() != 'y':
                self.logger.info(
                    "Okay. "
                    "You can still view the report from the menu options.")
                return
            pandoc_required = True

        self.request("PUBLISHING MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'publish' and to_show and not pandoc_required:
                self.print_menu_option(arg)
        self.print_menu_option('m')
        self.print_menu_option('q')

    def help(self, h_str):
        """Check the help request based on the prescribed string pattern.

        Parameters
        ----------
        h_str : str
            Help request string.
        """
        # Match the help string against the defined pattern:
        m = self.h_pattern.match(h_str)

        if m is None and h_str.lower().startswith("help"):
            print("Usage: help(<option>)")
        elif m is None and h_str.lower().startswith("h"):
            print("Usage: h(<option>)")
        elif m is not None:
            self.show_help(m.groups()[1])
        else:
            self.show_options()

    def load_excel_set(self, my_dir):
        """Read all Excel workbooks found in a given directory.

        The file paths to each are stored in the ``calc_set`` attribute.
        """
        if os.path.isdir(my_dir):
            self.calc_set = find_excel_files(my_dir)

        # Set okay flag to False for empty directories:
        if self.num_files > 0:
            self.is_okay = True
        else:
            self.is_okay = False
            self.warn("No Excel files found")

    def load_json_set(self, my_dir):
        """Read a directory for JSON-LD files.

        Parameters
        ----------
        my_dir : str
            Directory path.
        """
        if os.path.isdir(my_dir):
            self.json_set = find_json_files(my_dir)

        # Set okay flag to False for empty directories:
        if self.num_files > 0:
            self.is_okay = True
        else:
            self.is_okay = False
            self.warn("No JSON-LD files")

    def make_param_visible(self, p, v):
        """Turn menu option visibility on/off.

        Parameters
        ----------
        p : str
            A valid menu option (e.g., 'r1')
        v : bool
            Whether visible.

        Raises
        ------
        ValueError
            For invalid menu options.
        TypeError
            For invalid boolean parameter.
        """
        if p not in self.params.keys():
            raise ValueError("Parameter, '%s', not found!" % p)
        if not isinstance(v, bool):
            raise TypeError("Expected true/false, received '%s'" % v)

        self.params[p]['show'] = v

    def open_file(self, val):
        """Open zipio.ZipReader connection with a JSON-LD file and read the
        project and save initial report values.
        """
        self.logger.info("Opening file '%s'" % val)
        self.netl.open(val)
        self.netl.read()

    def open_server(self):
        """Open IPC server connection to openLCA using the configured port
        number and reads the project data.

        Warns when connection fails and saves initial report values.
        """
        self.logger.info("Opening IPC server connection")
        self.netl.connect()
        try:
            self.netl.read()
        except Exception:
            # There are a ton of errors associated with bad connection
            # (e.g., MaxRetryError, ConnectionError, NewConnectionError,
            # ConnectionRefusedError), so grab them all!
            self.warn(
                "Failed to connect to IPC server on port %d" % self.netl.port)
        else:
            self.assign_product_system()
            self.make_param_visible('1', False)
            self.make_param_visible('2', False)
            self.make_param_visible('3', True)
            self.make_param_visible('4', True)
            self.make_param_visible('5', True)
            self.make_param_visible('6', True)
            self.make_param_visible('7', True)
            self.make_param_visible('o', True)
            self.show_options()

    def print_menu_option(self, opt):
        """Print menu option line.

        Parameters
        ----------
        opt : str
            The option (e.g., 'm' for main menu option).

        Notes
        -----
        Thanks to the Internet for how to manage padding and alignment for
        format strings. See #the-fill-and-align-subcomponents here:
        https://realpython.com/python-formatted-output/
        """
        if opt in self.params.keys():
            line = "{0:>2s} ..... {1}".format(opt, self.params[opt]['text'])
            print(line)
        else:
            logging.error("Option, %s, not found!" % opt)

    def print_report(self):
        """Print markdown version of report.
        """
        if self.rd.md is None:
            print("Please read or write report to file first.")
        else:
            print(self.rd.md)

    def prompt_calculation_file(self):
        """Request user selection of Excel workbooks found in the
        calculations directory."""
        self.logger.debug("Re-reading working directory for new files.")
        self.load_excel_set(self.calc_dir)
        my_str = ""
        for i in range(self.num_workbooks):
            p_file = os.path.basename(self.calc_set[i])
            my_str += "%d ... %s\n" % (i+1,  p_file)
        my_str += "choose file > "
        ans = input(my_str)
        is_done = self.check_val(ans)

        try:
            int(ans)
        except:
            self.warn("Select from 1 to %d" % self.num_workbooks)
        else:
            ans = int(ans)
            if ans < 1 or ans > self.num_workbooks:
                self.warn("Choose number from 1 to %d" % self.num_workbooks)
            elif self.check_ans(ans):
                p_idx = ans - 1
                p_file = self.calc_set[p_idx]
                is_done = self.set_calc_file(p_file)
                if not is_done:
                    self.warn("Calculation file not set!")
        return is_done

    def prompt_new_actor(self):
        """Prompt user for an actor from the YAML file and add it to project.

        Returns
        -------
        bool
            True for successful prompt and assignment or if user enters
            the quit signal or empty entry.
        """
        # Read user input from YAML
        a_name = self.netl.get_actor_yaml(self.work_dir)
        a_list = self.netl.get_yaml_entities(fpath=a_name)
        num_names = len(a_list)

        # Print actor names, get user selection and check for exit sequence
        my_str = ""
        for i in range(num_names):
            my_str += "%d. %s, %s\n" % (i+1, a_list[i].name, a_list[i].address)
        my_str += "select > "
        ans = input(my_str)
        is_done = self.check_val(ans)

        # Process user response, and attempt to add new actor to project
        if not is_done:
            try:
                int(ans)
            except:
                self.warn("Selection should be an integer.")
            else:
                ans = int(ans)
                if ans < 1 or ans > num_names:
                    self.warn("Choose a number from 1 to %d" % num_names)
                elif self.check_ans(ans):
                    r_idx = ans - 1
                    a = a_list[r_idx]
                    is_done = self.add_to_project(a)
                    if not is_done:
                        self.warn("Failed to set new actor")
                    else:
                        self.success()
        return is_done

    def prompt_process_type(self):
        """Prompt user to select process type code.

        Returns
        -------
        bool
            Whether selection was successful.

        Notes
        -----
        Consider adding help text for each of these options via Interface's
        menu (e.g., h(EP) would tell what is extraction process).
        """
        self.logger.debug("Prompting user for process type.")
        for k, v in self.process_types.items():
            print("%s ... %s" % (k, v))
        q = "choose process type (%s) > " % self.process_code
        ans = input(q)
        is_done = self.check_val(ans)

        if not is_done:
            is_done = self.set_process_type(ans)
            if not is_done:
                self.warn("Selection should be a two-letter option.")

        return is_done

    def prompt_product_system(self):
        """Prompt user for product system selection.

        Note this serves as the unit process that the report is based on.

        Returns
        -------
        bool
            True for successful prompt and assignment or if user enters
            the quit signal or empty entry.
        """
        # Check to see how many product systems there are in the dataset.
        num_ps = self.netl.get_number_product_systems()

        # Short-circuit the selection when there is only one to choose.
        if num_ps == 1:
            ans = 1
            is_done = False
        else:
            self.netl.print_project("Product system")
            q = "choose product system > "
            ans = input(q)
            is_done = self.check_val(ans)

        if not is_done:
            try:
                int(ans)
            except:
                self.warn("Selection should be an integer.")
            else:
                ans = int(ans)
                if ans < 1 or ans > num_ps:
                    self.warn("Choose number from 1 to %d" % num_ps)
                elif num_ps == 1 and ans == 1:
                    # Skip the line.
                    ps_idx = ans - 1
                    ps_uid = self.netl.get_spec_ids(
                        self.netl.get_spec_class("Product system"))[ps_idx]
                    is_done = self.set_product_system(ps_uid)
                    if not is_done:
                        self.warn("Product system failed to set")
                    else:
                        self.success()
                elif self.check_ans(ans):
                    ps_idx = ans - 1
                    ps_uid = self.netl.get_spec_ids(
                        self.netl.get_spec_class("Product system"))[ps_idx]
                    is_done = self.set_product_system(ps_uid)
                    if not is_done:
                        self.warn("Product system failed to set")
                    else:
                        self.success()
        return is_done

    def prompt_project_file(self):
        """Prompt user for a JSON-LD project file and UP product system.

        Notes
        -----
        Reads the working directory again for new files (e.g., if a user
        moves files into the data directory while the interface is running).

        Returns
        -------
        bool
            True for successful prompt and assignment or if user enters
            the quit signal or empty entry.
        """
        self.logger.debug("Re-reading working directory for new files.")
        self.load_json_set(self.work_dir)
        my_str = ""
        for i in range(self.num_files):
            p_file = os.path.basename(self.json_set[i])
            my_str += "%d ... %s\n" % (i+1,  p_file)
        my_str += "choose file > "
        ans = input(my_str)
        is_done = self.check_val(ans)

        try:
            int(ans)
        except:
            self.warn("Select from 1 to %d" % self.num_files)
        else:
            ans = int(ans)
            if ans < 1 or ans > self.num_files:
                self.warn("Choose number from 1 to %d" % self.num_files)
            elif self.check_ans(ans):
                p_idx = ans - 1
                p_file = self.json_set[p_idx]
                is_done = self.set_project_file(p_file)
                if not is_done:
                    self.warn("Project file not set!")
                else:
                    self.assign_product_system()
        return is_done

    def prompt_reviewer(self):
        """Prompt user to define the reviewer for this project's unit process.

        Returns
        -------
        bool
            True for successful prompt and assignment or if user enters
            the quit signal or empty entry.
        """
        # Get current reviewer's name
        r_name, _ = self.netl.get_reviewer(uuid=self.product_sys_uid)

        # Print unique reviewer selection options
        a_dict = self.netl.get_actors(unique=True)
        name_list = a_dict.get("name", [])
        addr_list = a_dict.get("address", [])
        num_names = len(name_list)
        my_str = ""
        for i in range(num_names):
            my_str += "%d. %s, %s\n" % (i+1,  name_list[i], addr_list[i])
        my_str += "%d. %s\n" % (i+2, "Add new name to YAML.")
        my_str += "select reviewer (%s)> " % r_name

        # Get user's input and check for exit character
        ans = input(my_str)
        is_done = self.check_val(ans)
        if not is_done:
            try:
                int(ans)
            except:
                self.warn("Selection should be an integer.")
            else:
                ans = int(ans)
                if ans < 1 or ans > num_names+1:
                    self.warn("Choose number from 1 to %d" % num_names+1)
                elif self.check_ans(ans):
                    # User selected "Add new to YAML," send to add actor
                    if ans > num_names:
                        self.add_actor()
                    else:
                        r_idx = ans - 1
                        r_uid = a_dict['uuid'][r_idx]
                        is_done = self.set_reviewer(r_uid)
                        if not is_done:
                            self.warn("Failed to set reviewer")
                        else:
                            self.success()
        return is_done

    def prompt_server_port(self):
        """Prompt user for an IPC server port number.

        Returns
        -------
        bool
            True for successful prompt and assignment or if user enters
            the quit signal or empty entry.
        """
        prompt = "server port (%d)> " % self.netl.port
        ans = input(prompt)
        is_done = self.check_val(ans)
        if not is_done:
            if self.check_ans(ans):
                is_done = self.set_server_port(ans)
                if not is_done:
                    self.warn("Port number not set!")
                else:
                    self.success()
        return is_done

    def prompt_working_dir(self):
        """Prompt user for a working directory.

        Returns
        -------
        bool
            True for successful prompt and assignment or if user enters
            the quit signal or empty entry.
        """
        prompt = "working dir (%s)> " % self.work_dir
        ans = input(prompt)
        is_done = self.check_val(ans)
        if not is_done:
            if self.check_ans(ans):
                is_done = self.set_working_dir(ans)
                if not is_done and os.path.isdir(ans):
                    self.warn("No files found in directory")
                elif not is_done:
                    self.warn("Working directory must exist")
                else:
                    self.success()
        return is_done

    def query(self):
        """Display query menu.
        """
        self.request("REVIEW MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'query' and to_show:
                line = "{} ..... {}".format(arg, self.params[arg]['text'])
                print(line)
        line = "{}  ..... {}".format('q', self.params['q']['text'])
        print(line)

    def query_category(self):
        """Display the category for the unit process.
        """
        cat_str = "CATEGORY\n"
        if self.product_sys_uid == "":
            self.warn("Assuming the reference product system")
            cat_str += "%s" % self.netl.get_reference_category()
        else:
            cat_str += "%s" % self.netl.get_reference_category(
                self.product_sys_uid)
        print_messages([cat_str], 79, ">>")

    def query_description(self):
        """Display the description for the unit process.
        """
        cat_str = "DESCRIPTION:\n"
        if self.product_sys_uid == "":
            self.warn("Assuming the reference product system")
            cat_str += "%s" % self.netl.get_reference_description()
        else:
            cat_str += "%s" % self.netl.get_reference_description(
                self.product_sys_uid)
        print_messages([cat_str], 79, ">>")

    def query_documentation(self):
        """Display process documentation in YAML format.
        """
        my_str = "DOCUMENTATION:\n"
        if self.product_sys_uid == "":
            self.warn("Assuming the reference product system")
            d_str = self.netl.get_reference_doc()
        else:
            d_str = self.netl.get_reference_doc(uuid=self.product_sys_uid)
        d_str = my_str + d_str
        print_messages([d_str], 79, ">>")

    def query_flows(self):
        """Display lists of input and output flows and their amounts for
        the unit process.
        """
        # Title strings; run before print messages
        ip_str = "INPUT FLOWS:"
        op_str = "OUTPUT FLOWS:"

        # Manage the input/output flow dictionaries depending on process ID
        if self.product_sys_uid == "":
            self.warn("Assuming the reference product system")
            ip_dict = self.netl.get_input_flows()
            op_dict = self.netl.get_output_flows()
        else:
            ip_dict = self.netl.get_input_flows(uuid=self.product_sys_uid)
            op_dict = self.netl.get_output_flows(uuid=self.product_sys_uid)

        # Convert dictionaries into list of formatted strings
        # NOTE: length of value lists should be the same for inputs/outputs
        num_ip = len(ip_dict['name'])
        num_op = len(op_dict['name'])
        ip_list = [
            "%s %s %s" % (
                ip_dict['amount'][i],
                ip_dict['unit'][i],
                ip_dict['name'][i],
            ) for i in range(num_ip)
        ]
        op_list = [
            "%s %s %s" % (
                op_dict['amount'][i],
                op_dict['unit'][i],
                op_dict['name'][i],
            ) for i in range(num_op)
        ]
        print(ip_str)
        print_messages(ip_list, 79)
        print(op_str)
        print_messages(op_list, 79)

    def quit(self):
        """Terminate the run sequence.

        Note that connections remain live (e.g., file or server).
        """
        self.is_running = False
        self._hidden_state = -1
        print("Exiting...")

    def read_report(self):
        """Provide user's the option to read existing markdown file without
        generating a new version."""
        try:
            self.rd.read_report_markdown()
        except OSError:
            print(
                "Markdown report is not found! Try writing report first.")
        else:
            if self.rd.md is None:
                print("Markdown report is empty!")
            else:
                print("Markdown report read.")

    def request(self, msg):
        """Format print a request to user.
        """
        msg_len = len(msg)
        print("-"*msg_len)
        print(msg)
        print("-"*msg_len)

    def run(self):
        """Main run loop.
        """
        self.is_running = True
        if self._hidden_state == 0:
            if not os.path.isdir(self.work_dir):
                self.assign_working_dir()
            if self.is_running:
                self.show_options()
                while self.is_okay and self.is_running:
                    self.do_next()

    def save_report(self):
        """Fetch data from report class, read calculations, generate the
        markdown report, and write it to file.
        """
        try:
            # This generates the markdown content.
            # Make any value adjustments before this is called.
            self.logger.info("Fetching info")
            self.rd.fetch_data(self.product_sys_uid)

            # Read the filled workbook and extract the calculations
            calculations = self.rd.read_calc_wb(self.calc_file)

            # Set the calculations content in NetlOlcaReport
            if calculations:
                self.rd.calculations_content = calculations
            else:
                print("No calculations found or error in reading the workbook.")

            # Generate the report, including the Excel calculations
            self.rd.save_markdown()
        except Exception as e:
            # Exit if there's an error during the report generation process
            print(f"Error during report generation: {e}")
            return

    def set_calc_file(self, val):
        """Assign a file path to the user's calculation workbook."""
        is_done = False
        if os.path.isfile(val):
            self.calc_file = val
            is_done = True
        return is_done

    def set_process_type(self, val):
        """Assign the process code.

        Parameters
        ----------
        val : str
            A user's process code selection (e.g., 'BP').

        Returns
        -------
        bool
            Whether the user's selection is a valid process code.
        """
        is_done = False
        # Correct case sensitivity
        if isinstance(val, str):
            val = val.upper()

        # Check if valid option
        if val in self.process_types.keys():
            logging.info("Process code set to %s" % val)
            self.process_code = val
            is_done = True

        return is_done

    def set_product_system(self, val):
        """Define product system UUID to the class attribute and
        save the reference name for output file handling.

        Parameters
        ----------
        val : str
            Universally unique identity (UUID) string.

        Returns
        -------
        bool
            Whether assignment of new value was successful.
        """
        is_done = False
        id_list = self.netl.get_spec_ids(
            self.netl.get_spec_class("Product system"))
        if val in id_list:
            self.product_sys_uid = val
            self.rd.reference_name = self.rd.netlolca.get_reference_name(val)
            print("Product system set to '%s'" % self.rd.reference_name)
            is_done = True
        return is_done

    def set_project_file(self, val):
        """Define the working project file to the class attributes.

        Parameters
        ----------
        val : str
            A file path to an openLCA JSON-LD project file.

        Returns
        -------
        bool
            Whether assignment of new value was successful.
        """
        is_done = False
        if os.path.isfile(val):
            try:
                self.open_file(val)
            except:
                # May receive BadZipFile error
                pass
            else:
                self.work_file = val
                is_done = True
        return is_done

    def set_reviewer(self, val):
        """Edits an openLCA project with a new process that includes the
        reviewer attribute (within the process documentation) assigned to
        the Actor whose ID is provided.

        For IPC server connections, the edit is a simple put command.
        For JSON-LD zip files, the edit overwrites the process JSON.

        Parameters
        ----------
        val : str
            A universally unique identifier (UUID) for an existing actor
            within the openLCA project. To add a new actor, see
            :func:`add_actor`.

        Returns
        -------
        bool
            True for success.
        """
        # Query for Actor using UUID and reference process class
        a = self.netl.query(self.netl.get_spec_class('Actor'), val)
        p = self.netl.get_reference_process(
            uuid=self.product_sys_uid, as_ref=False)[0]

        is_success = False
        if p is not None:
            if a is not None:
                # Documentation states reviewers are Refs to Actors
                # https://greendelta.github.io/olca-schema/classes/Process.html
                p.process_documentation.reviewer = a.to_ref()
                is_success = self.add_to_project(p)
            else:
                self.warn("Failed to find actor ('%s')" % val)
        else:
            self.warn(
                "Failed to find reference process ('%s')" % (
                    self.product_sys_uid))
        return is_success

    def set_server_port(self, val):
        """Define the IPC server port to the NetlOlca class member.

        Parameters
        ----------
        val : int
            Port number (e.g., 8080).

        Returns
        -------
        bool
            Whether assignment of new value was successful.
        """
        is_done = False
        try:
            self.netl.port = val
        except (ValueError, TypeError) as e:
            is_done = False
        else:
            is_done = True
        return is_done

    def set_working_dir(self, val):
        """Define the working directory to the class attributes.

        Parameters
        ----------
        val : str
            The working directory path.

        Returns
        -------
        bool
            Whether assignment of new value was successful.
        """
        is_done = False
        if os.path.isdir(val) and dir_has_json(val):
            is_done = True
            self.load_json_set(val)
            self.work_dir = val
            print("Read %d files in working directory" % self.num_files)
        return is_done

    def show_help(self, h_opt):
        """Print help message for a given help option.

        Parameters
        ----------
        h_opt : str
            Help option.

        Returns
        -------
        None
        """
        if h_opt in self.params:
            msg_text = "{}: {}".format(self.params[h_opt]['name'],
                                       self.params[h_opt]['help'])
            msg = [msg_text, ]
        else:
            msg = [("ERROR: Option '%s' not recognized." % (h_opt)), ]

        print_messages(msg, 79, '>>')

    def show_misc(self):
        """Print miscellany options
        """
        self.request("MISCELLANY MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'misc' and to_show:
                self.print_menu_option(arg)
        self.print_menu_option('m')
        self.print_menu_option('q')

    def show_options(self):
        """Print user options
        """
        self.request("MAIN MENU: Select an option")
        for arg in sorted(list(self.params.keys())):
            param_type = self.params[arg]['type']
            to_show = self.params[arg]['show']
            if param_type == 'option' and to_show:
                self.print_menu_option(arg)
        self.print_menu_option('q')

    def success(self):
        """Print a success message.
        """
        print("Success!")

    def warn(self, msg):
        """Print a warning message to user.

        Parameters
        ----------
        msg : str
            Warning message.
        """
        print("!!! %s !!!" % msg)


##############################################################################
# FUNCTIONS
##############################################################################
def dir_has_json(my_dir):
    """Return whether a given directory contains JSON-LD files.

    Parameters
    ----------
    my_dir : str
        Directory path.

    Returns
    -------
    bool
        Whether the directory contains JSON-LD files.
    """
    my_list = find_json_files(my_dir)
    if len(my_list) > 0:
        return True
    else:
        return False


def find_excel_files(my_dir):
    """Return a sorted list of Excel files found in a given directory.

    Parameters
    ----------
    my_dir : str
        The directory path.

    Returns
    -------
    list
        A list of Excel file paths.
    """
    my_files = []
    for img_type in [".xls", ".xlsx"]:
        s_str = os.path.join(my_dir, "*%s" % (img_type))
        my_files += glob.glob(s_str)
    my_files = sorted(list(set(my_files)))

    return my_files


def find_json_files(my_dir):
    """Return a sorted list of JSON-LD files found in a given directory.

    Parameters
    ----------
    my_dir : str
        The directory path.

    Returns
    -------
    list
        A list of JSON-LD paths.
    """
    my_files = []
    for img_type in [".zip", ".json"]:
        s_str = os.path.join(my_dir, "*%s" % (img_type))
        my_files += glob.glob(s_str)
    my_files = sorted(list(set(my_files)))

    return my_files


def print_messages(msg_list, char_count, prefix=None):
    """Print a formatted message.

    Parameters
    ----------
    msg_list : list
        A list of error messages.
    char_count : int
        Character fill line length.
    prefix : str, optional
        Character to precede each message in the list;
        if None, the list will be consecutively numbered.
    """
    for i in range(len(msg_list)):
        # Break each error message into individual words:
        # Hotfix newline characters by spacing around them.
        msg = msg_list[i].replace("\r", "").replace("\n", " \n ").split(" ")

        # Split the error message into separate lines based on each
        # line's length
        out_lines = []
        line_num = 0
        out_lines.append("")
        for j in range(len(msg)):
            count = len(out_lines[line_num] + msg[j])
            if j > 0 and msg[j-1] == "\n":
                line_num += 1
                out_lines.append(msg[j])
            elif count > char_count - 4:
                line_num += 1
                out_lines.append(msg[j])
            else:
                out_lines[line_num] += msg[j]
            out_lines[line_num] += " "
        for k in range(len(out_lines)):
            if not out_lines[k].isspace() and out_lines[k] != '':
                if k == 0 and prefix is None:
                    print("{0:2}. {1:}".format(i + 1, out_lines[k]))
                elif k == 0:
                    print("{0:>3.2} {1:}".format(prefix, out_lines[k]))
                else:
                    print("    {}".format(out_lines[k]))
    print("{}".format('-'*char_count))


def get_logger(level="CRITICAL", detailed_format=None):
    """Create a logger with stream handler.

    Parameters
    ----------
    level : str
        The logging level, defaults to CRITICAL.
        Valid options include:
        * "NOTSET"
        * "DEBUG"
        * "INFO"
        * "ERROR"
        * "CRITICAL"

    detailed_format : bool, optional
        If True, the log will include the timestamp and function name.
        If False, only the log message will be shown. If None, the user
        will be prompted to choose.

    Returns
    -------
    logging.Logger
        A root logger.

    Examples
    --------
    Create a logger with the default settings (CRITICAL level, no detailed format):

    >>> logger = get_logger()

    Create a logger with DEBUG level and detailed format:

    >>> logger = get_logger(level="DEBUG", detailed_format=True)

    Create a logger with ERROR level and no detailed format:

    >>> logger = get_logger(level="ERROR", detailed_format=False)
    """
    if isinstance(level, str):
        level = level.upper()
    if level not in ["NOTSET", "DEBUG", "INFO", "ERROR", "CRITICAL"]:
        raise ValueError("Logging level, '%s', not recognized!" % level)

    # If detailed_format is None, ask the user
    if detailed_format is None:
        user_input = input("Do you want detailed logging (timestamp and function name)? (yes/no): ").strip().lower()
        if user_input == "yes":
            detailed_format = True
        else:
            detailed_format = False

    logger = logging.getLogger()
    handler = logging.StreamHandler()

    # Determine the format based on detailed_format parameter
    if detailed_format:
        rec_format = "%(asctime)s, %(name)s.%(funcName)s: %(message)s"
    else:
        rec_format = "%(message)s"

    formatter = logging.Formatter(rec_format, datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    # HOTFIX Issue #33 [TWD; 2024-06-12]
    logger.handlers[0].stream = sys.stdout

    return logger


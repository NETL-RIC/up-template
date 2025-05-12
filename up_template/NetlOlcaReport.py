#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# NetlOlcaReport.py
#
##############################################################################
# MODULE DOCUMENTATION
##############################################################################
__doc__ = """This module provides functionality for generating reports based
on Life Cycle Inventory Data. It allows fetching data, formatting it into
readable formats, and exporting reports in Markdown, PDF, and Word formats.
This module is a key part of the NETL Life Cycle Analysis (LCA) toolkit,
designed for streamlined analysis and report generation.

Last Edited:
    2024-11-01
"""
__all__ = [
    "NetlOlcaReport",
    "DATA_DIR",
    "OUTPUT_DIR",
]


##############################################################################
# REQUIRED MODULES
##############################################################################
import datetime
import logging
import os
import re
import subprocess

import olca_schema as o
import pandas as pd
import sympy


##############################################################################
# GLOBAL PARAMETERS
##############################################################################
CALC_DIR = "calculations"
'''str : Default folder for saving calculation workbooks.'''

DATA_DIR = "data"
'''str : Default data directory where JSON-LD project files may be stored.'''

OUTPUT_DIR = "output"
'''str : Default output directory where all output files will be saved.'''


##############################################################################
# CLASSES
##############################################################################
class NetlOlcaReport:
    """A report generating class for the Jupyter Notebook unit process
    template.

    Attributes
    ----------
    netlolca : NetlOlca
        An instance of the NetlOlca worker class.
    data_fetched : bool
        Whether data was successfully read from a database or JSON-LD file.
    reference_description : str
        Unit process reference process description.
    input_flows : str
        Markdown-formatted table of input flows.
    output_flows : str
        Markdown-formatted table of output flows.
    process_code : str
        Alternative process type defined by the user during Interface.
    process_doc : str
        Unit process description.
    allocation_info : tuple
        A tuple containing allocation_factors and default_allocation_method.
    md : str
        Markdown-formatted unit process report.
    logo : str
        File name associated with the logo image for report.
    valid_ext : list
        A list of valid file extensions for report export.

    Notes
    -----
    The actors.yaml supplemental file (provided by NetlOlca class) is not
    implemented here (or in Interface class, which includes a call to
    ``get_actors``). This will likely change in the next iteration when
    editing is better handled.

    Todo:
        -   Move global variables OUTPUT_DIR and DATA_DIR to class global
            variables; this will enable a user to overwrite them if needed.

    Examples
    --------
    >>> n = NetlOlcaReport(NetlOlca())
    >>> n.reference_name = "Alkaline electrolysis"
    >>> n.get_file_name("md")
    'Alkaline_electrolysis.md'

    """
    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # Class Initialization
    # ////////////////////////////////////////////////////////////////////////
    def __init__(self, netlolca_instance):
        # Initialize with a NetlOlca instance
        self.netlolca = netlolca_instance
        self.data_fetched = False

        # Initialize attributes
        self.logo = "netl_logo_100x52.png"
        self.boundary_doc = None
        self.create_date = None
        self.reference_name = None
        self.reference_flow = None
        self.reference_description = None
        self.version = None
        self.emissions_flows = None
        self.input_flows = None
        self.location = None
        self.output_flows = None
        self.poc = None
        self.process_doc = None
        self.project_doc = None
        self.allocation_info = None
        self.param_table = None
        self.sources = []
        self.md = None
        self.valid_ext = ['.md', '.txt', '.docx', '.html', '.pdf']
        self.process_types = {
            'EP': 'Extraction Process',
            'MP': 'Manufacturing Process',
            'BP': 'Basic Process',
            'IP': 'Installation Process',
            'EC': 'Energy Conversion',
            'TP': 'Transportation Process',
            'RP': 'Recovery Process',
            'WT': 'Waste Treatment',
            'AP': 'Auxiliary Process',
        }
        self.process_code = 'BP'
        self.allocation_types = {
            'CAUSAL_ALLOCATION': 'Causal',
            'PHYSICAL_ALLOCATION': 'Physical',
            'ECONOMIC_ALLOCATION': 'Economic',
            'NO_ALLOCATION': 'No allocation',
        }

        # This will store the content read from the filled Excel workbook
        self.template_path = None
        self.calculations_content = None

        # Run initialization methods
        self.check_output_dir()

        # Create the default NETL disclaimer
        # Update to match 2024 publication guidelines [24.10.08; TWD]
        self.disclaimer = (
            "This report was prepared as an account of work "
            "sponsored by an agency of the United States Government. "
            "Neither the United States Government nor any agency thereof, "
            "nor any of their employees, makes any warranty, express or "
            "implied, or assumes any legal liability or responsibility for "
            "the accuracy, completeness, or usefulness of any information, "
            "apparatus, product, or process disclosed, or represents that "
            "its use would not infringe privately owned rights. Reference "
            "herein to any specific commercial product, process, or service "
            "by trade name, trademark, manufacturer, or otherwise does not "
            "necessarily constitute or imply its endorsement, recommendation, "
            "or favoring by the United States Government or any agency "
            "thereof. The views and opinions of authors expressed herein do "
            "not necessarily state or reflect those of the United States "
            "Government or any agency thereof."
        )

    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    # Class Function Definitions
    # ////////////////////////////////////////////////////////////////////////
    def check_output_dir(self):
        """Check that output folder exists; otherwise, create it.
        """
        if not os.path.isdir(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR)

    def convert(self, from_file, to_file):
        """Run pandoc using Python's subprocess system call.

        Parameters
        ----------
        from_file : str
            The file path to the original text (e.g., output/report.md)
        to_file : str
            The file path to the new report format (e.g., output/report.pdf)

        Raises
        ------
        OSError
            If the input file is not found.
            If the conversion fails (e.g., pandoc not installed).
        """
        # Error handling
        if not os.path.isfile(from_file):
            raise OSError("Input file, %s, missing!" % from_file)
        self.check_output_dir()

        # Scrub the file extension that's being converted to:
        # Hotfix extension tuple [2024-05-28; TWD]
        out_ext = os.path.splitext(to_file)[1]
        out_ext = out_ext.lstrip(".")
        out_ext = out_ext.upper()

        # Define the sub-process list of commands
        sp_list = ['pandoc', from_file, '-o', to_file]
        if out_ext == 'HTML':
            sp_list = [
                'pandoc',
                from_file,
                '--output',
                to_file,
                '--standalone',
                '--embed-resources',
                '--section-divs',
                '--css',
                'https://cdnjs.cloudflare.com/ajax/libs/concrete.css/3.0.0/concrete.min.css',
                '--mathjax',
                '--include-before-body',
                'template/before_body.html',
                '--include-after-body',
                'template/after_body.html',
            ]
        elif out_ext == 'DOCX':
            sp_list = [
                'pandoc', from_file,
                '-o', to_file,
                '--reference-doc', 'template/template.docx',
            ]

        try:
            subprocess.run(sp_list, check=True)
        except subprocess.CalledProcessError as e:
            raise OSError(
                "An error occurred while converting to %s. "
                "Ensure pandoc is installed and accessible. %s" % (
                    out_ext, str(e))
            )
        else:
            print(f"Report saved to {to_file}")

    def convert_to_html(self):
        """
        Convert the Markdown formatted report to an HTML file.

        This method first ensures that the report is saved in Markdown format,
        then uses `pandoc` to convert the Markdown file to an HTML file. The
        resulting HTML file is saved in the specified DATA_DIR.

        Raises
        ------
            Exception: If `pandoc` is not installed or fails to run.
        """
        # Ensure the report is saved in Markdown format
        input_path = self.get_file_path('md')
        if os.path.isfile(input_path):
            self.read_report_markdown(input_path)
        else:
            self.save_markdown()

        # Define the output file path
        output_path = self.get_file_path('html')
        self.convert(input_path, output_path)

    def convert_to_pdf(self):
        """Write markdown report to portable document format using pandoc.

        Notes
        -----
        Assumes that pandoc is installed and locally available.
        See https://pandoc.org/ for installation instructions.
        """
        input_path = self.get_file_path('md')
        if os.path.isfile(input_path):
            self.read_report_markdown(input_path)
        else:
            self.save_markdown()

        # Use reference name in the file paths
        # HOTFIX; add error handling for no PDF support [2024-05-28; TWD]
        output_path = self.get_file_path('pdf')
        try:
            self.convert(input_path, output_path)
        except OSError as e:
            logging.error("Failed to generate PDF. %s" % str(e))

    def convert_to_word(self):
        """Writes markdown report to Microsoft Word format using pandoc.

        Notes
        -----
        Assumes that pandoc is installed and locally available.
        See https://pandoc.org/ for installation instructions.
        """
        input_path = self.get_file_path('md')
        if os.path.isfile(input_path):
            self.read_report_markdown(input_path)
        else:
            self.save_markdown()

        output_path = self.get_file_path('docx')
        self.convert(input_path, output_path)

    def create_report_markdown(self):
        """Create a markdown formatted report based on class attribute values.

        Notes
        -----
        Class attributes are updated with fetched data, see :func:`fetch_data`.

        Returns
        -------
        str
            Markdown-formatted report string.
        """
        # Set default values or placeholders for report elements
        create_date = self.create_date or "%s" % datetime.datetime.now().date()
        ref_name = self.reference_name or "N/A"
        ref_flow = self.reference_flow or "N/A"
        process_desc = self.reference_description or "N/A"
        boundary_desc = self.boundary_doc or "Detailed boundary description not available"
        input_flows_md = self.input_flows or "No input flows available."
        output_flows_md = self.output_flows or "No output flows available."
        process_doc_md = self.process_doc or "No process documentation available."
        param_table_md = self.param_table or "None"
        project_doc_md = self.project_doc or "No goal or scope info available."
        project_poc_md = self.poc or "NETL"
        version_number = self.version or "1.0.0"
        allocation_md = self.allocation_info or "No allocation"

        sources_md = "None"
        if len(self.sources) > 0:
            sources_md = "\n\n".join(self.sources)

        # Add the calculations content from the filled workbook
        calculations_md = self.calculations_content or "No calculations available."

        # Create markdown report
        report_md = f"""# Overview

## Process Name
{ref_name}

## Reference Flow
{ref_flow}

## Brief Description
{process_desc}

# Metadata
{process_doc_md}

## Relevant Flows Included:

Releases to Air
:   - [ ] Greenhouse Gases
    - [ ] Criteria Air Pollutants
    - [ ] Other

Releases to Water
:   - [ ] Inorganic Emissions
    - [ ] Organic Emissions
    - [ ] Other

Releases to Soil
:   - [ ] Inorganic Emissions
    - [ ] Organic Emissions
    - [ ] Other

Water Usage
:   - [ ] Water Demand
    - [ ] Water Consumption


# Process Description

## Goal & Scope
{project_doc_md}

## Boundary & Description
{boundary_desc}

## Methods

### Block Flow Diagram
Link to your block flow diagram.
For example:

```sh
![](data/diagram.png)
```

### Input Flows
{input_flows_md}

## Output Flows
{output_flows_md}

### Process Parameters
{param_table_md}

### Allocation
{allocation_md}

### Calculations
{calculations_md}

## References
{sources_md}

# Document Control Information
Date Created
:   {create_date}

Point of Contact
:   {project_poc_md}

Revision History
:   {version_number}

How to Cite This Document
:   TBA

# Disclaimer/Terms of Use
{self.disclaimer}
        """

        return report_md

    def empty_template(self):
        """Create an empty report template.

        Returns
        -------
        str
            A markdown-formatted string.
        """
        empty_rp = f"""# Overview

## Process Name

## Reference Flow

## Brief Description

# Metadata

## Relevant Flows Included:

Releases to Air
:   - [ ] Greenhouse Gases
    - [ ] Criteria Air Pollutants
    - [ ] Other

Releases to Water
:   - [ ] Inorganic Emissions
    - [ ] Organic Emissions
    - [ ] Other

Releases to Soil
:   - [ ] Inorganic Emissions
    - [ ] Organic Emissions
    - [ ] Other

Water Usage
:   - [ ] Water Demand
    - [ ] Water Consumption


# Process Description

## Goal & Scope
<!-- Documentation - Administrative information - Project -->

## Boundary & Description
<!-- Documentation - Data source information - Data selection -->

## Methods

### Block Flow Diagram

### Input Flows

### Output Flows

### Process Parameters
<!-- Add specific adjustable process parameters here if any -->

### Allocation

### Calculations

## References

# Document Control Information
Date Created
:   TBA

Point of Contact
:   TBA

Revision History
:   TBA

How to Cite This Document
:   TBA

# Disclaimer/Terms of Use
{self.disclaimer}
        """

        return empty_rp

    def fetch_data(self, uuid=None):
        """Attempt to read data from an opened database or JSON-LD file.

        Parameters
        ----------
        uuid : str, optional
            A universally unique identifier for a product system.
            Defaults to None.
        """
        try:
            # Fetch reference name
            self.reference_name = self.netlolca.get_reference_name(uuid)
            self.reference_flow = self.netlolca.get_reference_flow(uuid)
            self.reference_description = self.netlolca.get_reference_description(uuid)

            # Fetch and format input flows if available
            raw_input_flows = self.netlolca.get_input_flows(uuid)
            if raw_input_flows:
                self.input_flows = self.format_flows(raw_input_flows)

            # Fetch and format output flows if available
            raw_output_flows = self.netlolca.get_output_flows(uuid)
            if raw_output_flows:
                self.output_flows = self.format_flows(raw_output_flows)

            # Fetch default allocation info
            self.allocation_info = self.format_allocation(uuid)

            # Fetch process location
            self.location = self.format_location(uuid)

            # Fetch and format process documentation if available
            raw_process_doc = self.netlolca.get_process_doc(uuid=uuid)
            if raw_process_doc:
                self.boundary_doc = self.format_boundary_doc(raw_process_doc)
                self.process_doc = self.format_process_doc(raw_process_doc)
                self.project_doc = self.format_project_doc(raw_process_doc)
                self.poc = self.format_poc(raw_process_doc)

            param_list = self.netlolca.find_process_parameters(uuid)
            self.param_table = self.format_parameter_table(param_list)

            sources = self.netlolca.get_sources(uuid, False)
            self.sources = [self.format_source(x) for x in sources]

        except Exception as e:
            print(f"Unexpected error during fetching data! {e}")
            self.data_fetched = False
        else:
            self.data_fetched = True
            print("Data fetched successfully.")

    def format_allocation(self, uuid):
        a_factors, a_default = self.netlolca.get_allocation_info(uuid)

        default_name = "No allocation"
        if a_default:
            default_name = a_default.name
            default_name = self.allocation_types.get(
                default_name, "No allocation")

        # Use a nested dictionary to make data frames, which can be quickly
        # converted to markdown tables.
        r_dict = {
            'Physical': {
                'Product': [],
                'Amount': [],
                'Unit': []
            },
            'Economic': {
                'Product': [],
                'Amount': [],
                'Unit': []
            },
            'Causal': {
                'Flow': [],
                'Product': [],
                'Amount': [],
            }
        }

        num_factors = len(a_factors)
        for i in range(num_factors):
            a = a_factors[i]
            a_type = self.allocation_types.get(a.allocation_type.name, None)
            if a_type is not None:
                a_product = a.product.name
                a_amount = a.value
                a_unit = a.product.ref_unit
                # NOTE: query the exchange to get category, direction, and unit
                # see NetlOlca.get_flow_by_exchange
                a_flow = a.to_dict().get('exchange', {}).get("internalId", -1)

                r_dict[a_type]['Product'].append(a_product)
                r_dict[a_type]['Amount'].append(a_amount)

                if "Unit" in r_dict[a_type].keys():
                    r_dict[a_type]['Unit'].append(a_unit)

                if 'Flow' in r_dict[a_type].keys():
                    r_dict[a_type]['Flow'].append(a_flow)

        has_econ = len(r_dict['Economic']['Product']) > 0
        has_phys = len(r_dict["Physical"]['Product']) > 0
        has_caus = len(r_dict["Causal"]['Product']) > 0

        md_txt = "Default allocation: %s" % default_name
        if num_factors > 0:
            md_txt += "\n\n"
            if has_econ:
                tmp_df = pd.DataFrame(r_dict["Economic"])
                md_txt += "Economic allocation factors:\n\n"
                md_txt += tmp_df.to_markdown(index=False)
                md_txt += "\n\n"

            if has_phys:
                tmp_df = pd.DataFrame(r_dict["Physical"])
                md_txt += "Physical allocation factors:\n\n"
                md_txt += tmp_df.to_markdown(index=False)
                md_txt += "\n\n"

            if has_caus:
                tmp_df = pd.DataFrame(r_dict["Causal"])
                md_txt += "Causal allocation factors:\n\n"
                md_txt += tmp_df.to_markdown(index=False)
                md_txt += "\n\n"

        return md_txt

    def format_boundary_doc(self, p):
        """Use data selection description from process doc for boundary."""
        return p.get("dataSelectionDescription", None)

    def format_flows(self, flows):
        """Convert the dictionary of flows to markdown table.

        Parameters
        ----------
        flows : dict
            A flow dictionary.

        Returns
        -------
        str
            A markdown-formatted table with flow name, quantity, and units.

        Notes
        -----
        All flow amounts are converted to scientific notation with three
        significant digits.
        """
        if not flows or isinstance(flows, str):
            return "No flow data available."

        # Format flows into Markdown table format
        try:
            flows_markdown = (
                "| Compartment | Flow Name | Quantity | Unit | DQI |\n"
                "|-------------|-----------|----------|------|-----|\n"
            )
            # Check for expected list length:
            num_vals = len(flows['name'])
            for i in range(num_vals):
                comp = flows['category'][i]
                dq = flows['dq'][i]
                name = flows['name'][i]
                # HOTFIX: rounds to 3 significant figures in scientific not.
                quantity = "%0.3E" % flows['amount'][i]
                unit = flows['unit'][i]
                flows_markdown += (
                    f"| {comp} | {name} | {quantity} | {unit} | {dq} |\n"
                )
        except (TypeError, AttributeError):
            flows_markdown = "Error in processing flow data."

        return flows_markdown

    def format_location(self, uuid):
        """Pull the location name from process class attribute."""
        uuid = self.netlolca.get_process_id(uuid)
        p_obj = self.netlolca.query(o.Process, uuid)

        return p_obj.to_dict().get('location', {}).get('name', 'N/A')

    def format_parameter_table(self, param_list):
        """Typeset the parameter section of the report.

        Begins with formulas of process and global scale parameters.
        Ends with a parameter table of values and uncertainties.

        Parameters
        ----------
        param_list : list
            A list of parameter objects (in olca-schema classes).

        Returns
        -------
        str
            A markdown-formatted parameter section of text.
        """
        # Calculate total number of parameters
        num_params = len(param_list)

        # Separate into four characteristic groups: process vs global and
        # input versus calculated. Note that input parameters have uncertainty
        # and no formula and calculated parameters have a formula and no
        # uncertainty.
        proc_input_params = [
            x for x in param_list if x.is_input_parameter and (
                x.parameter_scope.name == o.ParameterScope.PROCESS_SCOPE.name)]
        proc_calc_params = [
            x for x in param_list if not x.is_input_parameter and (
                x.parameter_scope.name == o.ParameterScope.PROCESS_SCOPE.name)]
        glob_input_params = [
            x for x in param_list if x.is_input_parameter and (
                x.parameter_scope.name == o.ParameterScope.GLOBAL_SCOPE.name)]
        glob_calc_params = [
            x for x in param_list if not x.is_input_parameter and (
                x.parameter_scope.name == o.ParameterScope.GLOBAL_SCOPE.name)]

        # Get total number of process-level parameters
        num_proc_params = len(proc_input_params)
        num_proc_params += len(proc_calc_params)

        # Get total number of global parameters
        num_glob_params = len(glob_input_params)
        num_glob_params += len(glob_calc_params)

        # Initialize formula section
        md_formula = ""
        if len(proc_calc_params) > 0 or len(glob_calc_params) > 0:
            md_formula = (
                "The following are parameter formulas used or referenced "
                "in this process.\n\n"
            )

        # Initialize parameter table
        md_table = ""
        if num_params > 0:
            md_table = (
                "The following table provides process and global parameter "
                "values and their associated uncertainty.\n\n"
            )
            md_table += (
                "| Scope | Name | Value | Uncertainty | Description |\n")
            md_table += (
                "|:------|:-----|------:|:------------|:------------|\n")

        if num_proc_params > 0:
            md_table += "| Process |  |  |  |  |\n"
            for param in proc_input_params:
                p_name = param.name
                p_value = "%0.3E" % param.value
                p_uncert = _fix_uncertainty(param)
                p_descr = re.sub("\\r\\n", " ", param.description)
                p_items = ["", p_name, p_value, p_uncert, p_descr]
                p_string = " | ".join(p_items)
                md_table += "| " + p_string + " |\n"

            for param in proc_calc_params:
                p_name = param.name
                p_value = "%0.3E" % param.value
                p_uncert = _fix_uncertainty(param)
                p_form = _fix_formula(p_name, param.formula)
                p_descr = re.sub("\\r\\n", " ", param.description)
                p_items = ["", p_name, p_value, p_uncert, p_descr]
                p_string = " | ".join(p_items)

                md_table += "| " + p_string + " |\n"
                md_formula += p_form + "\n\n"

        if num_glob_params > 0:
            md_table += "| Global |  |  |  |  |\n"
            for param in glob_input_params:
                p_name = param.name
                p_value = "%0.3E" % param.value
                p_uncert = _fix_uncertainty(param)
                p_descr = re.sub("\\r\\n", " ", param.description)
                p_items = ["", p_name, p_value, p_uncert, p_descr]
                p_string = " | ".join(p_items)
                md_table += "| " + p_string + " |\n"

            for param in glob_calc_params:
                p_name = param.name
                p_value = "%0.3E" % param.value
                p_uncert = _fix_uncertainty(param)
                p_form = _fix_formula(p_name, param.formula)
                p_descr = re.sub("\\r\\n", " ", param.description)
                p_items = ["", p_name, p_value, p_uncert, p_descr]
                p_string = " | ".join(p_items)
                md_table += "| " + p_string + " |\n"
                md_formula += p_form + "\n\n"

        # Add the formulas before the parameter table.
        md_table = md_formula + md_table

        return md_table

    def format_poc(self, p):
        """Use the dataset owner value from process doc for POC info.

        The author name comes from olca-schema Actor class.
        https://greendelta.github.io/olca-schema/classes/Actor.html
        """
        return p.get("dataSetOwner", {}).get('name', "NETL")

    def format_project_doc(self, p):
        """Return the reference process's project documentation to be
        used for the goal and scope in the report template.

        Parameters
        ----------
        p : dict
            Project documentation info dictionary.

        Returns
        -------
        str
            Project documentation, which should include the goal and
            scope of the project.
        """
        raw_md = p.get("projectDescription", "N/A")
        return raw_md

    def format_process_doc(self, p):
        """Convert process documentation dictionary into markdown table.

        Parameters
        ----------
        p : dict
            Process document dictionary

        Returns
        -------
        str
            Markdown-formatted table of location, valid to/from, creation
            date, and geography description.

        Notes
        -----
        Hard-codes system boundary to 'Cradle-to-Grave'.
        """
        # Format Process documentation
        if not p or isinstance(p, str):
            return "No process documentation available."

        try:
            # Initialize table
            pd_markdown = (
                "| Feature | Information |\n|-----------|----------|\n")

            # This comes from the process-level data read elsewhere.
            location = self.location or 'N/A'

            # Extracting data from process documentation
            valid_from = p.get('validFrom', 'N/A')
            valid_until = p.get('validUntil', 'N/A')
            creation = p.get('creationDate', 'N/A')
            date_part, _ = creation.split('T')
            process_type = p.get('processType', self.process_code)
            process_scope = p.get('technologyDescription', 'N/A')
            data_completeness = p.get('completeness_description', 'N/A')

            # Hardcoded for now.
            system_boundary = "Cradle-to-Gate"

            # Cleanup process scope (in case there are newlines that
            # break the table format)
            # NOTE: pandoc encodes in UTF-8.
            process_scope = process_scope.replace("\n", " ")

            # Adding data to markdown string
            pd_markdown += f"| Location | {location} |\n"
            pd_markdown += f"| Valid From | {valid_from} |\n"
            pd_markdown += f"| Valid Until | {valid_until} |\n"
            pd_markdown += f"| Creation Date | {date_part} |\n"
            pd_markdown += f"| Process Type | {process_type} |\n"
            pd_markdown += f"| Process Scope | {process_scope} |\n"
            pd_markdown += f"| System Boundary | {system_boundary} |\n"
            pd_markdown += f"| Completeness | {data_completeness} |\n"

            return pd_markdown
        except Exception as e:
            return f"Error in processing process documentation: {e}"

    def format_source(self, s_obj):
        """Convert source object into citation text string.

        Parameters
        ----------
        s_obj : olca-schema.Source
            A source object.

        Returns
        -------
        str
            Citation string.

        Notes
        -----
        The goal is to get a citation close to APA format:
        Name (Year). Title. Publication. URL.

        Often the "Text reference" field holds all this info.
        Other times it is in either the description or the name fields.
        """
        # Part 1 of the citation, author.
        s_txt = "%s" % s_obj.name

        # Part 2, year
        if s_obj.year:
            s_txt += " (%s)" % s_obj.year

        # Part 3, title
        if s_obj.text_reference:
            s_txt += ". %s" % s_obj.text_reference
        elif s_obj.description:
            s_txt += ". %s" % s_obj.description

        # Part 4, URL
        if s_obj.url:
            s_txt += ". Online: %s" % re.sub("\\r\\n", "", s_obj.url)

        # Clean-up step
        s_txt = re.sub("\\r\\n", " ", s_txt)

        return s_txt

    def generate_full_report(self):
        """Compile full markdown report.

        Returns
        -------
        str
            Full markdown-formatted report.
        """
        if not self.data_fetched:
            print("Data has not been fetched yet. Cannot generate report.")
            return None

        # Generate report markdown
        self.md = self.create_report_markdown()
        print("Report generated successfully.")
        return self.md

    def get_file_name(self, ext=".md"):
        """Generates the default report name with given file extension.

        Parameters
        ----------
        ext : str, optional
            File extension (e.g., 'md', 'html', 'docx', or 'pdf'), by default
            ".md".

        Returns
        -------
        str
            Report file name with given extension.

        Raises
        ------
        ValueError
            If a non-valid file extension is given.
            See class attribute, `valid_ext` list.
        """
        ext = ext.lower()
        # Correct parameters missing the "dot" with extension
        if not ext.startswith("."):
            ext = "." + ext
        # Error handle non-valid file extensions
        if ext not in self.valid_ext:
            raise ValueError("Invalid file extension: '%s'" % ext)
        if ext == '.txt':
            ext = '.md'

        r_name = "report" + ext
        if self.reference_name:
            # No spaces in file names
            p1 = re.compile("\\s+")
            r_name = re.sub(p1, "_", self.reference_name)

            # No special characters in file names
            p2 = re.compile("[/@.,&'\\\\\\(|\\)<>#;]+")
            r_name = re.sub(p2, "_", r_name)

            # Reduce extra underscores
            p3 = re.compile("_+")
            r_name = re.sub(p3, "_", r_name)

            # Drop trailing underscore
            if r_name[-1] == "_":
                r_name = r_name[0:-1]

            r_name += ext

        return r_name

    def get_file_path(self, ext=".md"):
        """Prepend the output directory path to the report file name.

        Parameters
        ----------
        ext : str, optional
            The report file extension (e.g., 'md', 'docx', 'html', or 'pdf'),
            by default ".md"

        Returns
        -------
        str
            File path to report of chosen file extension.
        """
        f_name = self.get_file_name(ext)

        return os.path.join(OUTPUT_DIR, f_name)

    def get_logo(self):
        """Return the relative file path to the logo image.

        The file path assumes the output report is in the default outputs
        directory and the logo is in the img directory.

        Returns
        -------
        str
            File path
        """
        return os.path.join("..", "img", self.logo)

    def get_multiline_input(self, prompt, end_marker="EOF"):
        """
        Prompt the user for multi-line input.

        Multiline reading ends when the specified end marker character string
        is entered.

        Parameters
        ----------
        prompt : str
            The prompt to display to the user.
        end_marker : str
            The marker that indicates the end of user input.

        Returns
        -------
        str
            The user-entered text.
        """
        print(prompt)
        print(f"(Type '{end_marker}' on a new line to finish)")
        lines = []
        while True:
            line = input()
            if line.strip() == end_marker:
                break
            lines.append(line)

        return "\n".join(lines)

    def pandoc_installed(self):
        """
        Check if pandoc is installed and accessible.

        Notes
        -----
        For installation instructions, see:
        https://pandoc.org/installing.html

        Returns
        -------
        bool
            True if pandoc is installed, false otherwise.
        """
        try:
            subprocess.run(
                ['pandoc', '--version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            logging.warning("Pandoc is not installed.")
            return False
        except Exception as e:
            logging.error(f"Error checking Pandoc installation: {e}")
            return False
        else:
            logging.info("Pandoc is installed.")
            return True

    def read_report_markdown(self, md_file=None):
        """Read a plain-text report.

        Parameters
        ----------
        md_file : str, optional
            File path to plain-text report, by default None.
            If no file path is given, the default markdown file is used.

        Raises
        ------
        OSError
            If file read fails.
        """
        if md_file is None:
            md_file = self.get_file_path('md')
        try:
            with open(md_file, encoding='utf-8') as f:
                md_txt = ""
                for line in f.readlines():
                    # HOTFIX: issue with reading files on Windows.
                    line = line.rstrip()
                    line += "\n"
                    md_txt += line
        except:
            raise OSError("Could not read markdown file, %s!" % md_file)
        else:
            self.md = md_txt

    def save_markdown(self):
        """Generate markdown report and save to file.

        Notes
        -----
        1.  The file is saved to the globally defined output directory with a
            file name that defaults to the reference process name.
        2.  This method re-creates the markdown report based on fetched data;
            any changes to the original markdown will be overwritten!
        """
        self.md = self.create_report_markdown()
        file_path = self.get_file_path('md')
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(self.md)
        print(f"Markdown report saved to {file_path}")

    def read_calc_wb(self,file_path):
        """
        Read the filled-out Excel workbook and extract calculations to be included in the report.

        Parameters
        ----------
        file_path : str
            The path to the filled-out Excel workbook.

        Returns
        -------
        str
            The extracted calculations as a formatted string.
        """
        try:
            # Step 1: Read the Excel file
            df = pd.read_excel(file_path, sheet_name='Calculations')

            # Step 2: Initialize a list to store formatted calculations
            calculations = []

            # Step 3: Iterate through each row in the Excel sheet
            for _, row in df.iterrows():
                parameter = row.get("Parameter", "N/A")
                formula = row.get("Formula", "N/A")
                value = row.get("Value", "N/A")
                explanation = row.get("Explanation", "N/A")
                references = row.get("References", "N/A")
                units = row.get("Units", "N/A")

                # Don't show missing units.
                if units != units or units is None or units == "N/A":
                    units = ""

                # Replace NaN with string
                if formula != formula:
                    formula = "N/A"

                # Replace NaN w/ empty string
                if value != value:
                    value = ""

                # If there's no value or units, use n/a as placeholder
                if value == "" and units == "":
                    value = "N/A"

                # Step 4: Format each calculation entry in a readable format
                calc_entry = (
                    f"Parameter, {parameter}: {explanation}\n"
                    f":   - Formula: {formula}\n"
                    f"    - Value: {value} {units}\n"
                    f"    - References: {references}\n"
                )
                calculations.append(calc_entry)

            # Step 5: Join all calculation entries into a single string
            formatted_calculations = "\n".join(calculations)

            # Step 6: Return the formatted calculations as a string
            return formatted_calculations

        except Exception as e:
            print(f"Error reading the Excel file: {e}")
            return None  # Return None if an error occurs


##############################################################################
# FUNCTIONS
##############################################################################
def _fix_formula(p_name, f_txt, in_line=False):
    """Escape common markdown characters found in equation text.

    Parameters
    ----------
    p_name : str
        The parameter name to be given a formula.
    f_txt : str
        A formula (e.g., "b * c * d")
    in_line : bool
        If true, use in-line equation markup; else use block-style.
        Defaults to false.

    Returns
    -------
    str
        The equation either in LaTeX math or in plain markdown.
        In the latter case, common characters are escaped (e.g.,
        "A\\_tot = b \\* c \\* d").

    Note
    ----
    Sympy does not like equations (with equal sign), so run the
    symplify on left- and right-hand sides and stick together
    with an equals.

    Sympy fails if there is a space before an underscore in a variable name.

    If not parameter name is given, return just the formula.
    """
    # Return empty string if there is no formula
    if f_txt == "" or f_txt != f_txt or f_txt is None:
        return ""

    has_name = (p_name != "") and (p_name == p_name) and (p_name is not None)
    has_form = (f_txt != "") and (f_txt == f_txt) and (f_txt is not None)

    try:
        # Convert to latex
        left_side = ""
        if has_name:
            left_side = sympy.latex(sympy.sympify(p_name))

        right_side = ""
        if has_form:
            right_side = sympy.latex(sympy.sympify(f_txt))
    except Exception as e:
        logging.warning("Sympy failed.\n %s" % str(e))
        # Make the formula into an equation.
        if has_name and has_form:
            f_txt = p_name + " = " + f_txt
        elif has_name and not has_form:
            f_txt = p_name
        # Escape markdown and return without LaTeX.
        new_txt = re.sub("[*]", "\\*", f_txt)
        new_txt = re.sub("[_]", "\\_", new_txt)
    else:
        if has_name and has_form:
            # Make the formula into an equation.
            new_txt = left_side + " = " + right_side
        elif has_name and not has_form:
            # Parameter only
            new_txt = left_side
        else:
            # Formula only
            new_txt = right_side

        # Put between latex equation markers
        if in_line:
            new_txt = "$%s%" % new_txt
        else:
            new_txt = "$$\n%s\n$$" % new_txt

    return new_txt


def _fix_uncertainty(param):
    """Correct the string output for a Parameter object's uncertainty data.

    Parameters
    ----------
    param : olca_schema.Parameter
        A parameter class instance.

    Returns
    -------
    str
        The uncertainty type and its parameters or 'none'.

    Notes
    -----
    Uncertainty class object-level schema is found here:
    https://greendelta.github.io/olca-schema/classes/Uncertainty.html
    """
    r_str = "none"
    if param and 'uncertainty' in dir(param) and param.uncertainty:
        # Get distribution type name
        u_type = param.uncertainty.distribution_type.name
        u_type = u_type.replace("_", " ")
        u_type = u_type.title()

        # Pull the param values
        u_gmean = param.uncertainty.geom_mean
        u_gsdev = param.uncertainty.geom_sd
        u_max = param.uncertainty.maximum
        u_ave = param.uncertainty.mean
        u_min = param.uncertainty.minimum
        u_mode = param.uncertainty.mode
        u_sdev = param.uncertainty.sd

        # Build lists of parameter names and values
        u_names = ['gmean', 'gsdev', 'max', 'ave', 'min', 'mode', 'sdev']
        u_params = [u_gmean, u_gsdev, u_max, u_ave, u_min, u_mode, u_sdev]
        num_params = len(u_params)

        # Pair together only parameters with values.
        u_params = [
            "%s:%s" % (u_names[i], u_params[i]) \
                for i in range(num_params) \
                    if u_params[i] is not None
        ]
        u_params = ", ".join(u_params)

        # Bring it all together, for example:
        # Triangle Distribution (max:13.0, min:5.0, mode:7.5)
        r_str = "%s (%s)" % (u_type, u_params)

    return r_str

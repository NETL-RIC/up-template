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

Examples:

>>> from up_template import NetlOlcaReport
>>> from netlolca import NetlOlca
>>> n = NetlOlca()                          # initialize data manager
>>> n.connect()                             # establish with IPC Server
>>> n.read()                                # read openLCA database
>>> r = NetlOlcaReport(n)                   # creates 'output' folder
>>> ps_id = r.product_systems[0]            # find 1st product system UUID
>>> r.fetch_data(ps_id)                     # automated data scraping
>>> r.convert_to_html()                     # create .md; render to .html

Last Edited:
    2026-03-13
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
class NetlOlcaReport(object):
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
    # Class Properties
    # ////////////////////////////////////////////////////////////////////////
    @property
    def product_systems(self):
        """List of product system UUIDs"""
        return self.netlolca.get_spec_ids(
            self.netlolca.get_spec_class("Product system")
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
                '--css',
                'resources/styles.css',
                '--metadata',
                f'pagetitle={self.reference_name}',
                '--title-prefix=NETL UP Library',
                '--mathjax',
                '--include-before-body',
                'resources/before_body.html',
                '--include-after-body',
                'resources/after_body.html',
            ]
        elif out_ext == 'DOCX':
            sp_list = [
                'pandoc', from_file,
                '-o', to_file,
                '--reference-doc', 'resources/template.docx',
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
        This is a semi-automated report for the natural gas combustion unit
        process.

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

        # Issue #8. Scenario attribute table (from workbook in DATA_DIR).
        try:
            scenario_table_md = scenario_attribute_table(
                workbook_filename="DS_Stage5_O_Natural_Gas_Combustion_2014.01.xlsx",
                sheet_name="PS",
                header_row_excel=6,
                start_col_excel="D",
            )
        except Exception as e:
            logging.warning(f"Scenario attribute table could not be created: {e}")
            scenario_table_md = "No scenario attributes available."

        # Add the calculations content from the filled workbook
        calculations_md = self.calculations_content or "No calculations available."

        # Issue #8. Create markdown report (this has hard-coded values).
        report_md = f"""# Overview

## Process Name
{ref_name}

## Reference Flow
{ref_flow}

## Brief Description
{process_doc_md}


# Process Description

## Goal & Scope
{process_desc}

## Process Boundary
{boundary_desc}

![](data/diagram.png)

### Input Flows

The table below provides a list of resource flows for this process.

<div class="table-wrapper" markdown="block">

{input_flows_md}

</div>

### Output Flows

The table below provides a list of emission flows for this process.

<div class="table-wrapper" markdown="block">

{output_flows_md}

</div>

## Preferred Providers

_For each input product flow, add a statement as to its potential provider process(es)._

## Suggested Downstream Uses

_Based on the quantitative reference flow, add a statement as to what processes may use this flow as a resource (if any)._


# Methods

## Scenarios

The following table describes the scenarios used in this process.

{scenario_table_md}

## Process Parameters

The following table provides parameter quantities for each of the scenarios defined [above](#scenarios).
These parameters represent the emissions found in the [output flow table](#output-flows).

{param_table_md}

## Allocation
{allocation_md}

## Calculations and Supplements

This report utilized the following supplemental files:

- .xlsx
    * _Include any workbooks used._
- .py
    * _Include any Python scripts (or Jupyter notebooks) used._
- .zolca
    * _Include the openLCA .zolca (or JSON-LD)._


## Modeling Assumptions

- _List the modeling assumptions, which may be found in "Modeling constants" section for process documentation in openLCA._

# Data

## Data Quality

The following Data Quality Indicator (DQI) scores are assigned to this process
using the DQI Matrix.

<div class="table-wrapper" markdown="block">

| DQI Indicator | Score | Basis for Score |
|--------------|:-----:|----------------|
| Source Reliability | **x** | _description_ |
| Completeness | **x** | _description_ |
| Temporal Correlation | **x** | _description_ |
| Geographical Correlation | **x** | _description_ |
| Technological Correlation | **x** | _description_ |

</div>

## Data Source Information

_Copy the values from the named fields below from openLCA's process documentation into the table._

| Element | Description |
|--------|-------------|
| Data Completeness |  |
| Data Selection |  |
| Data Treatment |  |
| Sampling Procedure |  |
| Data Collection Period |  |

## References
{sources_md}


# Use Information

Use Advice
:   _Copy text from "Intended Application" field in openLCA._

Access and Restrictions
:   _Copy text from "Access and use restrictions" field in openLCA._


# Document Control Information
Report Created:
:   {create_date}

Point of Contact:
:   {project_poc_md}

Revision History:
:   {version_number}

How to Cite This Document:
:   _Copied from EDX submission._

Archived
:   False

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

_The following template has instructions included under each section in italics._

## Process Name

_Process naming format should be based on the following: "Base name; treatment received, production route(s), standard(s) fulfilled; production or consumption type, location type; quantitative flow properties"_

## Reference Flow

_Copy and paste the quantitative reference flow for the process including the flow amount, units, and name._

## Brief Description

_High-level process summary that communicates the basic technology and what is included in the boundary; see example below._

- Process Type: _State whether this is a Unit Process or System Process_
- Inventory Method: _State whether this is Attributional or Consequential_
- Technology Type: _High level technology categorization, such as natural gas, or bio fuels_
- Unit Process Boundary: _State whether the process is Cradle-to-Grave, Cradle-to-Gate, Gate-to-Gate, etc._
- Co-products: _List names, if applicable; otherwise, N/A_
- Co-product allocation: _If applicable; otherwise, N/A. Examples include system expansion and mass allocation; list what is used and if there are any restrictions._
- Scenarios: _Yes or no (e.g., link to [Scenarios](#scenarios) section)_
- Location: _Geographic region associated with the unit process_
- Valid From: _Year or date format_
- Valid Until: _Year or date format_
- Unit Process Creation Date: _May be different from report date_
- Data Quantity Score: _The process DQI score (e.g., link to [Data Quality](#data-quality) for explanation of scoring)_
- Data Completeness: _Link to [Data Source Information](#data-source-information) for more information_

_Conclude with the stated intended use._

# Process Description

## Goal & Scope

_Define the purpose, and boundaries of the unit process, specifying what is included or excluded in the inventory._

## Process Boundary

_Describes the specific cutoff points that determine which inputs, outputs, and life cycle stages are included or excluded in the inventory._

_Also, include a graphic of the box diagram for your process._

## Input Flows

_Provide an introduction (e.g., "The table below provides a list of resource flows for this process.") and provide a table of resources with columns: 'Compartment', 'Flow Name', 'Quantity', 'Unit', and 'DQI' (automated in Python)._

## Output Flows

_Provide an introduction (e.g., "The table below provides a list of emission flows for this process.") and provide a table of resources with columns: 'Compartment', 'Flow Name', 'Quantity', 'Unit', and 'DQI' (automated in Python)._

## Preferred Providers

_Include a process or description of upstream providers for each of the product flows identified in the input table._

## Suggested Downstream Uses

_Include a process or description of process, models, or domains where the use of this unit process may be applicable._

# Methods

## Scenarios

_For natural gas unit processes, there are often scenarios that may be described in more detail here._

## Allocation

_State whether any allocation methods were used across co-products or by-production identified in the outputs table._


## Calculations and Supplements

_Include links and descriptions to additional resources that were utilized in creating this report and how they were utilized._
_This includes, but is not limited to Excel workbooks, Python scripts, Jupyter notebooks, and other data files._

## Modeling Assumptions

_List any assumptions and known limitations to the utility or applicability of this unit process._

# Data

## Data Quality

_Provide an overview of the data quality index utilized for this process, and include a table of its scores (see below for example empty table)._

<div class="table-wrapper" markdown="block">

| DQI Indicator | Score | Basis for Score |
|--------------|:-----:|----------------|
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |

</div>

## Data Source Information

_Additional data source metadata is included here (e.g., Data Completeness, Data Selection, Data Treatment, Sampling Procedure, and Data Collection Period), which should all be automated from openLCA (see below for empty table example)._

<div class="table-wrapper" markdown="block">

| Element | Description |
|--------|-------------|
| Data Completeness |  |
| Data Selection |  |
| Data Treatment |  |
| Sampling Procedure |  |
| Data Collection Period |  |

</div>


## References

_List the references cited in this report following a standard style (e.g., APA or IEEE)._

# Use Information

Use Advice
:   _Describe the intended application and any additional uses._

Access and Restrictions
:   Neither the U.S. Department of Energy (DOE) National Energy Technology Laboratory (NETL) nor any person acting on behalf of these organizations:

    A.  Makes any warranty or representation, express or implied, with respect to the accuracy, completeness, or usefulness of the information contained in this document, or that the use of any information, apparatus, method, or process disclosed in this document may not infringe on privately owned rights; or

    B.  Assumes any liability with this report as to its use, or damages resulting from the use of any information, apparatus, method, or process disclosed in this document.

    Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise, does not necessarily constitute or imply its endorsement, recommendation, or favoring by NETL.  The views and opinions of the authors expressed herein do not necessarily state or reflect those of NETL.

# Document Control Information

Date Created
:   _The date when the report was finalized._

Point of Contact
:   _Name and email address._

Revision History
:   _Version number. If other than 1.0, consider including a list of changes._

How to Cite This Document
:   _Recommended citation (full text)._

Archived
:   _True/False (Yes/No) to indicate the active (false) or superseded (true) status._

# Disclaimer/Terms of Use

_Standard federal disclaimer (see default language below)._

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

            # NEW: EY25 test case uses the supplemental MD table [260219;TWD]
            # param_list = self.netlolca.find_process_parameters(uuid)
            # self.param_table = self.format_parameter_table(param_list)
            self.param_table = '<div class="horizontal-scroll-except-first-column" markdown="block">'
            self.param_table += '\n\n'
            self.param_table += read_markdown_table("up_test_parameters.txt")
            self.param_table += "\n\n</div>"

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
                # HOTFIX: for scenarios, use formula if available [260219; TWD]
                quantity = flows['amountFormula'][i]
                if quantity is None:
                    # HOTFIX: round to 3 sig figs in scientific notation
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
            #Open scrollable table
            md_table += '<div class="table-wrapper" markdown="block">\n\n'

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

        # Close scrollable table
        if num_params > 0:
            md_table += "\n</div>\n"

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
            r_name = re.sub(p1, "-", self.reference_name)

            # No special characters in file names
            p2 = re.compile("[/@.,&'\\\\\\(|\\)<>#;]+")
            r_name = re.sub(p2, "-", r_name)

            # Reduce extra dashes
            p3 = re.compile("-+")
            r_name = re.sub(p3, "-", r_name)

            # Drop trailing dash
            if r_name[-1] == "-":
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
        return os.path.join("..", "resources", self.logo)

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

    def save_markdown(self, blank=False):
        """Generate markdown report and save to file.

        Parameters
        ----------
        blank : bool (optional)
            Whether to save a blank template.
            Defaults to false.

        Notes
        -----
        1.  The file is saved to the globally defined output directory with a
            file name that defaults to the reference process name.
        2.  This method re-creates the markdown report based on fetched data;
            any changes to the original markdown will be overwritten!

        Examples
        --------
        >>> r = NetlOlcaReport(NetlOlca()) # initialize empty class
        >>> r.save_markdown(blank=True)    # create empty template
        """
        if blank:
            if self.reference_name is None:
                self.reference_name = "blank-report"
            self.md = self.empty_template()
        else:
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
            new_txt = f"${new_txt}$"
        else:
            new_txt = f"$$\n{new_txt}\n$$"

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


def read_markdown_table(md_file):
    """Helper function to read a markdown table from a file.

    Parameters
    ----------
    md_file : str
        Markdown file name.
        Note: file must be located in the ``DATA_DIR`` directory.

    Returns
    -------
    str
        Markdown table as a Python string.

    Raises
    ------
    OSError
        If the file does not exist in the ``DATA_DIR``.
    """
    file_path = os.path.join(DATA_DIR, md_file)
    if not os.path.isfile(file_path):
        raise OSError("Failed to find %s in %s!" % (md_file, DATA_DIR))
    with open(file_path, 'r') as f:
        my_data = f.readlines()  # newline character is in the string
    my_str = "".join(my_data)
    return my_str


def scenario_attribute_table(
    workbook_filename: str,
    sheet_name: str = "PS",
    *,
    header_row_excel: int = 6,
    start_col_excel: str = "D",
    max_height_px: int = 600,
    return_dataframe: bool = False,
):
    """Build scenario attribute table from scenario header strings in an Excel sheet.

    Workbook must be located in DATA_DIR. Scenario names are assumed to be in the
    header row (Excel row header_row_excel) starting at start_col_excel.
    """
    workbook_path = os.path.join(DATA_DIR, workbook_filename)
    if not os.path.isfile(workbook_path):
        raise OSError(f"Workbook not found in DATA_DIR: {workbook_path}")

    # Convert Excel col letter(s) to 0-indexed integer
    col_letter = str(start_col_excel).strip().upper()
    if not col_letter or any(not ("A" <= c <= "Z") for c in col_letter):
        raise ValueError(f"Invalid Excel column letter: {start_col_excel}")

    start_col_index = 0
    for c in col_letter:
        start_col_index = start_col_index * 26 + (ord(c) - ord("A") + 1)
    start_col_index -= 1

    header_row_index = header_row_excel - 1
    scenario_source_df = pd.read_excel(
        workbook_path,
        sheet_name=sheet_name,
        header=header_row_index,
        engine="openpyxl",
    )

    scenario_header_candidates = list(scenario_source_df.columns[start_col_index:])
    scenario_names = []
    for header_val in scenario_header_candidates:
        if pd.isna(header_val):
            continue
        header_text = re.sub(r"\s+", " ", str(header_val)).strip().strip(",")
        if header_text.startswith("External Combustion Boilers") or header_text.startswith("Internal Combustion Engines"):
            scenario_names.append(header_text)

    scenario_records = []
    for scenario_id, scenario_name in enumerate(scenario_names, start=1):
        name = re.sub(r"\s+", " ", str(scenario_name)).strip().strip(",")
        parts = [p.strip() for p in name.split(",") if p.strip()]

        tech = parts[0] if len(parts) > 0 else "NA"
        sector = parts[1] if len(parts) > 1 else "NA"
        fuel = parts[2] if len(parts) > 2 else "NA"
        remainder = parts[3:] if len(parts) > 3 else []

        regulatory_vintage = "NA"
        size_class_mmbtu_hr = "NA"
        firing_type = "NA"
        operating_mode = "Standard"

        if "External Combustion Boilers" in tech:
            technology_family = "External Combustion Boiler"
            equipment_category = "Boiler"

            if "Pre-NSPS" in name:
                regulatory_vintage = "Pre-NSPS"
            elif "Post" in name and "NSPS" in name:
                regulatory_vintage = "Post-NSPS"

            if any(r.lower() == "cogeneration" for r in remainder):
                operating_mode = "Cogeneration"
                equipment_subtype = "Cogeneration"
                control_technology = remainder[-1] if remainder else "NA"

                scenario_records.append({
                    "Scenario_ID": scenario_id,
                    "Scenario_Name": name,
                    "Technology_Family": technology_family,
                    "Sector": sector,
                    "Fuel": fuel,
                    "Equipment_Category": equipment_category,
                    "Equipment_Subtype": equipment_subtype,
                    "Size_Class_MMBtu_hr": "NA",
                    "Firing_Type": "NA",
                    "Control_Technology": control_technology,
                    "Regulatory_Vintage": regulatory_vintage,
                    "Operating_Mode": operating_mode,
                })
                continue

            if any("Tangentially Fired Units" in r for r in remainder):
                equipment_subtype = "Tangential"
                firing_type = "Tangential"
            else:
                equipment_subtype = "Non-tangential"
                firing_type = "Non-tangential"
                joined = " ".join(remainder)
                if re.search(r">\s*100", joined):
                    size_class_mmbtu_hr = ">100"
                elif re.search(r"<\s*100", joined):
                    size_class_mmbtu_hr = "<100"
                elif re.search(r"10\s*-\s*100", joined):
                    size_class_mmbtu_hr = "10-100"
                elif re.search(r"<\s*10", joined):
                    size_class_mmbtu_hr = "<10"

            control_technology = remainder[-1] if remainder else "NA"

        else:
            technology_family = "Internal Combustion Engine"
            equipment_category = "Engine"
            equipment_subtype = remainder[0] if remainder else "NA"
            control_technology = remainder[-1] if remainder else "NA"
            operating_mode = "Cogeneration" if ":Cogeneration" in equipment_subtype else "Standard"
            regulatory_vintage = "NA"
            size_class_mmbtu_hr = "NA"
            firing_type = "NA"

        scenario_records.append({
            "Scenario_ID": scenario_id,
            "Scenario_Name": name,
            "Technology_Family": technology_family,
            "Sector": sector,
            "Fuel": fuel,
            "Equipment_Category": equipment_category,
            "Equipment_Subtype": equipment_subtype,
            "Size_Class_MMBtu_hr": size_class_mmbtu_hr,
            "Firing_Type": firing_type,
            "Control_Technology": control_technology,
            "Regulatory_Vintage": regulatory_vintage,
            "Operating_Mode": operating_mode,
        })

    scenario_columns = [
        "Scenario_ID",
        "Scenario_Name",
        "Technology_Family",
        "Sector",
        "Fuel",
        "Equipment_Category",
        "Equipment_Subtype",
        "Size_Class_MMBtu_hr",
        "Firing_Type",
        "Control_Technology",
        "Regulatory_Vintage",
        "Operating_Mode",
    ]
    scenario_table_df = pd.DataFrame(scenario_records)
    for c in scenario_columns:
        if c not in scenario_table_df.columns:
            scenario_table_df[c] = "NA"
    scenario_table_df = scenario_table_df[scenario_columns].fillna("NA")

    scenario_table_md = (
        f'<div style="width:100%; overflow:auto; max-height:{max_height_px}px;">\n\n'
        f'{scenario_table_df.to_markdown(index=False)}\n\n'
        f'</div>\n'
    )

    if return_dataframe:
        return scenario_table_df, scenario_table_md
    return scenario_table_md


#
# SANDBOX
#
if __name__ == '__main__':
    from up_template import NetlOlcaReport
    from netlolca import NetlOlca
    n = NetlOlca()                          # initialize data manager
    n.connect()                             # establish with IPC Server
    n.read()                                # read openLCA database
    r = NetlOlcaReport(n)                   # creates 'output' folder
    ps_id = r.netlolca.get_spec_ids(        # find 1st product system UUID
        r.netlolca.get_spec_class("Product system")
    )[0]
    r.fetch_data(ps_id)                     # automated data scraping
    r.convert_to_html()                     # create .md; render to .html

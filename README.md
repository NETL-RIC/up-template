# NETL's Unit Process Template and Report Generator
[![DOI - 10.18141/2564974](https://img.shields.io/badge/DOI-10.18141%2F2564974-blue)](https://doi.org/10.18141/2564974)

A Jupyter Notebook for developing and reporting NETL LCA unit processes.

The foundation of all tools in this package is the [NetlOlca](https://doi.org/10.18141/2503973) class, which is designed to provide a single set of methods for querying and editing openLCA databases either directly with openLCA app or indirectly via exported JSON-LD zip files.


## Jupyter Notebook Unit Process Template
The unit process template is a markdown file, organized by headers, to capture the essential information that goes into the creation of a life cycle unit process.
Capturing key metadata is critical for reproducibility of unit processes and for transparency to enable its application.

Two Python classes were developed to support the generation of this report:

1. NetlOlcaReport (up_template/NetlOlcaReport.py)
2. Interface (up_template/Interface.py)

The NetlOlcaReport class provides the methods for converting openLCA entity data into usable data frames and summaries and writing them into markdown format that can be converted into other reportable formats (e.g., HTML, Microsoft Word, and PDF).
The file format conversion depends on a user's local installation of [pandoc](https://pandoc.org/), a free and open-source tool for converting between different markup formats.

To create a blank template in markdown:

```python
>>> from netlolca import NetlOlca
>>> from up_template import NetlOlcaReport
>>> r = NetlOlcaReport(NetlOlca())
>>> r.save_markdown(blank=True)
```

You may edit this markdown file before rendering to HTML.
If you rename the file, be sure to update the reference name in the Python class.

```python
>>> r.reference_name = "new_report"  # don't include the file extension
```

To generate the HTML version of the report, run the conversion method (PDF and Microsoft Word formats are also available).

```python
>>> r.convert_to_html()  # requires pandoc install
>>> r.convert_to_pdf()   # requires additional LaTeX install
>>> r.convert_to_word()
```

Automated methods are available in the NetlOlcaReport class, which attempt to read and extract metadata from an openLCA database and map it to the report template.
Similar to above, the steps to connect the NetlOlcaReport class to an openLCA database are as follows:

```python
>>> n = NetlOlca()
>>> n.connect()     # establish connection via IPC service (default port 8080)
>>> n.read()        # read database UUIDs
>>> r = NetlOlcaReport(n)
>>> ps_uuid = r.product_systems[0]  # Get UUID of lone Product System
>>> r.fetch_data(ps_uuid)           # Scrape database for metadata
>>> r.save_to_html()  # create MD and HTML report files
```

The Interface.py is an experimental class that guides users through metadata review and gap-filling.
This is best accommodated through [JupyterLab](https://jupyter.org/), the latest web-based interactive development environment for computational notebooks.
JupyterLab may be installed using Python's `pip` or conda's `install` commands.
To start Jupyter Lab, run the following command (after installing) in the parent folder where your up_template.ipynb is located:

```bash
$ jupyter lab
```

This should start the Jupyter notebook server and automatically launch the landing page in your default web browser.


## Repository Organization

    up-template/
    ├── calculations/   <- store for auxiliary Excel workbooks to document
    │   │                  calculations in the UP template
    │   └── calculation_template.xlsx   <- template for calculations
    │
    ├── (data/)         <- folder for data files (e.g., JSON-LD)
    │
    ├── dockers/ (for getting things to run in Docker)
    │   ├── USERGUIDE.md   <- Docker instructions
    │   ├── gdt_server/
    │   │   ├── README.md
    │   │   ├── build.bat
    │   │   ├── build.sh
    │   │   ├── get-docker.bat
    │   │   ├── get-docker.sh
    │   │   ├── run.bat
    │   │   └── run.sh
    │   └── jupyter/
    │       ├── README.md
    │       ├── build.bat
    │       ├── build.sh
    │       ├── get-docker.bat
    │       ├── get-docker.sh
    │       ├── requirements.txt
    │       ├── run.bat
    │       └── run.sh
    │
    ├── docs/           <- Sphinx documentation (e.g. user's guide)
    │   ├── source/          <- source files for building documentation
    │   ├── make.bat         <- Windows / *nx make files for building
    │   └── Makefile         <- source files to documentation (e.g., html)
    │
    ├── img/            <- image resources for notebooks and README
    │   ├── ipynb-token.png (92 KB)
    │   └── package_uml.png (281 KB)
    │
    ├── (output/)       <- Created when running UP Template to store the
    │                      generated reports (e.g., .md, .html, .docx, .pdf)
    │
    ├── resources/
    │   ├── after_body.html
    │   ├── banner.png                        <- header in up_template.ipynb
    │   ├── before_body.html
    │   ├── boundary_diagram.png
    │   ├── logo_doe-netl_white_1000x176.png  <- footer in template.docx
    │   ├── netl_logo_100x52.png              <- header in template.docx
    │   ├── netl_logo_1153x599.png            <- header in before_body.html
    │   ├── styles.css
    │   └── template.docx
    │
    ├── up_template/       <- Source code for this package.
    │   ├── __init__.py               <- Makes this a Python package.
    │   ├── Interface.py              <- Class for menu-driven UP template.
    │   └── NetlOlcaReport.py         <- Class for UP report generation.
    │
    ├── .gitignore        <- Git repo ignore list
    ├── LICENSE           <- Package licensing information; CC0 1.0
    │                        https://creativecommons.org/publicdomain/zero/1.0/
    ├── README.md         <- The top-level README.
    ├── setup.py          <- Makes package pip installable (`pip install -e .`)
    │                        (see Installation section for troubleshooting)
    └── up_template.ipynb <- Unit Process development template.


## Sphinx Documentation
The following describes the steps takes to create the documentation (under docs/source).
Note that for rendering the documentation, only the last step is necessary.

| `Graphviz <https://graphviz.org/download/>`_ is a third-party software dependency (similar to pandoc) for generating UML diagrams within the documentation.
| Installation of this free software is available across all major operating systems.
| If unavailable, please remove the blocks in the documentation that use graphviz before rendering (e.g., graphviz and inheritance_diagram).

1. Install Sphinx Python package (version 7.2.6)

    ```command
    $ pip install sphinx
    ```

2. Create docs folder in repository
3. Run quick start

    ```command
    $ sphinx-quickstart
    ```

4. Configuration:
    - Create separate build and source folders
5. Modify the conf.py file in source
    - Add top-matter for path correction (need access to one level up)
    - Add extensions for:
        * autodoc (generate documentation based on source code),
        * mathjax (add support for rendering math equations)
        * napolean (add support for numpy-style documentation)
        * graphviz (add support for UML diagrams)
        * inheritance_diagram (for hyperlinked image to class doc)
    - Turn on figure, table, section numbering
    - Set theme to 'alabaster'
    - Add logo
6. Run autodoc

    ```command
    $ sphinx-autogen
    ```

7. Correct the modules.rst file
    - Remove the setup.py script
8. Modify the index.rst file
    - Add individual pages to the TOC
9. Render the site

    ```command
    $ make html
    ```

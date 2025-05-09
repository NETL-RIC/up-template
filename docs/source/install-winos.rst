Windows Installation
====================

Note that NETL and KeyLogic PCs may come preinstalled with Python (via Anacondas), if requested through IT.
If not, follow the download and installation instructions below.


Python on Windows
-----------------

1. There are several ways to install Python on Windows; the recommended method is to use the third-party software, Anacondas, which conveniently packages Python and conda tools together.

2. Instructions are available here: https://docs.anaconda.com/free/anaconda/install/windows/. Below are recommended settings during the installation process:

   a. Install for Just Me

   b. Add Anaconda3 to my PATH environment variable (note: yours may look different)

   .. image:: image2.png
      :width: 5.325in
      :height: 2.21667in

3. After installation, test to see that anaconda works.

   a. Open the Command Prompt app.

   b. Type \`conda --version\` and hit enter.

   c. You should get a version number (for example, see screenshot below).

   .. image:: image3.png
      :width: 5.0875in
      :height: 1.30833in

Windows Setup: virtual environments
-----------------------------------

1. Depending on your Python installation, you may have conda (e.g., if installed with Anaconda, see Installation), which provides tools for creating **virtual environments** (an independent set of Python packages installed in their own site directories; acts as a container with its own Python interpreter and libraries separate from other existing Python installations).

   Other Python virtual environment tools exist. For non-conda installations, the virtualenvwrapper-win tool is recommended (see here: https://docs.python-guide.org/dev/virtualenvs/#virtualenvwrapper).

2. For conda:

   a. For a full reference guide, see https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html

   b. To list the currently installed virtual environments

      i.   Open Command Prompt and type \`conda env list\`

      ii.  Anaconda comes with a "base" environment along with any other user-defined environments. In the snapshot below, the "base" and user-defined "ebm" environments are available.

         .. image:: image4.png
            :width: 4.47083in
            :height: 1.75in

   c. To create a new virtual environment for your UP template work:

      i.    Open Command Prompt

      ii.   Type \`conda create -n olca python=3.11\` (note that Python >3.11 is required for olca-ipy connection with openLCA v2.0)

      iii.  Hit enter and conda will begin collecting the package meta data to resolve the new environment (see screenshot).

         .. image:: image5.png
            :width: 5in
            :height: 1.6012in

      v.    Once resolved, conda will display the package plan and the required downloads.

         .. image:: image6.png
            :width: 5in
            :height: 3.42208in

      vii.  You will be prompted to begin the download and installation process.

         .. image:: image7.png
            :width: 5in
            :height: 2.82855in

      ix.   After installation, conda displays the syntax for activating the virtual environment (e.g. \`conda activate olca\`); if this fails try: \`activate olca\` (omitting the "conda").

         .. image:: image8.png
            :width: 3.5in
            :height: 2.47083in

      xi.   You will know a virtual environment is active when the name of the active virtual environment appears to the right of the command prompt in parentheses.

         .. image:: image9.png
            :width: 2.04583in
            :height: 0.25in

Windows Setup: dependency packages
----------------------------------

1. As described in the README, the required third-party Python packages include the following:

   a. olca-ipc (https://github.com/GreenDelta/olca-ipc.py)

   b. pandas (https://pandas.pydata.org/)

   c. pyyaml (https://pyyaml.org/wiki/PyYAMLDocumentation)

   d. jupyterlab (https://jupyter.org/)

      i. Note that this package also installs Jupyter Lab, a web-based developer's environment

2. Activate the virtual environment you want to install packages to (e.g., \`conda activate olca\`)

3. Install olca-ipc

   a. Recommended first attempt: \`conda install olca-ipc\`

   b. If you receive a PackagesNotFoundError (such as indicated below):

      .. image:: image10.png
         :width: 5.5in
         :height: 1.11763in

   d. try pip: \`pip install olca-ipc\`

      .. image:: image11.png
         :width: 5.5in
         :height: 2.87877in

4. Continue the successful installation option (i.e., \`conda install\` or \`pip\`) for \`pyyaml\`, \`pandas\`, and \`jupyterlab\`.

   a. Note that \`conda install\` is a faster installer and is the preferred method to use in conda virtual environments; use \`pip install\` when conda fails.

5. Test new package installation

   a. Open the Command Prompt and type \`jupyter lab\` to boot the Jupyter web-based developer's environment. It should open your default web browser.

   b. In case you receive an error (e.g., ModuleNotFoundError pictured below),

      .. image:: image12.png
         :width: 5.5in
         :height: 0.69897in

   d. Try installing the missing packages (e.g., \`conda install chardet\`) and re-run \`jupyter lab\`

macOS Installation
==================

| Note that for individuals using a model of Mac with the Apple silicone chip (M1, M2) there is a preinstalled version of python on the system. This may usually be python 2.7 or 2.8. This should not affect your installation of the latest version of python as a system can handle two version of python without having to delete either.
| Please do not delete the default version of python on your Mac, this may cause issues in proper functioning of your system.

Python on macOS
----------------

1. There are several ways to install Python on Windows; the recommended method is to use the third-party software, Anacondas, which conveniently packages Python and conda tools together.

2. Instructions are available here: `https://docs.anaconda.com/free/anaconda/install/mac-os <https://docs.anaconda.com/free/anaconda/install/mac-os/#wizard-install>`__. Below are recommended settings during the installation process:

   a. Install for "Just Me" upon running the `Anaconda installer <https://www.anaconda.com/download>`__.

      Note: If you are running a mac with the M1, M2, or M3 chip, make sure to select the relevant installer, as shown in the drop-down in the screenshot below.

      .. image:: image13.png
         :alt: A screenshot of a computer download Description automatically generated
         :width: 5.10504in
         :height: 2.38671in

   b. Allow the installer to run the program for the installer.

      .. image:: image14.png
         :alt: A screenshot of a software error Description automatically generated
         :width: 4.31694in
         :height: 3.09565in

   c. Select "Install for me only" in the Destination Select stage

      .. image:: image15.png
         :alt: A screenshot of a software Description automatically generated
         :width: 4.4913in
         :height: 3.1727in

3. After installation, test to see that anaconda works.

   a. Open the Terminal app.

   b. Type \`conda --version\` and hit enter.

   c. You should get a version number (for example, see screenshot below).

      .. image:: image16.png
         :alt: A screenshot of a computer Description automatically generated
         :width: 4.53047in
         :height: 2.82089in

macOS Setup: virtual environments
---------------------------------

1. Depending on your Python installation, you may have conda (e.g., if installed with Anaconda, see macOS Installation), which provides tools for creating **virtual environments** (an independent set of Python packages installed in their own site directories; acts as a container with its own Python interpreter and libraries separate from other existing Python installations).

   Other Python virtual environment tools exist. For non-conda installations, the virtualenvwrapper-win tool is recommended (see here: https://docs.python-guide.org/dev/virtualenvs/#virtualenvwrapper).

2. For conda:

   a. For a full reference guide, see https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html

   b. To list the currently installed virtual environments.

      i.  Open Terminal and type \`conda env list\` or \`conda info --envs\`

      ii. Anaconda comes with a "base" environment along with any other user-defined environments. In the snapshot below, the "base" environment, shown in the screenshot below.

         .. image:: image17.png
            :alt: A screenshot of a computer Description automatically generated
            :width: 4.59591in
            :height: 2.83829in

   c. To create a new virtual environment for your UP template work:

      i.   Open Terminal

      ii.  Type \`conda create -n olca python=3.11\` (note that Python >3.11 is required for olca-ipy connection with openLCA v2.0)

      iii. Hit enter and conda will begin collecting the package meta data to resolve the new environment (see screenshot).

         .. image:: image18.png
            :alt: A screenshot of a computer Description automatically generated
            :width: 6.5in
            :height: 1.34236in

      iv. Once resolved, conda will display the package plan and the required downloads and you will be prompted to begin the download and installation process.

         .. image:: image19.png
            :alt: A screenshot of a computer Description automatically generated
            :width: 4.12929in
            :height: 3.74106in

      v. After installation, conda displays the syntax for activating the virtual environment (e.g. \`conda activate olca`); if this fails try: \`activate olca\` (omitting the "conda").

         .. image:: image20.png
            :alt: A white background with black text Description automatically generated
            :width: 4.54348in
            :height: 1.48974in

      vi. You will know a virtual environment is active when the name of the active virtual environment appears to the right of the Terminal's prompt in parentheses.

         .. image:: image21.png
            :width: 3.68992in
            :height: 0.42609in

macOS Setup: dependency packages
--------------------------------

1. As described in README, the required third-party Python packages include the following:

   a. olca-ipc (https://github.com/GreenDelta/olca-ipc.py)

   b. pandas (https://pandas.pydata.org/)

   c. pyyaml (https://pyyaml.org/wiki/PyYAMLDocumentation)

   d. jupyterlab (https://jupyter.org/)

      i. Note that this package also installs Jupyter Lab, a web-based developer's environment

2. Activate the virtual environment you want to install packages to (e.g., \`conda activate olca\`)

3. Install olca-ipc

   a. Note that the commands to install olca-ipc-2.0.2 (for OpenLCA version 2.0) is different from that of older versions of the same package. Make sure you download the package for the latest version: \`pip install -U olca-ipc\`.

      .. image:: image22.png
         :alt: A screenshot of a computer program Description automatically generated
         :width: 4.09465in
         :height: 2.91612in

4.  Continue the installations for all other necessary packages (`pyyaml`, \`pandas\`, and \`jupyterlab\`) using either \`conda\` or \`pip\`

    a. Note that \`conda install\` is a faster installer and is the preferred method to use in conda virtual environments; use \`pip install\` when conda fails.

       i.   Pyyaml: \`conda install pyyaml\` or \`pip install pyyaml\`

       ii.  Pandas: \`conda install pandas\` or \`pip install pandas\`

       iii. Jupyterlab: \`conda install jupyterlab\` or \`pip install jupyterlab\`

5. Test new package installation

    a. Open the Terminal and type \`jupyter lab\` to boot the Jupyter web-based developer's environment. It should open your default web browser.

    b. In case you receive an error (e.g., ModuleNotFoundError pictured below),

      .. image:: image23.png
         :alt: A close up of a message Description automatically generated
         :width: 5.43561in
         :height: 0.69897in

   c. Try installing the missing packages (e.g., \`conda install chardet\`) and re-run \`jupyter lab\`

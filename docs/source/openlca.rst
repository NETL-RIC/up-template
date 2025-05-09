The language of openLCA
=======================

The Python class, ``NetlOlca``, was created to be the workhorse behind the development of the new Jupyter Notebook Unit Process Template.
It provides a unified set of methods for communicating with openLCA either directly (e.g., via the IPC Service in openLCA v2) or indirectly (e.g., via an exported JSON-LD file).

The main concept for programming with openLCA is the **root entity** list (see table below).
This comes from GreenDelta's `openLCA schema <https://greendelta.github.io/olca-schema/>`_.

.. table:: openLCA root entity names and descriptions
    :widths: auto

    ================ ====================================================
    Entity Name      Description
    ================ ====================================================
    Actor            A person or organization
    Currency         Costing currency
    DQ System        Data quality system, a matrix of quality indicators
    EPD              Environmental Product System
    Flow             Everything that can be an input/output of a process
    Flow property    Quantity used to express amounts of flow
    Impact category  Life cycle impact assessment category
    Impact method    An impact assessment method
    Location         A location (e.g., country, state, or city)
    Parameter        Input or dependent global/process/impact parameter
    Process          Systematic organization or series of actions
    Product system   A product's supply chain (functional unit)
    Project          An openLCA project
    Result           A calculation result of a product system
    Social indicator An indicator for Social LCA
    Source           A literature reference
    Unit group       Group of units that can be inter-converted
    ================ ====================================================

The **schema** provides the definitions for openLCA's lossless data exchange format.
Other LCA schemas include:

-   EcoSpold 1 and EcoSpold II
-   SimaPro CSV
-   International Life Cycle Data (`ILCD <https://eplca.jrc.ec.europa.eu/ilcd.html>`_) system

Each entity has it's own set of instructions.
These instructions are translated to Python class definitions.
The simplest example is the Actor, or data associated with a person or organization.

In Python, the Actor root entity is defined by the following:

.. code-block:: python

    @dataclass
    class Actor:
        id: str
        address: str
        category: str
        city: str
        country: str
        description: str
        email: str
        last_change: str
        name: str
        tags: List[str]
        telefax: str
        telephone: str
        version: str
        website: str
        zip_code: str

The class definition above provides insight into the **attributes** of the root entity.
Attributes are variables associated with a class.
Just like other variables in Python, these must have a valid `data type <https://docs.python.org/3/library/datatypes.html>`_ (e.g., integer, string, dictionary, list, tuple, boolean).
The difference is that they are defined only within the scope of the class object and are accessed using the standard dot notation: ``obj.attribute``.

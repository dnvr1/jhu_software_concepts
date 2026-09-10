Module 2: GradCafe Web Scraping
========================================

The collector preserves source HTML, follows real pagination links, and stops
when a public source rejects access. It can import visible HTML captured after
the user completes normal browser verification. The cleaning adapter invokes
the actual instructor-supplied local model package and preserves source fields.

The completed collection contains 30,000 genuine records, and the supplied
local model produced two additional standardized fields for all 30,000 records
without changing source fields. See README.md, FINAL_VALIDATION.md, and
readme.txt in the project root for setup, evidence, commands, data definitions,
limitations, and submission requirements.

Scraper API
-----------

.. automodule:: scrape
   :members:
   :show-inheritance:

Cleaning API
------------

.. automodule:: clean
   :members:

Browser capture helper
----------------------

.. automodule:: capture_receiver
   :members:

Standalone normal-browser collector
-----------------------------------

.. automodule:: browser_collect
   :members:

Shared JSON storage
-------------------

.. automodule:: storage
   :members:

Narrative score evidence
------------------------

.. automodule:: comment_scores
   :members:

Independent source audit
------------------------

.. automodule:: audit_data
   :members:

Parallel local cleaning
-----------------------

.. automodule:: parallel_clean
   :members:

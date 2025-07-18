Contributing Documentation
==========================

If you notice missing or errorneous documentation, you can either
create an `issue on Github
<https://github.com/os-migrate/os-migrate/issues>`_, or you can create
a `pull request <https://github.com/os-migrate/os-migrate/pulls>`_
with the desired documentation changes.

Documentation sources in the repository:

-  The majority of documentation is located under ``docs/src`` folder.

-  Individual roles have a readme file under
   ``roles/<ROLE>/README.md`` (Ansible Galaxy requirement).

-  Modules are documented directly in their Python file
   ``/plugins/modules/<MODULE>.py`` (Ansible convention).


Rendering the Documentation
---------------------------

After you make your change and before you submit a pull request, it's
good to verify that the changes you made are getting rendered into
HTML correctly.

If you haven't yet built a toolbox container for OS Migrate
development, do so now:

::

   make toolbox-build


To build the documentation, run:

::

   ./toolbox/run make docs

You can inspect the rendered documentation by opening
``docs/src/_build/html/index.html`` in your web browser.

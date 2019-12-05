Migrating to the new ``tk-3dsmax`` engine
#########################################

You can easily adjust an existing configuration to use the new
``tk-3dsmax`` engine.

A migration example
===================

You can view the pull request where ``tk-config-default2`` was updated to use the new engine `here <https://github.com/shotgunsoftware/tk-config-default2/pull/67>`_.

To learn more about each changes, keep reading.

Updating the engine location
============================

You need update the ``location`` of the 3dsMax engine to point to the new engine named ``tk-3dsmax`` with a version of ``v1.0.0`` or greater.

For example:

.. code-block:: yaml

    tk-3dsmax:
        location:
            type: app_store
            name: tk-3dsmax
            version: v1.0.0

Updating the application hooks
==============================

You need to update the versions of the following applications that originally shipped with the ``Blur Python`` version of the ``tk-3dsmax`` hooks.

- ``tk-multi-loader2`` version ``v1.20.0`` or greater
- ``tk-multi-snapshot`` version ``v0.8.0`` or greater
- ``tk-multi-workfiles2`` version ``v0.12.0`` or greater

If you omit to update these applications you will get the following errors in your Toolkit logs:

.. code-block:: python

    Traceback (most recent call last):
      File "C:\Users\xxxxxx\install\core\python\tank\util\loader.py", line 55, in load_plugin
        module = imp.load_source(module_uid, plugin_file)
      File "C:\Users\xxxxxxx\bundle_cache\app_store\tk-multi-workfiles2\v0.11.14\hooks\scene_operation_tk-3dsmax.py", line 12, in <module>
        from Py3dsMax import mxs
    ImportError: No module named Py3dsMax

In addition, the hooks for those applications are now distributed with the engine instead of being distributed with the application. Therfore, you need to update the hooks for the following applications:

tk-multi-loader2
****************

You need to update ``actions_hook`` accordingly:

.. code-block:: yaml

    tk-multi-loader2:
        actions_hook: "{engine}/tk-multi-loader2/basic/scene_actions.py"

tk-multi-workfiles2
*******************

You need to update ``hook_scene_operation`` accordingly:

.. code-block:: yaml

    tk-multi-workfiles2:
        hook_scene_operation: "{engine}/tk-multi-workfiles2/basic/scene_operation.py"

tk-multi-snapshot
*****************

You need to update ``actions_hook`` accordingly:

.. code-block:: yaml

    tk-multi-snapshot:
        hook_scene_operation: "{engine}/tk-multi-snapshot/basic/scene_operation.py"

tk-multi-shotgunpanel
*********************

You need to update ``actions_hook`` accordingly:

.. code-block:: yaml

    tk-multi-shotgunpanel:
        actions_hook: "{engine}/tk-multi-shotgunpanel/basic/scene_actions.py"

tk-multi-publish2
*********************

There is no need to edit the hooks for the publisher. The default hook setting for the publisher searches for the hooks in the engine's ``hooks`` folder and this engine includes them at the expected location.

Updating your schema
====================

It is possible that your configuration uses ``defer_creation`` parameter. Make sure that any references to ``tk-3dsmaxplus`` are converted to ``tk-3dsmax``.

Updating Shotgun
****************

Visit the ``Software`` page on your Shotgun site. If you are a Shotgun administrator, you can access the page by clicking on the user icon at the top right on your site and selecting ``Software``. On this page, please make sure that there is a ``3ds Max`` software with the ``Engine`` column set to ``tk-3dsmax``.

.. image:: _static/software-entity.png

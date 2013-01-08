"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""

import tank
import sys
import os
import unicodedata



class MenuGenerator(object):
    """
    Menu generation functionality for 3dsmax
    """

    def __init__(self, engine, menu_adapter):
        self._engine = engine
        self._adapter = menu_adapter

    ##########################################################################################
    # public methods

    def create_menu(self):
        """
        Render the entire Tank menu.
        """
        # create main menu
        tank_menu = self._adapter.create_tank_menu()
        
        # now add the context item on top of the main menu
        context_menu = self._add_context_menu(tank_menu)
        
        # add a separator
        self._adapter.create_divider(tank_menu)
        
        # now enumerate all items and create menu objects for them
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            menu_items.append( AppCommand(self._adapter, cmd_name, cmd_details) )

        # now add favourites
        for fav in self._engine.get_setting("menu_favourites", []):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            
            # scan through all menu items
            for cmd in menu_items:                 
                if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                    # found our match!
                    cmd.add_command_to_menu(tank_menu)
                    # mark as a favourite item
                    cmd.favourite = True

        self._adapter.create_divider(tank_menu)
        
        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}
        
        for cmd in menu_items:
            
            if cmd.get_type() == "default":
                # normal menu item
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items" 
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

            elif cmd.get_type() == "context_menu":
                # context menu!
                cmd.add_command_to_menu(context_menu)

            else:
                # special, engine specific menu item.
                self._adapter.create_other( cmd.get_type(), cmd.name, cmd.callback, cmd.properties)           
        
        # now add all apps to main menu
        for app_name in sorted(commands_by_app.keys()):
            
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry for his app
                # make a sub menu and put all items in the sub menu
                m = self._adapter.create_submenu(tank_menu, app_name)
                for cmd in commands_by_app[app_name]:
                    cmd.add_command_to_menu(m)
            else:
                # this app only has a single entry. 
                # display that on the menu
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are already on the menu
                    cmd_obj.add_command_to_menu(tank_menu)
                    
        # finally request the creation of this menu
        self._adapter.render_menu()
        
    def destroy_menu(self):
        pass
        
    ##########################################################################################
    # context menu and UI

    def _add_context_menu(self, tank_menu):
        """
        Adds a context menu which displays the current context
        """        
        
        ctx = self._engine.context
        
        if ctx.entity is None:
            # project-only!
            ctx_name = "%s" % ctx.project["name"]
        
        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. Shot ABC_123
            ctx_name = "%s %s" % (ctx.entity["type"], ctx.entity["name"])

        else:
            # we have either step or task
            task_step = None
            if ctx.step:
                task_step = ctx.step.get("name")
            if ctx.task:
                task_step = ctx.task.get("name")
            
            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "%s, %s %s" % (task_step, ctx.entity["type"], ctx.entity["name"])
        
        # create the menu object
        ctx_menu = self._adapter.create_submenu(tank_menu, ctx_name)
        self._adapter.create_item(ctx_menu, "Jump to Shotgun", self._jump_to_sg)
        self._adapter.create_item(ctx_menu, "Jump to File System", self._jump_to_fs)
        self._adapter.create_divider(ctx_menu)
        
        return ctx_menu
                        
    def _jump_to_sg(self):

        if self._engine.context.entity is None:
            # project-only!
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       "Project", 
                                       self._engine.context.project["id"])
        else:
            # entity-based
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       self._engine.context.entity["type"], 
                                       self._engine.context.entity["id"])
        
        self._adapter.launch_web_browser(url)
        
    def _jump_to_fs(self):
        
        """
        Jump from context to FS
        """
        
        if self._engine.context.entity:
            paths = self._engine.tank.paths_from_entity(self._engine.context.entity["type"], 
                                                     self._engine.context.entity["id"])
        else:
            paths = self._engine.tank.paths_from_entity(self._engine.context.project["type"], 
                                                     self._engine.context.project["id"])
        
        # launch one window for each location on disk
        # todo: can we do this in a more elegant way?
        for disk_location in paths:
                
            # get the setting        
            system = sys.platform
            
            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)
            
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
        
            
                                
class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    
    def __init__(self, adapter, name, command_dict):        
        self._adapter = adapter
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False
        
        
    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None
        
    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None
        
        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name
            
        return None
                
    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")
        
    def add_command_to_menu(self, menu):
        """
        Adds an app command to the menu
        """
        icon = self.properties.get("icon")
        self._adapter.create_item(menu, self.name, self.callback, icon)


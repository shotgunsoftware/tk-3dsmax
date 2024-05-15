# Copyright (c) 2024 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Menu handling for 3ds Max
"""
from pymxs import runtime as rt

from .menu_generation_menuman import MenuGenerator_menuMan, AppCommand


class MenuGenerator(MenuGenerator_menuMan):
    """
    Menu generation functionality for 3dsmax 2025+
    """

    def create_menu(self):
        """
        Create the Shotgun Menu
        """
        # Create the main menu

        # callbacks initial dict
        cmd_fn_list = {
            2001: self._jump_to_sg,
            2002: self._jump_to_fs,
        }

        # enumerate all items and create menu objects for them
        cmd_items = []
        for idx, (cmd_name, cmd_details) in enumerate(self._engine.commands.items()):
            code = idx + 1000
            command = AppCommand2025(cmd_name, cmd_details, code)
            cmd_items.append(command)
            cmd_fn_list[code] = command.execute

        # start with context menu
        context_items = []
        for cmd in cmd_items:
            if cmd.get_type() == "context_menu":
                context_items.append(cmd)

        # now favourites
        favorites = []
        for fav in self._engine.get_setting("menu_favourites", []):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            # scan through all menu items
            for cmd in cmd_items:
                if (
                    cmd.get_app_instance_name() == app_instance_name
                    and cmd.name == menu_name
                ):
                    # found our match!
                    favorites.append(cmd)
                    # mark as a favourite item
                    cmd.favourite = True

        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}
        for cmd in cmd_items:
            if cmd.get_type() != "context_menu":
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items"
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

        # Define 3dsmax 2025 menu callbacks
        def populate_apps_menu(menuroot):
            for app_name in sorted(commands_by_app.keys()):
                if len(commands_by_app[app_name]) > 1:
                    # make a sub menu and put all items in the sub menu
                    submenu = menuroot.addsubmenu(app_name)
                    for cmd in commands_by_app[app_name]:
                        submenu.additem(cmd.code, cmd.name)
                else:
                    cmd_obj = commands_by_app[app_name][0]
                    if not cmd_obj.favourite:
                        # skip favourites since they are alreay on the menu
                        menuroot.additem(cmd_obj.code, cmd_obj.name)

        def populate_favs_menu(menuroot):
            for cmd in favorites:
                menuroot.additem(cmd.code, cmd.name)

        def populate_cntx_menu(menuroot):
            menuroot.additem(2001, "Jump to Flow Production Tracking")
            menuroot.additem(2002, "Jump to File System")
            for cmd in context_items:
                menuroot.additem(cmd.code, cmd.name)

        def menu_item_selected(itemid):
            cmd_fn_list[itemid]()

        # let this be called from mxs by injecting it in the global maxscript namespace
        rt.populate_apps_menu = populate_apps_menu
        rt.populate_favs_menu = populate_favs_menu
        rt.populate_cntx_menu = populate_cntx_menu
        rt.menu_item_selected = menu_item_selected

        mxswrapper = """
        macroscript Python_Apps_Action_Item category:"Menu Apps Category" buttonText:"Toolkit Apps"
        (
            on populateDynamicMenu menuRoot do
            (
                populate_apps_menu menuRoot
            )
            on dynamicMenuItemSelected id do
            (
                menu_item_selected id
            )
        )
        macroscript Python_Favs_Action_Item category:"Menu Favs Category" buttonText:"Favorites"
        (
            on populateDynamicMenu menuRoot do
            (
                populate_favs_menu menuRoot
            )
            on dynamicMenuItemSelected id do
            (
                menu_item_selected id
            )
        )
        macroscript Python_Cntx_Action_Item category:"Menu Cntx Category" buttonText:"{context_name}"
        (
            on populateDynamicMenu menuRoot do
            (
                populate_cntx_menu menuRoot
            )
            on dynamicMenuItemSelected id do
            (
                menu_item_selected id
            )
        )
        """.format(
            context_name=str(self._engine.context)
        )
        rt.execute(mxswrapper)

        def create_menu_callback():
            menumgr = rt.callbacks.notificationparam()
            mainmenubar = menumgr.mainmenubar
            newsubmenu = mainmenubar.createsubmenu(
                rt.genguid(), self._engine.MENU_LABEL, beforeid=self._engine.HELPMENU_ID
            )
            newsubmenu.createaction(
                rt.genguid(), 647394, "Python_Cntx_Action_Item`Menu Cntx Category"
            )
            newsubmenu.createaction(
                rt.genguid(), 647394, "Python_Favs_Action_Item`Menu Favs Category"
            )
            newsubmenu.createseparator(rt.genguid())
            newsubmenu.createaction(
                rt.genguid(), 647394, "Python_Apps_Action_Item`Menu Apps Category"
            )

        MENU_DEMO_SCRIPT = rt.name(self._menu_var)
        rt.callbacks.removescripts(id=MENU_DEMO_SCRIPT)
        rt.callbacks.addscript(
            rt.name("cuiRegisterMenus"), create_menu_callback, id=MENU_DEMO_SCRIPT
        )

    def destroy_menu(self):
        rt.callbacks.removescripts(id=rt.name(self._menu_var))
        iCuiMenuMgr = rt.MaxOps.GetICuiMenuMgr()
        iCuiMenuMgr.LoadConfiguration(iCuiMenuMgr.GetCurrentConfiguration())


class AppCommand2025(AppCommand):
    def __init__(self, name, command_dict, code):
        self.code = code
        super().__init__(name, command_dict)

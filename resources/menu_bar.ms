-- Copyright (c) 2013 Shotgun Software Inc.
-- 
-- CONFIDENTIAL AND PROPRIETARY
-- 
-- This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
-- Source Code License included in this distribution package. See LICENSE.
-- By accessing, using, copying or modifying this work you indicate your 
-- agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
-- not expressly granted therein are reserved by Shotgun Software Inc.


rollout SgtkMenuBar "Shotgun"
(

    button btn_work_area "Current Work Area" width: 100 height: 24 pos:[41,5] border:false
    button btn_apps "Current Apps" width: 100 height: 24 pos:[147,5] border: false

    on btn_work_area pressed do
    (   
        -- get the coordinates for our window
        dialog_pos = GetDialogPos SgtkMenuBar
        -- call home to python
        tank = python.import "tank"
        current_engine = tank.platform.current_engine()
        current_engine.max_callback_work_area_menu dialog_pos
    )
    on btn_apps pressed do
    (   
        -- get the coordinates for our window
        dialog_pos = GetDialogPos SgtkMenuBar
        -- call home to python
        tank = python.import "tank"
        current_engine = tank.platform.current_engine()
        current_engine.max_callback_apps_menu dialog_pos
    )

)

--------------------------------------------------------------------------------

Environment = dotNetClass "System.Environment"
bg_path = Environment.GetEnvironmentVariable "TANK_MENU_BG_LOCATION"
bg = openBitMap bg_path

createDialog SgtkMenuBar  bitmap: bg width: 252 height: 34
cui.RegisterDialogBar SgtkMenuBar
cui.DockDialogBar SgtkMenuBar #cui_dock_bottom


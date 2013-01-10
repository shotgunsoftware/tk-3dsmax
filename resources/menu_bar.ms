
--Copyright (c) 2012 Shotgun Software, Inc
--------------------------------------------------------------------------------


rollout TankMenuBar "Tank"
(

    button btn_work_area "Current Work Area" width: 110 height: 30 pos:[110,12] border:false
    button btn_apps "Current Apps" width: 110 height: 30 pos:[230,12] border: false

    on btn_work_area pressed do
    (   
        -- get the coordinates for our window
        dialog_pos = GetDialogPos TankMenuBar
        -- call home to python
        tank = python.import "tank"
        current_engine = tank.platform.current_engine()
        current_engine.max_callback_work_area_menu dialog_pos
    )
    on btn_apps pressed do
    (   
        -- get the coordinates for our window
        dialog_pos = GetDialogPos TankMenuBar
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

createDialog TankMenuBar  bitmap: bg width: 353 height: 50
cui.RegisterDialogBar TankMenuBar
cui.DockDialogBar TankMenuBar #cui_dock_bottom


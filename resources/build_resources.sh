#!/usr/bin/env bash
# 
# Copyright (c) 2008 Shotgun Software, Inc
# ----------------------------------------------------

echo "building user interfaces..."
pyside-uic --from-imports app_menu.ui > ../python/tk_3dsmax/ui/app_menu.py
pyside-uic --from-imports context_menu.ui > ../python/tk_3dsmax/ui/context_menu.py

#echo "building resources..."
pyside-rcc resources.qrc > ../python/tk_3dsmax/ui/resources_rc.py

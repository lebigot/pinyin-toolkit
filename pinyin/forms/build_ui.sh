#!/bin/bash

if [ ! -d "designer" ]; then
    echo "Please run this from the project root"
    exit
fi

pyuic=`which pyuic4`
pyrcc=`which pyrcc4`

# Clean the directory up
rm -rf scratch generated

# Make directories
mkdir scratch
mkdir generated

# Build each form
echo "Generating forms.."
for file in designer/*.ui; do
    pythonfile=$(echo $file | sed -e 's%\.ui%\.py%; s%designer/%generated/%')
    modulename=$(echo $pythonfile | sed -e 's%\.py%%; s%generated/%%')
    
    echo " * $pythonfile"
    $pyuic $file -o $pythonfile
    echo "	\"$modulename\"," >> scratch/list
    echo "import $modulename" >> scratch/imports
    
    # Munge the output to not use translation
    perl -e 's/QtGui.QApplication.translate\(".*?", /_(/; s/, None, QtGui.*/))/' $pythonfile
    
    # Remove the 'created' time, to avoid flooding the version control system
    perl -e 's/^# Created:.*$//' $pythonfile
done

# Build __init__.py
INIT="generated/__init__.py"
echo "# This file auto-generated by build_ui.sh. Don't edit." > $INIT
echo "__all__ = [" >> $INIT #
cat scratch/list >> $INIT   # Module list called __all__
echo "]" >> $INIT           #
echo "import icons_rc" >> $INIT #
cat scratch/imports >> $INIT    # One import per module in the list

# Build resources
echo "Building resources.."
(cd icons && $pyrcc icons.qrc -o ../generated/icons_rc.py)

# Destroy scratch directory
rm -rf scratch

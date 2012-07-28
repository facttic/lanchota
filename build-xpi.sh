#! /bin/bash

BUILD_DIR=`pwd`/"build"
PLUGIN_DIR=`pwd`/"lanchota"

function build
{
TMP_DIRECTORY="`mktemp -d`"
echo "Copying files from pos directory to " $TMP_DIRECTORY
cp -R $PLUGIN_DIR/* $TMP_DIRECTORY
cd $TMP_DIRECTORY
echo "Creating new extension"
zip -r $BUILD_DIR/lanchota.xpi *
}

build

QT += core gui widgets svg dbus
CONFIG += c++20 console
CONFIG -= app_bundle
DEFINES += HEADLESS
TEMPLATE = app
TARGET = tray-appearance
JDSP_SOURCE = $$(JDSP_TEST_SOURCE_TREE)
isEmpty(JDSP_SOURCE): error("Set JDSP_TEST_SOURCE_TREE to the patched upstream source")
INCLUDEPATH += $$JDSP_SOURCE/src $$JDSP_SOURCE/src/audio/base
SOURCES += $$PWD/tray_appearance.cpp \
    $$JDSP_SOURCE/src/interface/TrayIcon.cpp \
    $$JDSP_SOURCE/src/config/AppConfig.cpp \
    $$JDSP_SOURCE/src/config/ConfigContainer.cpp \
    $$JDSP_SOURCE/src/config/ConfigIO.cpp \
    $$JDSP_SOURCE/src/data/PresetProvider.cpp
HEADERS += $$JDSP_SOURCE/src/interface/TrayIcon.h $$JDSP_SOURCE/src/config/AppConfig.h
RESOURCES += $$JDSP_SOURCE/resources/resources.qrc

QT += core gui widgets svg
CONFIG += c++20 console
CONFIG -= app_bundle
TEMPLATE = app
TARGET = interface-readability
JDSP_SOURCE = $$(JDSP_TEST_SOURCE_TREE)
isEmpty(JDSP_SOURCE): error("Set JDSP_TEST_SOURCE_TREE to the patched upstream source")
include($$JDSP_SOURCE/src/subprojects/GraphicEQWidget/GraphicEQWidget/GraphicEQWidget.pri)
include($$JDSP_SOURCE/src/subprojects/FlatTabWidget/FlatTabWidget/FlatTabWidget.pri)
SOURCES += $$PWD/interface_readability.cpp

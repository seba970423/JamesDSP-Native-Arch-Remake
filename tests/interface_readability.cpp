#include "GraphicEQFilterGUI.h"
#include "GraphicEQFilterGUIView.h"
#include "widgets/FrequencyPlotHRuler.h"
#include "flattabwidget.h"
#include <QApplication>
#include <QRadioButton>
#include <QScrollBar>
#include <QStyle>
#include <QTableWidget>
#include <QVBoxLayout>
#include <cassert>
#include <iostream>

static void checkLabels(GraphicEQFilterGUI& graph) {
    auto* ruler = graph.findChild<FrequencyPlotHRuler*>();
    auto* view = graph.findChild<FrequencyPlotView*>();
    assert(ruler && view && ruler->height() >= ruler->fontMetrics().height());
    const auto labels = ruler->tickLabels();
    assert(labels.size() >= 2);
    for (int i = 0; i < labels.size(); ++i) {
        assert(labels[i].rect.left() >= view->viewportMargins().left());
        assert(labels[i].rect.right() <= ruler->width());
        assert(labels[i].rect.width() >= ruler->fontMetrics().horizontalAdvance(labels[i].text));
        for (int j = i + 1; j < labels.size(); ++j)
            assert(!labels[i].rect.intersects(labels[j].rect));
    }
}

int main(int argc, char** argv) {
    qputenv("QT_QPA_PLATFORM", "offscreen");
    QApplication app(argc, argv);
    const auto baseFont = app.font();
    for (bool dark : {false, true}) {
        auto palette = app.style()->standardPalette();
        const QColor text = dark ? QColor("#eeeeee") : QColor("#202020");
        palette.setColor(QPalette::Window, dark ? QColor("#292929") : QColor("#f3f3f3"));
        palette.setColor(QPalette::Base, dark ? QColor("#202020") : QColor("#ffffff"));
        palette.setColor(QPalette::WindowText, text);
        palette.setColor(QPalette::Text, text);
        palette.setColor(QPalette::ButtonText, text);
        palette.setColor(QPalette::Disabled, QPalette::WindowText, QColor("#bcbcbc"));
        app.setPalette(palette);
        QWidget window;
        auto* layout = new QVBoxLayout(&window);
        FlatTabWidget tabs;
        tabs.setAnimatePageChange(false);
        for (const QString& title : {"Bass/Misc", "Sound Positioning", "Reverb", "Equalizer", "Convolver", "DDC", "Liveprog"})
            tabs.addPage(title, new QWidget);
        auto* graph = new GraphicEQFilterGUI;
        graph->setEnableSwitchVisible(true);
        graph->setAutoEqAvailable(true);
        tabs.addPage("Graphic EQ", graph);
        layout->addWidget(&tabs);
        tabs.setCurrentTab(7);
        graph->load("GraphicEQ: 20 0; 25 0; 31.5 0; 40 0; 50 0; 63 0; 80 0; 100 0; 125 0; 160 0; 200 0; 250 0; 315 0; 400 0; 500 0; 630 0; 800 0; 1000 0; 1250 0; 1600 0; 2000 0; 2500 0; 3150 0; 4000 0; 5000 0; 6300 0; 8000 0; 10000 0; 12500 0; 16000 0; 20000 0");
        graph->loadPreferences({{"scrollX", 102}, {"scrollY", 825}, {"zoomX", 0.561}, {"zoomY", 3.822}});
        QString initial;
        graph->store(initial);
        auto* bandTable = graph->findChild<QTableWidget*>("tableWidget");
        assert(bandTable && bandTable->rowCount() == 31);
        for (int row = 0; row < bandTable->rowCount(); ++row) {
            assert(bandTable->item(row, 0)->flags().testFlag(Qt::ItemIsEnabled));
            assert(!bandTable->item(row, 0)->flags().testFlag(Qt::ItemIsEditable));
        }
        for (int points : {9, 12, 16}) {
            auto font = baseFont;
            font.setPointSize(points);
            window.setFont(font);
            for (const auto size : {QSize(685, 400), QSize(1000, 650)}) {
                window.resize(size);
                window.show();
                tabs.redrawTabBar();
                for (int n = 0; n < 3; ++n) app.processEvents();
                for (int tab = 0; tab < 8; ++tab)
                    assert(tabs.getItem(tab).label->color() == text);
                checkLabels(*graph);
                auto* view = graph->findChild<FrequencyPlotView*>();
                view->zoom(600, 0, view->viewport()->width() / 2, 0);
                app.processEvents();
                checkLabels(*graph);
                view->zoom(-600, 0, view->viewport()->width() / 2, 0);
                app.processEvents();
                checkLabels(*graph);
                QString after;
                graph->store(after);
                assert(after == initial);
            }
        }
        window.setFont(baseFont);
        window.resize(685, 400);
        for (int n = 0; n < 3; ++n) app.processEvents();
        auto* view = graph->findChild<FrequencyPlotView*>();
        view->scene()->setZoom(0.561, 3.822);
        view->horizontalScrollBar()->setValue(102);
        view->verticalScrollBar()->setValue(825);
        for (int n = 0; n < 3; ++n) app.processEvents();
        checkLabels(*graph);
        const auto output = qEnvironmentVariable(dark ? "JDSP_TEST_EQ_DARK_IMAGE" : "JDSP_TEST_EQ_IMAGE");
        if (!output.isEmpty()) assert(window.grab().save(output));
        for (const auto* mode : {"radioButton15", "radioButtonVar", "radioButton31"}) {
            graph->findChild<QRadioButton*>(mode)->setChecked(true);
            app.processEvents();
            checkLabels(*graph);
        }
    }
    std::cout << "EQ label spacing, font-sized rulers, band preservation and enabled-tab contrast passed.\n";
}

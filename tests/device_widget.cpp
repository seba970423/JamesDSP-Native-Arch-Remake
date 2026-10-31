#include "NativeDeviceWidget.h"
#include "ui_SettingsForm.h"
#include <QApplication>
#include <QPushButton>
#include <QScrollArea>
#include <QScrollBar>
#include <QTemporaryDir>
#include <QVBoxLayout>
#include <cassert>
#include <iostream>

int main(int argc, char** argv) {
    qputenv("QT_QPA_PLATFORM", "offscreen");
    QApplication app(argc, argv);
    QWidget form;
    Ui::SettingsFragment ui;
    ui.setupUi(&form);
    QTemporaryDir directory;
    DevicePolicy policy(directory.filePath("device_rules.json"));
    IOutputDevice laptop("alsa_card.laptop", "Built-in audio with a long device name", "analog-output-speaker", "Speakers");
    laptop.id = 1;
    laptop.output_routes = {Route("analog-output-speaker", "Speakers"), Route("analog-output-headphones", "Headphones")};
    IOutputDevice speaker("bluez_card.JBL", "JBL GO 4", "a2dp-output", "Bluetooth audio");
    speaker.id = 2;
    IOutputDevice laptopSink, speakerSink;
    laptopSink.id = 100; laptopSink.device_id = 1;
    speakerSink.id = 200; speakerSink.device_id = 2;
    int changes = 0;
    auto* widget = new NativeDeviceWidget(&policy, [=] { return std::vector<IOutputDevice>{laptop, speaker}; },
        [=] { return std::vector<IOutputDevice>{laptopSink, speakerSink}; }, [&] { ++changes; }, &form);
    ui.devices_group->hide();
    NativeDeviceWidget::installOnPage(ui.devices, widget);
    ui.stackedWidget->setCurrentWidget(ui.devices);
    ui.selector->setCurrentItem(ui.selector->topLevelItem(3));
    auto* table = widget->findChild<QTableWidget*>("nativeDeviceRules");
    assert(table && table->rowCount() == 5);
    auto set = [&](const QString& device, const QString& route, bool enabled) {
        for (int row = 0; row < table->rowCount(); ++row) {
            auto* item = table->item(row, 2);
            if (item->data(Qt::UserRole).toString() == device && item->data(Qt::UserRole + 1).toString() == route) {
                item->setCheckState(enabled ? Qt::Checked : Qt::Unchecked);
                return;
            }
        }
        assert(false && "device/route checkbox is missing");
    };
    set("alsa_card.laptop", "analog-output-speaker", true);
    assert(changes == 1);
    assert(policy.enabled("alsa_card.laptop", "analog-output-speaker"));
    assert(!policy.enabled("alsa_card.laptop", "analog-output-headphones"));
    set("bluez_card.JBL", "*", true);
    assert(policy.enabled("bluez_card.JBL", "a2dp-output"));
    set("bluez_card.JBL", "a2dp-output", false);
    assert(!policy.enabled("bluez_card.JBL", "a2dp-output"));
    assert(policy.enabled("alsa_card.laptop", "analog-output-speaker"));
    auto* scroll = form.findChild<QScrollArea*>("nativeDevicesScroll");
    auto* status = widget->findChild<QLabel*>("nativeKernelStatus");
    assert(scroll && status && widget->parentWidget() == scroll->widget());
    auto* refreshButton = widget->findChild<QPushButton*>("nativeDeviceRefresh");
    assert(refreshButton && refreshButton->text() == QStringLiteral("Refresh devices and status"));
    assert(!refreshButton->text().contains('\n'));
    status->setText("Kernel: PREEMPT_RT\nInstalled profile: PREEMPT_RT\nReal-time threads: 2");
    const auto originalFont = app.font();
    for (int points : {9, 12, 16}) {
        auto font = originalFont;
        font.setPointSize(points);
        form.setFont(font);
        for (const auto size : {QSize(685, 365), QSize(700, 450), QSize(1000, 650)}) {
            form.resize(size);
            form.show();
            for (int i = 0; i < 3; ++i) app.processEvents();
            if (scroll->horizontalScrollBar()->maximum() != 0) {
                const auto printWidget = [&](const char* name, QWidget* child) {
                    const auto hint = child->sizeHint();
                    const auto minimum = child->minimumSizeHint();
                    const auto layoutMinimum = child->layout() ? child->layout()->minimumSize().width() : -1;
                    std::cerr << "  " << name << ": width=" << child->width()
                              << " minWidth=" << child->minimumWidth()
                              << " minHint=" << minimum.width()
                              << " sizeHint=" << hint.width()
                              << " layoutMin=" << layoutMinimum
                              << " visible=" << child->isVisible() << std::endl;
                };
                printWidget("scroll content", scroll->widget());
                printWidget("NativeDeviceWidget", widget);
                printWidget("device rules table", table);
                printWidget("blocklist group", ui.blocklistBox);
                printWidget("blocklist description", ui.label_4);
                printWidget("allowlist checkbox", ui.blocklistInvert);
                printWidget("clear list button", ui.blocklistClear);
                printWidget("new devices checkbox", widget->findChild<QCheckBox*>("nativeNewDeviceEffects"));
                printWidget("refresh button", widget->findChild<QPushButton*>("nativeDeviceRefresh"));
                std::cerr << "Devices page horizontal overflow: font=" << points << "pt"
                          << ", requested=" << size.width() << "x" << size.height()
                          << ", actual=" << form.width() << "x" << form.height()
                          << ", viewport=" << scroll->viewport()->width()
                          << ", content=" << scroll->widget()->width()
                          << ", content minimum=" << scroll->widget()->minimumWidth()
                          << ", device controls minimum=" << widget->minimumWidth()
                          << ", blocklist minimum=" << ui.blocklistBox->minimumWidth()
                          << ", scrollbar maximum=" << scroll->horizontalScrollBar()->maximum()
                          << std::endl;
            }
            assert(scroll->horizontalScrollBar()->maximum() == 0);
            assert(refreshButton->fontMetrics().horizontalAdvance(refreshButton->text()) + 12 <= refreshButton->width());
            for (int i = 0; i < widget->layout()->count(); ++i) {
                auto* control = widget->layout()->itemAt(i)->widget();
                assert(control && widget->rect().contains(control->geometry()));
                if (auto* label = qobject_cast<QLabel*>(control))
                    assert(label->height() >= label->heightForWidth(label->width()));
                for (int j = i + 1; j < widget->layout()->count(); ++j)
                    assert(!control->geometry().intersects(widget->layout()->itemAt(j)->geometry()));
            }
            assert(ui.blocklistBox->parentWidget() == scroll->widget());
            assert(!widget->geometry().intersects(ui.blocklistBox->geometry()));
            scroll->ensureWidgetVisible(ui.blocklistClear);
            app.processEvents();
            const QRect clearButton(ui.blocklistClear->mapTo(scroll->viewport(), QPoint()), ui.blocklistClear->size());
            assert(scroll->viewport()->rect().intersects(clearButton));
        }
    }
    form.setFont(originalFont);
    form.resize(685, 365);
    scroll->verticalScrollBar()->setValue(0);
    for (int i = 0; i < 3; ++i) app.processEvents();
    const auto image = qEnvironmentVariable("JDSP_TEST_WIDGET_IMAGE");
    if (!image.isEmpty()) assert(form.grab().save(image));
    ui.stackedWidget->setCurrentWidget(ui.session);
    ui.selector->setCurrentItem(ui.selector->topLevelItem(5));
    ui.selector->expandItem(ui.selector->topLevelItem(5));
    ui.systray_unsupported->hide();
    ui.systray_r_showtray->setChecked(true);
    ui.trayIconAppearance->addItems({"Automatic", "Light (for dark panels)",
                                   "Dark (for light panels)", "Color (app icon)"});
    for (int points : {9, 12, 16}) {
        auto font = originalFont;
        font.setPointSize(points);
        form.setFont(font);
        for (const auto size : {QSize(685, 365), QSize(700, 450), QSize(1000, 650)}) {
            form.resize(size);
            for (int i = 0; i < 3; ++i) app.processEvents();
            if (ui.traySettingsScroll->horizontalScrollBar()->maximum() != 0) {
                std::cerr << "Tray horizontal overflow: font=" << points << "pt"
                          << ", requested=" << size.width() << "x" << size.height()
                          << ", viewport=" << ui.traySettingsScroll->viewport()->width()
                          << ", content=" << ui.traySettingsContents->width()
                          << ", maximum=" << ui.traySettingsScroll->horizontalScrollBar()->maximum()
                          << std::endl;
                const auto dump = [](const char* name, QWidget* child) {
                    std::cerr << "  " << name << ": width=" << child->width()
                              << " minHint=" << child->minimumSizeHint().width()
                              << " sizeHint=" << child->sizeHint().width() << std::endl;
                };
                dump("tray content", ui.traySettingsContents);
                dump("tray group", ui.systray_box);
                dump("exit radio", ui.systray_r_none);
                dump("tray radio", ui.systray_r_showtray);
                dump("autostart checkbox", ui.systray_minOnBoot);
                dump("appearance group", ui.trayAppearanceBox);
                dump("appearance combo", ui.trayIconAppearance);
                dump("appearance help", ui.trayAppearanceHelp);
            }
            assert(ui.traySettingsScroll->horizontalScrollBar()->maximum() == 0);
            assert(ui.traySettingsContents->rect().contains(ui.trayAppearanceBox->geometry()));
            assert(!ui.trayAppearanceBox->geometry().intersects(ui.systray_box->geometry()));
            assert(ui.trayAppearanceHelp->height() >=
                   ui.trayAppearanceHelp->heightForWidth(ui.trayAppearanceHelp->width()));
            assert(ui.trayAppearanceBox->rect().contains(ui.trayIconAppearance->geometry()));
            ui.traySettingsScroll->ensureWidgetVisible(ui.trayIconAppearance);
            app.processEvents();
            const QRect choiceRect(ui.trayIconAppearance->mapTo(ui.traySettingsScroll->viewport(), QPoint()),
                                   ui.trayIconAppearance->size());
            assert(ui.traySettingsScroll->viewport()->rect().contains(choiceRect));
        }
    }
    form.setFont(originalFont);
    form.resize(685, 365);
    ui.traySettingsScroll->verticalScrollBar()->setValue(0);
    for (int i = 0; i < 3; ++i) app.processEvents();
    const auto trayImage = qEnvironmentVariable("JDSP_TEST_TRAY_IMAGE");
    if (!trayImage.isEmpty()) assert(form.grab().save(trayImage));
    std::cout << "Device policy controls, Devices and Tray Settings layouts passed at 3 sizes and 3 font sizes.\n";
}

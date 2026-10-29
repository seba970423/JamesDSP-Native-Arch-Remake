// Exercise the real tray icon, configuration notifications and saved preference.
#include "interface/TrayIcon.h"
#include "config/AppConfig.h"
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QMenu>
#include <QTemporaryDir>
#include <cassert>
#include <iostream>

void Log::debug(const QString&, util::source_location) {}
void Log::error(const QString&, util::source_location) {}

static void settle() {
    QCoreApplication::processEvents();
    QCoreApplication::sendPostedEvents(nullptr, QEvent::DeferredDelete);
}

static QColor renderedColor(TrayIcon& tray) {
    settle();
    const auto icons = tray.findChildren<QSystemTrayIcon*>();
    assert(icons.size() == 1);
    const QImage image = icons.front()->icon().pixmap(48, 48).toImage();
    assert(!image.isNull());
    int red = 0, green = 0, blue = 0, count = 0;
    for (int y = 0; y < image.height(); ++y)
        for (int x = 0; x < image.width(); ++x) {
            const QColor pixel = image.pixelColor(x, y);
            if (pixel.alpha() < 200) continue;
            red += pixel.red(); green += pixel.green(); blue += pixel.blue(); ++count;
        }
    assert(count > 20);
    return QColor(red / count, green / count, blue / count);
}

static void setBackground(QApplication& app, bool dark) {
    auto palette = app.palette();
    palette.setColor(QPalette::Window, dark ? QColor("#202020") : QColor("#f5f5f5"));
    app.setPalette(palette);
    settle();
}

int main(int argc, char** argv) {
    QTemporaryDir directory;
    assert(directory.isValid());
    qputenv("QT_QPA_PLATFORM", "offscreen");
    qputenv("XDG_CONFIG_HOME", directory.path().toUtf8());
    QApplication app(argc, argv);
    auto& config = AppConfig::instance();
    QDir().mkpath(config.getPath());
    assert(config.get<QString>(AppConfig::TrayIconAppearance) == "auto");

    const auto themeRoot = directory.path() + "/icons";
    QDir().mkpath(themeRoot + "/fixture/22x22/status");
    QFile index(themeRoot + "/fixture/index.theme");
    assert(index.open(QIODevice::WriteOnly));
    index.write("[Icon Theme]\nName=Fixture\nDirectories=22x22/status\n"
                "[22x22/status]\nSize=22\nType=Fixed\nContext=Status\n");
    index.close();
    QIcon::setThemeSearchPaths({themeRoot});
    QIcon::setFallbackSearchPaths({});
    QIcon::setFallbackThemeName("fixture");
    QIcon::setThemeName("fixture");
    assert(!QIcon::hasThemeIcon("jamesdsp-tray"));

    TrayIcon tray;
    tray.setTrayVisible(false);
    // Match the palette notification connection used by the real MainWindow.
    QObject::connect(&app, &QApplication::paletteChanged, &tray, &TrayIcon::updateTheme);
    setBackground(app, true);
    assert(renderedColor(tray).lightness() > 180);
    setBackground(app, false);
    assert(renderedColor(tray).lightness() < 100);

    // Supply a deliberately red theme icon. Explicit choices must bypass it.
    QImage themed(22, 22, QImage::Format_ARGB32);
    themed.fill(Qt::red);
    assert(themed.save(themeRoot + "/fixture/22x22/status/jamesdsp-tray.png"));
    QIcon::setThemeName("refresh");
    QIcon::setThemeName("fixture");
    assert(QIcon::hasThemeIcon("jamesdsp-tray"));
    tray.updateTheme();
    const auto themeColor = renderedColor(tray);
    assert(themeColor.red() > 200 && themeColor.green() < 30);

    for (const QString mode : {"light", "dark", "color"}) {
        config.set(AppConfig::TrayIconAppearance, mode);
        const QColor color = renderedColor(tray);
        if (mode == "light") assert(color.lightness() > 180);
        else if (mode == "dark") assert(color.lightness() < 100);
        else assert(qMax(color.red(), color.blue()) - color.green() > 30);
        // App palette changes cannot undo a manual choice.
        setBackground(app, true);
        assert(renderedColor(tray) == color);
        setBackground(app, false);
        assert(renderedColor(tray) == color);
        // Rebuilding the tray menu recreates the native tray icon.
        tray.updateTrayMenu(tray.buildDefaultActions());
        assert(renderedColor(tray) == color);
        AppConfig restored;
        assert(restored.get<QString>(AppConfig::TrayIconAppearance) == mode);
    }
    config.set(AppConfig::TrayIconAppearance, "auto");
    assert(renderedColor(tray) == themeColor);
    config.set(AppConfig::TrayIconAppearance, "unrecognized-value");
    assert(renderedColor(tray) == themeColor);
    std::cout << "Tray appearance: theme, palette fallback, manual overrides, live updates and persistence passed.\n";
}

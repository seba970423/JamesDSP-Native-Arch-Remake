#include "DevicePolicy.h"
#include <QCoreApplication>
#include <QTemporaryDir>
#include <QFile>
#include <cassert>

int main(int argc, char** argv) {
    QCoreApplication app(argc, argv);
    QTemporaryDir directory;
    const auto path = directory.filePath("device_rules.json");
    DevicePolicy policy(path);
    assert(!policy.enabled("bluez_card.JBL", "a2dp-output"));
    assert(policy.setEnabled("alsa_card.laptop", "*", "Laptop", true));
    assert(policy.setEnabled("alsa_card.laptop", "analog-output-speaker", "Speakers", false));
    assert(policy.enabled("alsa_card.laptop", "analog-output-headphones"));
    assert(!policy.enabled("alsa_card.laptop", "analog-output-speaker"));
    assert(policy.setEnabled("bluez_card.headset", "*", "Headphones", true));
    DevicePolicy reconnected(path); // new instance, different runtime node IDs never enter the file
    assert(reconnected.enabled("bluez_card.headset", "a2dp-output"));
    assert(reconnected.enabled("bluez_card.headset", "headset-output"));
    assert(!reconnected.enabled("bluez_card.JBL", "a2dp-output"));
    assert(reconnected.setDefaultEnabled(true));
    assert(reconnected.enabled("unknown", "*"));
    assert(!reconnected.enabled("alsa_card.laptop", "analog-output-speaker"));
    QFile corrupt(path);
    assert(corrupt.open(QIODevice::WriteOnly)); corrupt.write("invalid JSON"); corrupt.close();
    DevicePolicy broken(path);
    assert(!broken.enabled("bluez_card.headset", "*"));
    assert(!broken.setEnabled("bluez_card.headset", "*", "Headset", true));
    assert(corrupt.open(QIODevice::ReadOnly)); assert(corrupt.readAll() == "invalid JSON");
    DevicePolicy unwritable(directory.filePath("device_rules.json/child"));
    assert(!unwritable.setEnabled("test", "*", "Test", true));
    assert(!unwritable.enabled("test", "*"));
}

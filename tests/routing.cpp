// Exercise the real routing controller against a deterministic PipeWire boundary.
#include "FilterContainer.h"
#include "config/AppConfig.h"
#include <QCoreApplication>
#include <QTemporaryDir>
#include <QElapsedTimer>
#include <QThread>
#include <cassert>

void Log::debug(const QString&, util::source_location) {}
void Log::error(const QString&, util::source_location) {}
PwPipelineManager::PwPipelineManager(bool) {}
PwPipelineManager::~PwPipelineManager() {}
void PwPipelineManager::lock() const {}
void PwPipelineManager::unlock() const {}
PwPipelineManager::StreamTarget PwPipelineManager::stream_target(uint32_t id) const {
    auto it = stream_targets.find(id);
    return it == stream_targets.end() ? StreamTarget{} : it->second;
}
void PwPipelineManager::restore_stream_target(uint32_t id, const StreamTarget& target) const {
    const_cast<PwPipelineManager*>(this)->stream_targets[id] = target;
}
void PwPipelineManager::connect_stream_output(const uint32_t& id) const {
    restore_stream_target(id, {{std::make_pair("Spa:Id", std::to_string(ee_sink_node.id))},
                              {std::make_pair("Spa:Id", std::to_string(ee_sink_node.serial))}});
}
uint32_t PwPipelineManager::count_node_ports(const uint32_t&) { return 2; }
std::vector<pw_proxy*> PwPipelineManager::link_nodes(const uint32_t&, const uint32_t&, const bool&, const bool&) {
    return {reinterpret_cast<pw_proxy*>(1), reinterpret_cast<pw_proxy*>(2)};
}
void PwPipelineManager::destroy_links(const std::vector<pw_proxy*>&) const {}
PwPluginBase::PwPluginBase(std::string tag, std::string value, PwPipelineManager* manager, const bool& probe)
    : log_tag(std::move(tag)), name(std::move(value)), enable_probe(probe), pm(manager) {}
PwPluginBase::~PwPluginBase() {}
bool PwPluginBase::connect_to_pw() { connected_to_pw = true; return true; }
void PwPluginBase::disconnect_from_pw() { connected_to_pw = false; }
uint32_t PwPluginBase::get_node_id() const { return 800; }
void PwPluginBase::setup() {}
void PwPluginBase::process(float*, float*, float*, float*, size_t) {}
void PwPluginBase::process(float*, float*, float*, float*, float*, float*, size_t) {}

static void settle() {
    QElapsedTimer time; time.start();
    while (time.elapsed() < 70) { QCoreApplication::processEvents(); QThread::msleep(2); }
}
static NodeInfo node(uint32_t id, uint64_t serial, std::string name, std::string type) {
    NodeInfo result;
    result.id = id; result.serial = serial; result.name = name; result.media_class = type;
    result.n_output_ports = 2;
    return result;
}
static PwPipelineManager::StreamTarget explicitTarget(uint64_t serial) {
    PwPipelineManager::StreamTarget target;
    target.object = std::make_pair("Spa:Id", std::to_string(serial));
    return target;
}
int main(int argc, char** argv) {
    QTemporaryDir directory;
    qputenv("XDG_CONFIG_HOME", directory.path().toUtf8());
    QCoreApplication app(argc, argv);
    auto& config = AppConfig::instance();
    PwPipelineManager manager(false);
    manager.ee_sink_node = node(99, 199, "jamesdsp_sink", "Audio/Sink");
    manager.node_map[110] = node(10, 110, "laptop", "Audio/Sink");
    manager.node_map[120] = node(20, 120, "JBL", "Audio/Sink");
    manager.node_map[130] = node(30, 130, "Brave", "Stream/Output/Audio");
    manager.default_output_device_name = "laptop";
    PwPluginBase plugin("test", "test", &manager);
    {
        FilterContainer router(&manager, &plugin, &config);
        assert(router.policy.setEnabled("sink:laptop", "*", "Laptop", true));
        router.refresh(); settle();
        assert(manager.stream_target(30).object->second == "199");
        // A user move through Plasma wins, even though the previous route used DSP.
        manager.stream_targets[30] = explicitTarget(120);
        manager.stream_target_changed(30); settle();
        assert(manager.stream_target(30) == explicitTarget(120));
        // Modern and legacy managers can update just one of the two keys.
        manager.stream_targets[30] = {};
        router.refresh(); settle();
        manager.stream_targets[30].object = explicitTarget(120).object;
        manager.stream_target_changed(30); settle();
        assert(manager.stream_target(30) == explicitTarget(120));
        manager.stream_targets[30] = {};
        router.refresh(); settle();
        manager.stream_targets[30].node = std::make_pair("Spa:Id", "20");
        manager.stream_target_changed(30); settle();
        assert(!manager.stream_target(30).object);
        assert(manager.stream_target(30).node->second == "20");
        // A following-default stream returns to native routing when the default is excluded.
        manager.stream_targets[30] = {};
        manager.stream_target_changed(30); settle();
        assert(manager.stream_target(30).object->second == "199");
        manager.default_output_device_name = "JBL";
        manager.new_default_sink_name("JBL"); settle();
        assert(manager.stream_target(30) == PwPipelineManager::StreamTarget{});
        assert(!plugin.connected_to_pw);
        // An explicit native destination survives a default-device change exactly.
        manager.default_output_device_name = "laptop";
        manager.stream_targets[30] = explicitTarget(110);
        router.refresh(); settle();
        assert(manager.stream_target(30).object->second == "199");
        manager.default_output_device_name = "JBL";
        router.refresh(); settle();
        assert(manager.stream_target(30) == explicitTarget(110));
        // Runtime app exclusions restore the application's prior route.
        manager.default_output_device_name = "laptop";
        router.refresh(); settle();
        assert(manager.stream_target(30).object->second == "199");
        config.set(AppConfig::AudioAppBlocklist, QStringList{"Brave"}); settle();
        assert(manager.stream_target(30) == explicitTarget(110));
        config.set(AppConfig::AudioAppBlocklist, QStringList{}); settle();
        assert(manager.stream_target(30).object->second == "199");
        // Node destruction and ID reuse cannot inherit another stream's saved route.
        manager.node_map.erase(130); manager.stream_targets.erase(30);
        manager.stream_output_removed(130);
        manager.node_map[131] = node(30, 131, "Player", "Stream/Output/Audio");
        router.refresh(); settle();
        assert(manager.stream_target(30).object->second == "199");
    }
    assert(manager.stream_target(30) == PwPipelineManager::StreamTarget{});
}

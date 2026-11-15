from kid.hardware import HardwareInfo, model_warning


def test_hardware_warning_boundary():
    info = HardwareInfo("Linux", "Intel", 4, 7.6, 1.0, "Intel UHD", 500.0)
    assert info.logical_cpus == 4
    assert model_warning("llama3.2:3b", info.available_ram_gib, 3.0)

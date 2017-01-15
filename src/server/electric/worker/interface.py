from icharger.comms_layer import ChargerCommsManager

__global_charger = None


def get_charger():
    global __global_charger
    if __global_charger is None:
        __global_charger = ChargerCommsManager()
    return __global_charger


def get_device_info():
    return get_charger().get_device_info()


def get_channel_status(channel, device_id=None):
    return get_charger().get_channel_status(channel, device_id)


def get_control_register():
    return get_charger().get_control_register()


def get_system_storage():
    return get_charger().get_system_storage()


def get_preset_list(count_only):
    return get_charger().get_preset_list(count_only)


def get_preset(index):
    return get_charger().get_preset(index)
// This code was autogenerated with `dbus-codegen-rust -c blocking -s -g -m None -d org.bluez -i org.bluez.Device1 -p /org/bluez/hci0/dev_04_5D_4B_72_C9_CE -o bluez.rs`, see https://github.com/diwic/dbus-rs
use dbus as dbus;
use dbus::arg;
use dbus::blocking;

pub trait OrgFreedesktopDBusIntrospectable {
    fn introspect(&self) -> Result<String, dbus::Error>;
}

impl<'a, C: ::std::ops::Deref<Target=blocking::Connection>> OrgFreedesktopDBusIntrospectable for blocking::Proxy<'a, C> {

    fn introspect(&self) -> Result<String, dbus::Error> {
        self.method_call("org.freedesktop.DBus.Introspectable", "Introspect", ())
            .and_then(|r: (String, )| Ok(r.0, ))
    }
}

pub trait OrgBluezDevice1 {
    fn disconnect(&self) -> Result<(), dbus::Error>;
    fn connect(&self) -> Result<(), dbus::Error>;
    fn connect_profile(&self, uuid: &str) -> Result<(), dbus::Error>;
    fn disconnect_profile(&self, uuid: &str) -> Result<(), dbus::Error>;
    fn pair(&self) -> Result<(), dbus::Error>;
    fn cancel_pairing(&self) -> Result<(), dbus::Error>;
    fn address(&self) -> Result<String, dbus::Error>;
    fn address_type(&self) -> Result<String, dbus::Error>;
    fn name(&self) -> Result<String, dbus::Error>;
    fn alias(&self) -> Result<String, dbus::Error>;
    fn set_alias(&self, value: String) -> Result<(), dbus::Error>;
    fn class(&self) -> Result<u32, dbus::Error>;
    fn appearance(&self) -> Result<u16, dbus::Error>;
    fn icon(&self) -> Result<String, dbus::Error>;
    fn paired(&self) -> Result<bool, dbus::Error>;
    fn trusted(&self) -> Result<bool, dbus::Error>;
    fn set_trusted(&self, value: bool) -> Result<(), dbus::Error>;
    fn blocked(&self) -> Result<bool, dbus::Error>;
    fn set_blocked(&self, value: bool) -> Result<(), dbus::Error>;
    fn legacy_pairing(&self) -> Result<bool, dbus::Error>;
    fn rssi(&self) -> Result<i16, dbus::Error>;
    fn connected(&self) -> Result<bool, dbus::Error>;
    fn uuids(&self) -> Result<Vec<String>, dbus::Error>;
    fn modalias(&self) -> Result<String, dbus::Error>;
    fn adapter(&self) -> Result<dbus::Path<'static>, dbus::Error>;
    fn manufacturer_data(&self) -> Result<::std::collections::HashMap<u16, arg::Variant<Box<dyn arg::RefArg + 'static>>>, dbus::Error>;
    fn service_data(&self) -> Result<::std::collections::HashMap<String, arg::Variant<Box<dyn arg::RefArg + 'static>>>, dbus::Error>;
    fn tx_power(&self) -> Result<i16, dbus::Error>;
    fn services_resolved(&self) -> Result<bool, dbus::Error>;
}

impl<'a, C: ::std::ops::Deref<Target=blocking::Connection>> OrgBluezDevice1 for blocking::Proxy<'a, C> {

    fn disconnect(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.Device1", "Disconnect", ())
    }

    fn connect(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.Device1", "Connect", ())
    }

    fn connect_profile(&self, uuid: &str) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.Device1", "ConnectProfile", (uuid, ))
    }

    fn disconnect_profile(&self, uuid: &str) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.Device1", "DisconnectProfile", (uuid, ))
    }

    fn pair(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.Device1", "Pair", ())
    }

    fn cancel_pairing(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.Device1", "CancelPairing", ())
    }

    fn address(&self) -> Result<String, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Address")
    }

    fn address_type(&self) -> Result<String, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "AddressType")
    }

    fn name(&self) -> Result<String, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Name")
    }

    fn alias(&self) -> Result<String, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Alias")
    }

    fn class(&self) -> Result<u32, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Class")
    }

    fn appearance(&self) -> Result<u16, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Appearance")
    }

    fn icon(&self) -> Result<String, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Icon")
    }

    fn paired(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Paired")
    }

    fn trusted(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Trusted")
    }

    fn blocked(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Blocked")
    }

    fn legacy_pairing(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "LegacyPairing")
    }

    fn rssi(&self) -> Result<i16, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "RSSI")
    }

    fn connected(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Connected")
    }

    fn uuids(&self) -> Result<Vec<String>, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "UUIDs")
    }

    fn modalias(&self) -> Result<String, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Modalias")
    }

    fn adapter(&self) -> Result<dbus::Path<'static>, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "Adapter")
    }

    fn manufacturer_data(&self) -> Result<::std::collections::HashMap<u16, arg::Variant<Box<dyn arg::RefArg + 'static>>>, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "ManufacturerData")
    }

    fn service_data(&self) -> Result<::std::collections::HashMap<String, arg::Variant<Box<dyn arg::RefArg + 'static>>>, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "ServiceData")
    }

    fn tx_power(&self) -> Result<i16, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "TxPower")
    }

    fn services_resolved(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.Device1", "ServicesResolved")
    }

    fn set_alias(&self, value: String) -> Result<(), dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::set(&self, "org.bluez.Device1", "Alias", value)
    }

    fn set_trusted(&self, value: bool) -> Result<(), dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::set(&self, "org.bluez.Device1", "Trusted", value)
    }

    fn set_blocked(&self, value: bool) -> Result<(), dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::set(&self, "org.bluez.Device1", "Blocked", value)
    }
}

pub trait OrgFreedesktopDBusProperties {
    fn get<R0: for<'b> arg::Get<'b> + 'static>(&self, interface: &str, name: &str) -> Result<R0, dbus::Error>;
    fn set<I2: arg::Arg + arg::Append>(&self, interface: &str, name: &str, value: I2) -> Result<(), dbus::Error>;
    fn get_all(&self, interface: &str) -> Result<::std::collections::HashMap<String, arg::Variant<Box<dyn arg::RefArg + 'static>>>, dbus::Error>;
}

impl<'a, C: ::std::ops::Deref<Target=blocking::Connection>> OrgFreedesktopDBusProperties for blocking::Proxy<'a, C> {

    fn get<R0: for<'b> arg::Get<'b> + 'static>(&self, interface: &str, name: &str) -> Result<R0, dbus::Error> {
        self.method_call("org.freedesktop.DBus.Properties", "Get", (interface, name, ))
            .and_then(|r: (arg::Variant<R0>, )| Ok((r.0).0, ))
    }

    fn set<I2: arg::Arg + arg::Append>(&self, interface: &str, name: &str, value: I2) -> Result<(), dbus::Error> {
        self.method_call("org.freedesktop.DBus.Properties", "Set", (interface, name, arg::Variant(value), ))
    }

    fn get_all(&self, interface: &str) -> Result<::std::collections::HashMap<String, arg::Variant<Box<dyn arg::RefArg + 'static>>>, dbus::Error> {
        self.method_call("org.freedesktop.DBus.Properties", "GetAll", (interface, ))
            .and_then(|r: (::std::collections::HashMap<String, arg::Variant<Box<dyn arg::RefArg + 'static>>>, )| Ok(r.0, ))
    }
}

#[derive(Debug)]
pub struct OrgFreedesktopDBusPropertiesPropertiesChanged {
    pub interface: String,
    pub changed_properties: ::std::collections::HashMap<String, arg::Variant<Box<dyn arg::RefArg + 'static>>>,
    pub invalidated_properties: Vec<String>,
}

impl arg::AppendAll for OrgFreedesktopDBusPropertiesPropertiesChanged {
    fn append(&self, i: &mut arg::IterAppend) {
        arg::RefArg::append(&self.interface, i);
        arg::RefArg::append(&self.changed_properties, i);
        arg::RefArg::append(&self.invalidated_properties, i);
    }
}

impl arg::ReadAll for OrgFreedesktopDBusPropertiesPropertiesChanged {
    fn read(i: &mut arg::Iter) -> Result<Self, arg::TypeMismatchError> {
        Ok(OrgFreedesktopDBusPropertiesPropertiesChanged {
            interface: i.read()?,
            changed_properties: i.read()?,
            invalidated_properties: i.read()?,
        })
    }
}

impl dbus::message::SignalArgs for OrgFreedesktopDBusPropertiesPropertiesChanged {
    const NAME: &'static str = "PropertiesChanged";
    const INTERFACE: &'static str = "org.freedesktop.DBus.Properties";
}

pub trait OrgBluezMediaControl1 {
    fn play(&self) -> Result<(), dbus::Error>;
    fn pause(&self) -> Result<(), dbus::Error>;
    fn stop(&self) -> Result<(), dbus::Error>;
    fn next(&self) -> Result<(), dbus::Error>;
    fn previous(&self) -> Result<(), dbus::Error>;
    fn volume_up(&self) -> Result<(), dbus::Error>;
    fn volume_down(&self) -> Result<(), dbus::Error>;
    fn fast_forward(&self) -> Result<(), dbus::Error>;
    fn rewind(&self) -> Result<(), dbus::Error>;
    fn connected(&self) -> Result<bool, dbus::Error>;
    fn player(&self) -> Result<dbus::Path<'static>, dbus::Error>;
}

impl<'a, C: ::std::ops::Deref<Target=blocking::Connection>> OrgBluezMediaControl1 for blocking::Proxy<'a, C> {

    fn play(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "Play", ())
    }

    fn pause(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "Pause", ())
    }

    fn stop(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "Stop", ())
    }

    fn next(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "Next", ())
    }

    fn previous(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "Previous", ())
    }

    fn volume_up(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "VolumeUp", ())
    }

    fn volume_down(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "VolumeDown", ())
    }

    fn fast_forward(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "FastForward", ())
    }

    fn rewind(&self) -> Result<(), dbus::Error> {
        self.method_call("org.bluez.MediaControl1", "Rewind", ())
    }

    fn connected(&self) -> Result<bool, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.MediaControl1", "Connected")
    }

    fn player(&self) -> Result<dbus::Path<'static>, dbus::Error> {
        <Self as blocking::stdintf::org_freedesktop_dbus::Properties>::get(&self, "org.bluez.MediaControl1", "Player")
    }
}

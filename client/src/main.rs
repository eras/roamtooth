extern crate dbus;
extern crate sse_client;
extern crate serde_json;

mod bluezdeviceapi;

use dbus::blocking::Connection;
use std::time::Duration;
use sse_client::EventSource;
use std::thread;
//use serde_json::{Result, Value};

fn connect() -> Result<(), Box<dyn std::error::Error>> {
    println!("connecting");
    // First open up a connection to the session bus.
    let conn = Connection::new_system()?;

    // Second, create a wrapper struct around the connection that makes it easy
    // to send method calls to a specific destination and path.
    //let proxy = conn.with_proxy("org.bluez.Device1", "/org/bluez/hci0/dev_04_5D_4B_72_C9_CE", Duration::from_millis(5000));
    // let proxy = conn.with_proxy("org.bluez", "/", Duration::from_millis(5000));
    let proxy = conn.with_proxy("org.bluez", "/org/bluez/hci0/dev_04_5D_4B_72_C9_CE", Duration::from_millis(5000));

    use crate::bluezdeviceapi::OrgBluezDevice1;

    let name = proxy.name()?;
    println!("device name: {}", name);

    proxy.connect()?;

    return Ok(());
}

fn disconnect() -> Result<(), Box<dyn std::error::Error>> {
    println!("disconnecting");
    // First open up a connection to the session bus.
    let conn = Connection::new_system()?;

    // Second, create a wrapper struct around the connection that makes it easy
    // to send method calls to a specific destination and path.
    //let proxy = conn.with_proxy("org.bluez.Device1", "/org/bluez/hci0/dev_04_5D_4B_72_C9_CE", Duration::from_millis(5000));
    // let proxy = conn.with_proxy("org.bluez", "/", Duration::from_millis(5000));
    let proxy = conn.with_proxy("org.bluez", "/org/bluez/hci0/dev_04_5D_4B_72_C9_CE", Duration::from_millis(5000));

    use crate::bluezdeviceapi::OrgBluezDevice1;

    let name = proxy.name()?;
    println!("device name: {}", name);

    proxy.disconnect()?;

    return Ok(());
}

fn main() -> Result<(), Box<dyn std::error::Error>> {

    let _ignored = connect();
    
    let event_source = EventSource::new("http://aiee.mf:5000/stream").unwrap();

    event_source.on_message(|message| {
        //println!("New message event {:?}", message);
        let data : serde_json::Value = serde_json::from_str(&message.data).unwrap();
	//println!("got data: {:?}", data);
	if let Some(sync) = data.get("sync") {
	    let _result = 
		match sync {
		    serde_json::Value::String(str) if str == "device_connect" => {
			connect()
		    }
		    serde_json::Value::String(str) if str == "device_disconnect" => {
			disconnect()
		    }
		    other => {
			println!("unknown sync command {:?}", other);
			Ok(())
		    }
		};
	} else if let Some(_async) = data.get("async") {
	    // match sync {
	    // 	serde_json::Value::String(str) if str == "device_connect" => {
	    // 	    connect().unwrap()
	    // 	}
	    // 	serde_json::Value::String(str) if str == "device_disconnect" => {
	    // 	    disconnect().unwrap()
	    // 	}
	    // 	other => {
	    // 	    println!("unknown sync command {:?}", other)
	    // 	}
	    // }
	} else {
	    println!("unknown message {:?}", data)
	}
	
	// match serde_json::from_str(&message.data) {
	//     Ok(serde_json::Value(data)) => {
	// 	println!("got data: {:?}", data);
	//     }
	//     Err(_) => {
	// 	println!("ignoring");
	//     }
	// }
    });

    event_source.add_event_listener("error", |error| {
        println!("Error {:?}", error);
    });

    loop {
	thread::sleep(Duration::from_millis(5000));
    }
    // event_source.close();

    // println!("carry on");
    
    // // Now make the method call. The ListNames method call takes zero input parameters and
    // // one output parameter which is an array of strings.
    // // Therefore the input is a zero tuple "()", and the output is a single tuple "(names,)".
    // let (names,): (Vec<String>,) = proxy.method_call("org.bluez.Device1", "ListNames", ())?;

    // // Let's print all the names to stdout.
    // for name in names {
    //     println!("{}", name);
    // }

    //Ok(())
}

Dendrite Evented Interconnect
=============================

As stated above, the Dendrite project is a simple Python service to add evented support over an existing HTTP/REST API. Though this project is open-source, it was originally developed for the [Globus Online](http://www.globusonline.org) transfer monitoring iOS application ("iGlobus," a closed-source project).

Installation/Configuration
--------------------------

There are several steps required before getting a fully up-and-running Dendrite application server:

* **Generate private and public key files.**
	
	If you don't already have an officially-signed certificate and private key, you will want to generate one with [OpenSSL](http://www.openssl.org/). If you can execute `openssl version` at a termial, then you're fine.
	
	To generate one, type at the terminal:
	
		% openssl req -new -x509 -nodes -out config/keys/server.crt -keyout config/keys/server.key
		Generating a 1024 bit RSA private key
		.............................................++++++
		...............++++++
		writing new private key to 'config/keys/server.key'
		-----
		You are about to be asked to enter information that will be incorporated
		into your certificate request.
		What you are about to enter is what is called a Distinguished Name or a DN.
		There are quite a few fields but you can leave some blank
		For some fields there will be a default value,
		If you enter '.', the field will be left blank.
		-----
		Country Name (2 letter code) [AU]:US
		State or Province Name (full name) [Some-State]:Illinois
		Locality Name (eg, city) []:Chicago
		Organization Name (eg, company) [Internet Widgits Pty Ltd]:Globus Online
		Organizational Unit Name (eg, section) []:Dendrite/Mobile Applications Division
		Common Name (eg, YOUR name) []:dendrite.apis.globusonline.org
		Email Address []:your@email.address    
		% 
	
	You should put the server hostname in the "Common name" field, otherwise some clients will fail the name verification step. For now, it is simply the hostname of the server to be HTTP compatible.
	
	Note: it is highly advisable __not to put a passphrase on the on the PEM-encoded private key__, as you will be prompted at every startup for the passphrase to the key. It is a [known bug][so1] in Python < 3.2 that this prompt will occur for every socket connection in some cases, not just at initiation, making this feature basically useless.

[so1]: http://stackoverflow.com/questions/3140011/keep-ssl-keyfile-open-in-python

	Right now, Dendrite only supports Apache-style PEM-encoded `.key` and `.crt` files. In the future, we hope to support PKCS#12 (`.p12`).

* **Copy `config/dendrite.default.yaml` to `config/dendrite.yaml` and adjust
  the configuration there.**
	
	Most of the configuration options in `config/dendrite.yaml` are pretty self-explanatory, but the most important options are detailed below.
	
	* `listen_url`: The URL to listen on. This only supports TCP streams (`tcp://host:port`), TLS over TCP (`ssl://host:port`) and UNIX domain sockets (`unix://relative/path/to/socket`, see note below). Dendrite, by default, runs on `ssl://*:1336`, and it's generally best to keep it at that. If you wish to run on a port under 1024, then you'll have to launch the server with root privileges (see note below).
		
		Examples:
		
		```
		tcp://hostname:80 => LISTEN PORT 80
		tcp://hostname => LISTEN PORT 1337
		ssl://hostname:1337 => LISTEN TCP WITH SSL PORT 1337
		unix://tmp/connect.sock => CONNECTS TO ./tmp/connect.sock
		unix:///tmp/connect.sock => CONNECTS TO /tmp/connect.sock
		```
		
		At the time of this writing, the hostname parameter for TCP and SSL is ignored: the server binds on all interfaces. If no URL is specified, then this instance does nothing, though in the future it will act as a helper for the front-facing instance.
  
	* `certificate_file` and `private_key_file`: the PEM-encoded certificate and private key used for encryption. As a guideline, the certificate and private-key are correctly-formed if the first line of each is `-----BEGIN CERTIFICATE-----` and `-----BEGIN RSA PRIVATE KEY-----`, respectively.
	
	* Anything else in the `config/dendrite.yaml` is largely just for performance tweaking, and should not significantly affect operation.
	
	Unix domain sockets note: If the URL is specified with three slashes (`unix:///path/to/file.sock`), then the socket is absolute. Two slashes (`unix://path/to/file.sock`) denote a relative path.  

* **Start Dendrite!**
	
	To start the server, simply run `python script/launch`. The server will only write to a log if it knows that the output is not a terminal, so if you want background support you may want to close stdout and stderr before demonizing it: `nohup python script/launch >/dev/null 2>/dev/null &`.
	
	The server can be halted cleanly with a `SIGINT` (Ctrl-C), or uncleanly with a `SIGKILL`. The output, goofy-ASCII art and all, should look like this:
	
		% python script/launch
		08-30 12:52:50 CDT       INFO | +------------------------+
		08-30 12:52:50 CDT       INFO | |                 ____@  |
		08-30 12:52:50 CDT       INFO | |  ()()-----\____/       |
		08-30 12:52:50 CDT       INFO | | ()()    |      \_____@ |
		08-30 12:52:50 CDT       INFO | |         \___/--\       |
		08-30 12:52:50 CDT       INFO | |                 \--@   |
		08-30 12:52:50 CDT       INFO | +------------------------+
		08-30 12:52:50 CDT       INFO | |  Dendrite Initialized  |
		08-30 12:52:50 CDT       INFO | +------------------------+
		08-30 12:52:50 CDT       INFO | Opening front-facing Dendrite instance on ssl://0.0.0.0:1337...
		08-30 12:52:50 CDT       INFO | Dendrite started.
		... long pause, followed by Ctrl-C ...
		08-30 12:52:55 CDT       INFO | Received SIGINT-
		08-30 12:52:55 CDT       INFO | Dendrite terminating...
		08-30 12:52:55 CDT       INFO | Dendrite terminated.
		% 

Running as Root
---------------

Running Dendrite as root is not recommended, since the server has really no need for the elevated privileges. You can do so, however, if you need it to run below 1024, for example, though this usage is untested.

To run as root, you need to enable and set the `user` and `group` options. If it is an integer, then it is treated as a UID or GID as appropriate, otherwise, the user is looked up from the [`pwd`][pwd-module] and [`grp`][grp-module] modules. As soon as the root port has bound, then the server drops into the less-privileged mode. 

Dendrite will also soon chroot into it's own little jail when running as root, so that an attacker will spend a bit longer trying to find privilege-escalation attacks go get root access.

[pwd-module]: http://docs.python.org/library/pwd.html
[grp-module]: http://docs.python.org/library/grp.html
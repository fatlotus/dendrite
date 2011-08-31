General Dendrite Architecture
=============================

There are several large modules within Dendrite, each of which follows a general pattern. There are basically three types of modules:

* **Components** Components represent the high-level behaviors in a server. As a general rule, the containers are intra-referential (see [`src/dendrite/__init__.py`][init0] for how this magic occurs). They are generally inter-dependent on the other components in the system. In the MVC triangle, then the Components are the closer to the Controller than the Model or View.
	
[init0]: https://github.com/globusonline/dendrite/blob/development/src/dendrite/__init__.py
	
	A few examples of controllers:
	
	* `dendrite.backends` This component provides an interface to whatever REST backend we are calling. This provides a basic interface in the form of a class `dendrite.backends.backend_name.Backend` that has the following interface:
		
		* `#authenticate(username, password)` -> (deferred) authentication session. The t-.i-.p-.Defer instance returned should either return a dict that contains implementation-specific login state or a failure message.
		
		* `#resource(auth_session, method, url, query_string, body)` -> a `Resource` object, as documented below. Resources should only be used for a single request __or__ a single listen. Invoking both or calling another on a cancelled Resource is undefined behavior.
			
			* `#fetch(success, failure)` fetches this resource once and calls `success(data)` on successful completion, and `failure(err, message)` if the request fails.
			
			* `#success(update, failue)` begins listening to this resource and calls `update(type, data)` whenever the resource has changed (using the inteligent differencing helper, see below). If the listening fails, then `failure(err, data)` is called, though this does not necessarily `#cancel()` this request.
			
			* `#cancel()` cancels any listening that may be occuring on this Resource. No further updates should be sent once a request has been cancelled.
	
	* `dendrite.container` provides a component to handle the organization and structure of long-running stateful `Service`'s across a Dendrite cluster. This is useful largely to pool expensive resources such as APNS sockets and other multiplexed streams. Right now, only a local in-memory `Container` is implemented, and it is according to the interface below:
		
		* `#service(service_class)` -> instance of `service_class` This method retrieves an instance of `service_class` from the container. If it hasn't already been instantiated, then this service instantiates it.
	
* **Helpers** are stateless, self-contained, "mini-modules" that simply provide other functionality to the main containers. Testing them is a bit more tricky, since they are typically treated as singletons, though with a bit of `sys.modules` twiddling integration testing becomes a breeze.

* **Tests** are of the standard unit-, integration- and fuzz- test varieties seen in many software products. A quick way to test if your build is clean:
	
		% nosetests --with-coverage --cover-package=dendrite --with-doctest
		..............
		Name                                  Stmts   Miss  Cover   Missing
		-------------------------------------------------------------------
		dendrite                                 19      0   100%   
		dendrite.backends                         0      0   100%   
		dendrite.backends.http_helper            23      3    87%   45-48
		... output truncated out of shame ...
		dendrite.storage.memory                  29     18    38%   11-15...
		-------------------------------------------------------------------
		TOTAL                                   845    389    54%   
		-------------------------------------------------------------------
		Ran 14 tests in 4.572s
		OK
		% 
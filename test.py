import threading
import time

from mitmproxy import options
from mitmproxy.proxy import config, server
from mitmproxy.tools import cmdline

from mitmproxy.tools import dump
from selenium import webdriver


proxy_host = "127.0.0.1"
proxy_port = 8080

webpage = "https://www.google.com/"


def open_selenium(web_page):
    """open selenium and get the page"""

    firefox_profile = webdriver.FirefoxProfile()
    # Specify to use manual proxy configuration.
    firefox_profile.set_preference('network.proxy.type', 1)
    # Set the host/port.
    firefox_profile.set_preference('network.proxy.http', proxy_host)
    firefox_profile.set_preference('network.proxy.http_port', proxy_port)
    firefox_profile.set_preference('network.proxy.ssl', proxy_host)
    firefox_profile.set_preference('network.proxy.ssl_port', proxy_port)

    # Launch Firefox.
    driver = webdriver.Firefox(firefox_profile=firefox_profile)
    driver.get(web_page)

    # Wait 10 sec for the page to fully load
    time.sleep(10)
    driver.close()


def setup_proxy(webpage):
    # setup proxy server
    args = ["-w","C:\mozilla-source\dumpSelenium\%s.har" %webpage]

    parser = cmdline.mitmdump()
    args = parser.parse_args(args)
    if args.quiet:
        args.flow_detail = 0


    dump_options = options.Options()
    dump_options.load_paths(args.conf)
    dump_options.merge(cmdline.get_common_options(args))
    dump_options.merge(
        dict(
            flow_detail = args.flow_detail,
            keepserving = args.keepserving,
            filtstr = " ".join(args.filter) if args.filter else None,
        )
    )
    dump_options.listen_host = proxy_host
    dump_options.listen_port = proxy_port

    pconf = config.ProxyConfig(dump_options)
    proxy_server = server.ProxyServer(pconf)

    master = dump.DumpMaster(dump_options, proxy_server)
    return master


proxy_master = setup_proxy(webpage)

thread = threading.Thread(target=proxy_master.run, args=())
thread.start() # Start the proxy server

time.sleep(5)
open_selenium(webpage)
time.sleep(5)
proxy_master.shutdown()

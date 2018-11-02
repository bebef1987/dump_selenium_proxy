import threading
import time
from urllib.parse import urlparse

from mitmproxy import options
from mitmproxy.proxy import config, server
from mitmproxy.tools import cmdline

from mitmproxy.tools import dump
from selenium import webdriver


class SeleniumProxyHelper():

    proxy_host = "127.0.0.1"
    proxy_port = 8080
    driver = None
    proxy_master = None

    def firefox_proxy_profile(self):
        firefox_profile = webdriver.FirefoxProfile()
        # Specify to use manual proxy configuration.
        firefox_profile.set_preference('network.proxy.type', 1)
        # Set the host/port.
        firefox_profile.set_preference('network.proxy.http', self.proxy_host)
        firefox_profile.set_preference('network.proxy.http_port', self.proxy_port)
        firefox_profile.set_preference('network.proxy.ssl', self.proxy_host)
        firefox_profile.set_preference('network.proxy.ssl_port', self.proxy_port)
        return firefox_profile



    def open_selenium(self, web_page, close_driver = True):
        """open selenium and get the page"""

        # Launch Firefox.
        self.driver = webdriver.Firefox(firefox_profile= self.firefox_proxy_profile())

        self.driver.get(web_page)

        # Wait 10 sec for the page to fully load
        time.sleep(10)

        if close_driver:
            self.close_driver()

    def close_driver(self):
        self.driver.close()
        self.driver=None

    def setup_proxy(self, args):

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
        dump_options.listen_host = self.proxy_host
        dump_options.listen_port = self.proxy_port

        pconf = config.ProxyConfig(dump_options)
        proxy_server = server.ProxyServer(pconf)

        master = dump.DumpMaster(dump_options, proxy_server)

        self.proxy_master = master

    def stop_proxy(self):
        time.sleep(5)
        self.proxy_master.shutdown()
        self.proxy_master= None

    def generate_log_for_webpage(self, webpage, filename):

        # setup proxy server
        args = ["-w", filename]

        self.setup_proxy(args)

        thread = threading.Thread(target=self.proxy_master.run, args=())
        thread.start() # Start the proxy server

        time.sleep(5)
        self.open_selenium(webpage)
        time.sleep(5)
        self.stop_proxy()


    def playback_webpage(self, webpage, file):

        # setup proxy server
        args = ["-k", "-s", "alternateServer.py %s" % file]

        self.setup_proxy(args)

        thread = threading.Thread(target=self.proxy_master.run, args=())
        thread.start() # Start the proxy server

        time.sleep(5)
        self.open_selenium(webpage, close_driver= False)


webpages = [
    "https://en.wikipedia.org/wiki/Barack_Obama"
    # "https://ca.news.yahoo.com/adopted-great-dane-teaches-puppy-000002643.html",
    # "https://www.reddit.com/r/technology/comments/9sqwyh/we_posed_as_100_senators_to_run_ads_on_facebook/",
    # "https://www.twitch.tv/videos/326804629",
    # "https://yandex.ru/search/?text=barack%20obama&lr=10115",
    # "https://www.bing.com/search?q=barack+obama",
    # "https://www.microsoft.com/en-us/windows/get-windows-10",
    # "http://fandom.wikia.com/articles/fallout-76-will-live-and-die-on-the-creativity-of-its-playerbase",
    # "https://www.vice.com/en_us/article/j53a8d/four-college-freshmen-photograph-their-first-semester-v25n3",
    # "https://www.imdb.com/title/tt0084967/?ref_=nv_sr_2",
    # "https://imgur.com/gallery/m5tYJL6",
    # "https://www.apple.com/macbook-pro/"
]

helper = SeleniumProxyHelper()
print("STARTING MITMPROXY recording!!")

for webpage in webpages:
    print("generating file for: %s" %webpage)
    base_url = urlparse(webpage).hostname
    filename = "%s.mp" %base_url

    helper.generate_log_for_webpage(webpage, filename=filename)

print("STARTING MITMPROXY playback!!")

input("STOP internet connection and press Enter to continue...")
for webpage in webpages:
    print("Playback file for: %s" % webpage)
    base_url = urlparse(webpage).hostname
    helper.playback_webpage(webpage, file="%s.mp" %base_url)

    input("Save the webpage and press Enter to continue...")

    helper.close_driver()
    helper.stop_proxy()



import proxi.proxi_server as p

if __name__ == '__main__':
    proxy = p.ProxiServer('127.0.0.1', 8001)

    proxy.start_listen()

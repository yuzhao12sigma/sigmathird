# -*- coding: utf-8 -*-

from app import app
import config


def main():
    sigmathird_ip = config.fetch("sigmathird", "ip")
    sigmathird_port = config.fetch("sigmathird", "port")
    app.run(host=sigmathird_ip, port=sigmathird_port)


if __name__ == "__main__":
    main()

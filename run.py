# -*- coding: utf-8 -*-

from api.app import app


def main(*args):
    app.run(host="0.0.0.0", port=7073)


if __name__ == "__main__":
    main()

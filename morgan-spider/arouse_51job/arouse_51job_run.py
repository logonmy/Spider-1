#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25

import sys

import arouse_utils

sys.path.append("../common")
import server
import settings
import os
import signal


def main():
    server.main(settings.project_settings)


def test():
    pass


if __name__ == '__main__':
    print sys.argv
    if len(sys.argv) < 2:
        print 'the length of argv is too less'
        exit(0)
    if sys.argv[1] == 'start':
        print 'start!!!'
        pid = os.getpid()
        f = open('pid', 'w')
        f.write(str(pid))
        f.close()
        main()
    elif sys.argv[1] == 'stop':
        print 'stop!!!'
        f = open('pid', 'r')
        pid = f.readline().strip()
        f.close()
        os.kill(int(pid), signal.SIGTERM)
        print 'killing the pid of', pid
    else:
        print 'error argv'

        # main()
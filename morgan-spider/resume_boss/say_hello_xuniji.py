#!coding:utf8

from demo_utils import ADB
import time

def get_activity_name(adb):
    a=adb.shell_command('dumpsys activity activities')
    activity_name = ''
    for i in a.split('\n'):
        if 'mFocusedActivity' in i:
            activity_name = i.split()[-2]
            break
    return activity_name

def main(adb, username, passwd):

    h,v = adb.shell_command('wm size').strip().split()[-1].split('x')
    h = int(h)
    v = int(v)

    # delete cache
    adb.shell_touch('input tap %s %s' % (v*0.88, h*0.33), 1)
    #input username
    adb.shell_touch('input tap %s %s' % (v*0.39, h*0.33), 1)

    adb.shell_command('input text ' + username)
    #input passwd
    adb.shell_touch('input tap %s %s' % (v*0.39, h*0.41), 1)

    adb.shell_command('input text ' + passwd)
    #login
    adb.shell_touch('input tap %s %s' % (v*0.39, h*0.59), 1)
    time.sleep(10)

    
    adb.shell_touch('input tap %s %s' % (v*0.10, h*0.97), 1)
    time.sleep(5)
    say_hello_count = 50

    while say_hello_count:

        # shaixuan
        adb.shell_touch('input tap %s %s' % (v*0.49, h*0.19), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.49, h*0.97), 1)
        time.sleep(1)
        # return to list page
        adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)
        time.sleep(1)
        # swipe up one people
        adb.shell_touch('input swipe %s %s %s %s' % (287, 514, 288, 514-(h*0.15)) , 1)
        say_hello_count -= 1


    # logout
    adb.shell_touch('input tap %s %s' % (v*0.83, h*0.96), 1)
    time.sleep(1)
    adb.shell_touch('input tap %s %s' % (v*0.95, h*0.05), 1)
    time.sleep(1)
    adb.shell_touch('input tap %s %s' % (v*0.49, h*0.59), 1)
    time.sleep(1)
    adb.shell_touch('input tap %s %s' % (v*0.73, h*0.58), 1)



if __name__ == '__main__':
    adb = ADB()

    adb.wait_for_device()
    err, dev = adb.get_devices()

    if len(dev) == 0:
        logger.error('no avaliable device')
        exit()
    adb.set_target_device(dev[0])

    # logger.info('close app')
    print 'close app'
    adb.shell_command(('am force-stop com.hpbr.bosszhipin'))
    time.sleep(0.5)
    # 启动app
    # logger.info('start app')
    print 'start app'
    adb.shell_command('am start -n com.hpbr.bosszhipin/com.hpbr.bosszhipin.module.login.activity.LoginActivity')
    # adb.shell_command('am start -n com.hpbr.bosszhipin/com.hpbr.bosszhipin.module.login.activity.LoginActivity')
    time.sleep(5)
    main(adb, '15910286297', 'bossboss')

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
    #into message
    adb.shell_touch('input tap %s %s' % (v*0.49, h*0.95), 1)
    time.sleep(1)
    adb.shell_touch('input tap %s %s' % (v*0.49, h*0.95), 1)
    time.sleep(2)

    while True:

        # shaixuan
        adb.shell_touch('input tap %s %s' % (v*0.94, h*0.05), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.06, h*0.17), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.19, h*0.28), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.06, h*0.40), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.65, h*0.95), 1)
        time.sleep(5)
        #get list activity
        activity_name_1 = get_activity_name(adb)
        adb.shell_touch('input tap %s %s' % (v*0.65, h*0.18), 1)
        #get chat activity
        activity_name_2 = get_activity_name(adb)
        if activity_name_1 == activity_name_2:
            print 'no chat people, return'
            adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)
            break
        step = 0.025
        start = 0.93
        activity_name_3 = ''
        for x in xrange(30):
            adb.shell_touch('input tap %s %s' % (v*0.96, h*(start-x*step)), 1)
            adb.shell_touch('input tap %s %s' % (v*0.50, h*0.05), 1)
            time.sleep(1)
            activity_name_3 = get_activity_name(adb)
            if activity_name_3 != activity_name_2:
                print 'has contect with this people'
                adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)
                time.sleep(2)
                break
        else:
            time.sleep(2)
            adb.shell_touch('input tap %s %s' % (v*0.49, h*0.97), 1)
            time.sleep(2)
            adb.shell_command('input text ' + 'hello')
            time.sleep(2)
            adb.shell_touch('input tap %s %s' % (v*0.95, h*0.96), 1)
            time.sleep(7)
        # return to main activity
        adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)
        activity_name_4 = get_activity_name(adb)
        if activity_name_4 == activity_name_3:
            print 'get weixin or phone.'
            adb.shell_touch('input tap %s %s' % (v*0.48, h*0.60), 1)
            time.sleep(2)
            adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)
        time.sleep(1)
        adb.shell_touch('input tap %s %s' % (v*0.04, h*0.05), 1)

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

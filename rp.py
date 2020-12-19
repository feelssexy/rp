#!/bin/python3
import pypresence as rp
from time import sleep, time
from datetime import datetime as dt
from datetime import timedelta

import os
import subprocess
import re
# import sys

# https://stackoverflow.com/a/42404044
def cur_win():
    #TODO: should probably rewrite this with `xdotool`
    root = subprocess.Popen('xprop -root _NET_ACTIVE_WINDOW'.split(' '), stdout=subprocess.PIPE)
    stdout, stderr = root.communicate()
    match, match2 = None, None

    m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)
    if m != None:
        window_id = m.group(1)
        window = subprocess.Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=subprocess.PIPE)
        stdout, stderr = window.communicate()
        match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)

    if m != None:
        window_id = m.group(1)
        window = subprocess.Popen(['xprop', '-id', window_id, 'WM_CLASS'], stdout=subprocess.PIPE)
        stdout2, stderr2 = window.communicate()
        match2 = re.match(b'WM_CLASS\(\w+\) = "(?P<name>[^"]+)".*$', stdout2)


    r = ['error', 'error']
    if match != None:
        r[0] = match.group("name").strip(b'"').decode('UTF-8')
    if match2 != None:
        r[1] = match2.group('name').strip(b'"').decode('UTF-8')

    # exception: st
    if r[0] == r[1] == 'st':
        x = resolve_parent(window_id.decode('UTF-8'))
        if x:
            r[0] = '|'.join(x)
    return r

def justfkingrun(cmd):
    stdout, stderr = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return [i.decode('UTF-8').strip() for i in (stdout, stderr)]

def resolve_parent(wid, depth=2, forceDepth=False):
    #cmd = "ps o 'ucmd' $("
    #for i in range(depth):
    #    cmd += "pgrep -P $("
    #cmd += "xdotool getwindowpid {}"
    #for i in range(depth):
    #    cmd += ")"
    #cmd += ")"
    #print(cmd)
    #p = subprocess.Popen(cmd.format(wid).split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #stdout, stderr = p.communicate()

    pid, err = justfkingrun('xdotool getwindowpid {}'.format(wid))
    if err:
        print('ERR')
        print(stdout, stderr)
        return None
    pid = [pid]

    for i in range(depth):
        s = justfkingrun("pgrep -d, -P {}".format(','.join(pid)))[0].split(',')
        #print(f'{s=}')
        if s == [''] and not forceDepth:
            break
        pid = s
    #print(f'{pid=}')

    ######################################################################
    secure = False
    if secure:
        u = 'u'
    else:
        u = ''

    stdout, stderr = justfkingrun("ps o {}cmd {}".format(u, ' '.join(pid)))
    old = stdout

    filterForFanciness = (
            r'^/usr/bin/',
            r'^/bin/',
    )
    for f in filterForFanciness:
        stdout = re.sub(f.replace('/', r'\/'), '', stdout, flags=re.MULTILINE) # python being retarded
    if old != stdout:
        #print('got stripped: ' + old + '\n' + stdout)
        pass

    if stderr:
        print("ps o {}cmd {}".format(u, ' '.join(pid)))
        return None
    return stdout.splitlines()[1:]

def get_music_status():
    popMe = subprocess.Popen('mpc status'.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = [s.decode('UTF-8') for s in popMe.communicate()]
    if stderr:
        return None, None, None, stdout
    if stdout.count('\n') != 3:
        return False, None, None, stdout

    m_song, playlist_status, mode_status = stdout.splitlines()
    # playing status
    m = re.match(r'\[(?P<status>playing|paused)\]  ?(?P<plstatus>#\d+/\d+)   (?P<cmin>\d+):(?P<csec>\d+)/(?P<tmin>\d+):(?P<tsec>\d+) \(\d{1,3}%\)'.replace('/', r'\/'), playlist_status)
    if not m:
        print(playlist_status)
        return None, None, None, stdout

    #if re.search(r'^\[playing\]', playlist_status):
    if m['status'] == 'playing':
        m_playing = True
    #elif re.search(r'^\[paused\]', playlist_status):
    else:
        m_playing = False

    delta = timedelta(seconds=int(time())) + timedelta(minutes=int(m['tmin']), seconds=int(m['tsec'])) - timedelta(minutes=int(m['cmin']), seconds=int(m['csec']))

    #return m_playing, int(delta.total_seconds()), m_song, '\n'.join(stdout.splitlines()[1:])[len('[playing] '):].replace('  ', ' ')
    return m_playing, int(delta.total_seconds()), m_song, f"*Playlist: {m['plstatus']} *SongLength: {m['tmin']}:{m['tsec']}" if m else stdout# *Other options: {stdout.splitlines()[2]}" if m else stdout

def filter(p, s):
    n = s.lower().find(p)

    while n != -1:
        s = s[:n] + s[n+len(p):]
        n = s.lower().find(p)

    return s

def smarterFilter(p, s):
    return re.sub(r'(?<!\w)%s(?!\w)' % re.escape(p), '', s, flags=re.IGNORECASE)

class HotSexException(Exception): pass

def main():
    replaceThis = {
        'navigator': 'firefox',
        'gl': 'MPV'
    }
    # ok fuck this os.environ... what absolute bullshit is this piece of junk
    #filterThis = os.environ['filterThis'].split(';') # nah, you better not look at this

    # quick and dirty
    envPiss = {}
    with open('.env', 'r') as f:
        for line in f.readlines():
            k, v = line.split('=')
            filterThis = envPiss[k] = v
    filterThis = envPiss['filterThis'].split(';')

    ## filterThis += [
    ##     '#welcome',
    ##     '#rules-info',
    ##     '#trial',
    ##     '#trial-talk',
    ##     '#announcements',
    ##     '#vips-announce-shit',
    ##     '#starboard',
    ##     '#mod-logs',
    ##     '#general',
    ##     '#multilingual-chat',
    ##     '#games',
    ##     '#vip-club',
    ##     '#malware-talk',
    ##     '#programming',
    ##     '#no-skid-zone',
    ##     '#tech-support',
    ##     '#hardware',
    ##     '#music',
    ##     '#midis-modules',
    ##     '#art-drawings',
    ##     '#shotpist',
    ##     '#spombats',
    ##     '#talk-to-andrej',
    ##     '#nool',
    ##     '#skid-zone',
    ##     '#clown-zoo',
    ##     '#ÿ',
    ##     '#staff-general',
    ##     '#staff-bots',
    ##     '#logs',
    ##     '#joins-boosts',
    ##     '#linux-distros',
    ##     '#trial-archive',
    ##     '#nouff-archived',
    ##     '#staff-verification',

    ##     'leurak'
    ## ]

    CLIENT_ID = 591626849969504276
    RPC = rp.Presence(CLIENT_ID)
    RPC.connect()

    # it didnt error with `last_locked = None` not being present
    last_window = last_title = last_music = last_locked = [None]
    hot_sex = 0
    while 1:
        hot_sex += 1
        if hot_sex >= 100:
            #raise HotSexException()
            pass

        title, window = cur_win()

        title = smarterFilter(window, title)

        if window.lower() in replaceThis:
            window = replaceThis[window.lower()]

        for f in filterThis:
            window = filter(f, window)
            title = filter(f, title)

        locked = True if os.path.isfile('/tmp/.screenlock') else False
        music = get_music_status()

        checks = (
            title != last_title,
            window != last_window,
            locked != last_locked,
            music[0] != last_music[0], # ignore the number value
            music[2:] != last_music[2:]
        )

        if any(checks):
            #print(checks)
            t = int(time()) if window != last_window else None if locked else t
            m_playing, m_leftToPlay, m_song, m_stdout = music
            m_stdout = "*Note: Try listening using `d.fsm` on DustOut Bot " + m_stdout
            if len(m_stdout) >= 128:
                pass
                #print('len of `m_stdout`', len(m_stdout))
            m_stdout = m_stdout[:127]#.encode().decode('ASCII')
            print('updating rp to', window, title, locked, m_playing)
            RPC.update(
                    details=(window.capitalize() + ': ' + title)[:128],
                    state=m_song[:128] if m_playing else "App has not been changed for",
                    start=t,
                    end=m_leftToPlay if m_playing else None,
                    large_image='sticker_nu5_kzba',
                    small_image='locked' if locked else 'music_playing' if m_playing else None,
                    small_text='Workspace is currently locked' if locked else m_stdout if m_playing else None
                )
        last_window = window
        last_title = title
        last_locked = locked
        last_music = music

        sleep(4)

if __name__ == '__main__':
    while 1:
        try:
            main()
        except rp.ServerError:
            print('--- where are you discord?? server error')
        except rp.InvalidID:
            print('--- where are you discord?? invalid id')
        except ConnectionRefusedError:
            print('--- where are you discord?? ConnectionRefusedError')
        except HotSexException:
            # because pypresence or discord sometimes likes to passionately fuck me in the ass
            # so i just like to restart the whole script...
            # i think i actually commented this out recently
            print('--- regular restart by bash loop')
            break
        #except UnboundLocalError:
            #print('excuse me, what??')
        hot_sex = 0
        sleep(10)

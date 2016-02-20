# https://github.com/Jamesits/netease-music-status
# by James Swineson
# 2016-02-20

import json
import re
from os.path import expanduser

from Tail import Tail

reg_url = "[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
log_path = expanduser("~/Library/Containers/com.netease.163music/Data/Documents/storage/Logs/music.163.log")


class NeteaseMusicStatus:
    @staticmethod
    def _is_json(text):
        return text.strip().startswith("{")

    def __init__(self):
        self.monitor_path = log_path
        self.tail = Tail(self.monitor_path)
        self.tail.register_callback(self._tail_callback)

        self.playState = 0
        self.track = None
        self.currentSong = None
        self.last_update = None
        self.coverUri = None

    def _tail_callback(self, content):
        content = content.strip().strip('\n')
        result = re.split('\[(.*?)\]', content)
        callbacks = {
            5: self._common_log_callback,
            1: self._audiostreamer_log_callback,
        }
        callbacks.get(len(result), self._default_log_callback)(result)
        # print(len(result), result)

    def _common_log_callback(self, log):
        try:
            self.last_update = log[1]
            log_details = log[-1].split(', ', maxsplit=2)
            if log_details[0].startswith('_'):
                operation = log_details[0]
                initiator = log_details[1]
                content = log_details[2]
            elif log_details[1].startswith('_'):
                operation = log_details[1]
                initiator = log_details[0]
                content = log_details[2]
            else:
                operation = None
                initiator = None
                content = log_details[2]
            # print("{}\t\t{}\t\t{}".format(initiator, operation, content))
            # print("Log content: ", content)

            if initiator == None:
                if operation == None:
                    if NeteaseMusicStatus._is_json(content):
                        self._song_change_callback(content)
            elif initiator == "player/index.js":
                if operation == "__onJump2Track":
                    if NeteaseMusicStatus._is_json(content):
                        self._track_change_callback(content)
                if operation == "__onPlayStateChange":
                    if NeteaseMusicStatus._is_json(content):
                        self._play_state_change_callback(content)
            elif initiator == "/detail/brief/index.js":
                if operation == "__onCoverLoad":
                    if not NeteaseMusicStatus._is_json(content):
                        self._cover_change_callback(content)
        except IndexError:
            # print("Index error: {}".format(log))
            pass

    def _song_change_callback(self, content):
        self.currentSong = json.loads(content)
        # self._state_change_finished("song metadata loaded")

    def _play_state_change_callback(self, content):
        new_playstate = int(json.loads(content)['state'])
        # self._state_change(new_playstate)

    def _track_change_callback(self, content):
        self.track = json.loads(content)
        # self._state_change_finished("track change")

    def _cover_change_callback(self, content):
        try:
            self.coverUri = content.split(' -> ')[1]
        except IndexError:
            pass
            # self._state_change_finished("cover changed")

    def _audiostreamer_log_callback(self, content):
        content = content[0].lower()
        if content.find("play") != -1:
            self._state_change(1)
        elif content.find("pause") != -1:
            self._state_change(2)
            pass

    def _default_log_callback(self, content):
        pass

    def _state_change(self, new_playstate):
        if not new_playstate == self.playState:
            self.playState = new_playstate
            if self.playState == 1:
                self._state_change_finished("Play")
            elif self.playState == 2:
                self._state_change_finished("Pause")
            elif self.playState == -1:
                self._state_change_finished("Loading new song")
            elif self.playState == -2:
                self._state_change_finished("New song loaded")
            else:
                self._state_change_finished("play status change")

    def _state_change_finished(self, reason="Event triggered."):
        print(">>>>>>> ", reason)
        print("Last event time: ", self.last_update)
        print("Song: ")
        print(self.currentSong)
        print("Play state: ", self.playState)
        # print("Cover URI: ", self.coverUri)

    def start(self):
        self.tail.follow()


if __name__ == '__main__':
    n = NeteaseMusicStatus()
    n.start()

#!/bin/sh
E="env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"
sudo -u dandelion $E gsettings set org.gnome.settings-daemon.plugins.media-keys volume-up "['XF86AudioRaiseVolume']"
sudo -u dandelion $E gsettings set org.gnome.settings-daemon.plugins.media-keys volume-down "['XF86AudioLowerVolume']"
sudo -u dandelion $E gsettings set org.gnome.settings-daemon.plugins.media-keys volume-mute "['XF86AudioMute']"
sudo -u dandelion $E gsettings get org.gnome.settings-daemon.plugins.media-keys volume-up
sudo -u dandelion $E gsettings get org.gnome.settings-daemon.plugins.media-keys volume-down
sudo -u dandelion $E wpctl get-volume @DEFAULT_AUDIO_SINK@

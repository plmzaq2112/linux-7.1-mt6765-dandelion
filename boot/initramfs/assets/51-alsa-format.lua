rule = {
  matches = {
    { { "node.name", "matches", "alsa_output.*" }, },
  },
  apply_properties = {
    ["audio.format"] = "S16LE",
    ["audio.rate"] = 44100,
  },
}
table.insert(alsa_monitor.rules, rule)

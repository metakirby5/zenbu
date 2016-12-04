import struct
import codecs

# Hex to X

def nohash(hex):
  return hex.lstrip('#')

def to_rgb(hex):
  return struct.unpack('BBB', codecs.decode(nohash(hex), 'hex'))

def to_chrome(hex):
  return '[{}]'.format(', '.join(map(str, to_rgb(hex))))

# alpha: 0 - 255
def to_apple(hex, alpha=0):
  return '{{{}}}'.format(', '.join(map(
    lambda x: str(x * 257), to_rgb(hex) + (alpha,)
  )))

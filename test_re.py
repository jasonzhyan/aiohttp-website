import re
import logging;logging.basicConfig(level=logging.INFO)

_RE_PASSWD_SHA1=re.compile(r'^[0-9a-f]{40}$')
logging.info(_RE_PASSWD_SHA1.match('1111111111111111111111111111111111111111'))

s=r'[0-9]+'
print(re.match(s,'a'))

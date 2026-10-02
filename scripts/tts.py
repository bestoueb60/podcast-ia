import os, ssl, sys
import edge_tts.communicate as c
ca = '/root/.ccr/ca-bundle.crt'
if os.path.exists(ca):
    c._SSL_CTX = ssl.create_default_context(cafile=ca)
from edge_tts.util import main
sys.argv = ['edge-tts'] + sys.argv[1:]
main()

=====
Usage
=====

Simple example::

    import socket
    from bettersocket import BetterSocketIO
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('marcsello.com', 420))
    
    bs = BetterSocketIO(s)
    
    bs.sendframe("GET / HTTP/1.1")
    bs.sendframe("Host: marcsello.com")
    bs.sendframe("")
    
    while True:
        line = bs.readframe()
        print(line)